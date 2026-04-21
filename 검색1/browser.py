import time
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from concurrent.futures import ThreadPoolExecutor, as_completed


def search_web(query: str, max_results: int = 10) -> list[dict]:
    results = []

    with DDGS() as ddgs:
        items = ddgs.text(
            query,
            region="kr-kr",
            safesearch="off",
            max_results=max_results
        )

        for item in items:
            results.append({
                "title": (item.get("title") or "").strip(),
                "url": (item.get("href") or "").strip(),
                "snippet": (item.get("body") or "").strip(),
            })

    return results


def extract_naver_blog_text(url: str, headers: dict) -> str:
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()

    if not res.encoding or res.encoding.lower() == "iso-8859-1":
        res.encoding = res.apparent_encoding

    soup = BeautifulSoup(res.text, "html.parser")

    iframe = soup.find("iframe", id="mainFrame")
    if iframe and iframe.get("src"):
        iframe_url = "https://blog.naver.com" + iframe["src"]

        res2 = requests.get(iframe_url, headers=headers, timeout=10)
        res2.raise_for_status()

        if not res2.encoding or res2.encoding.lower() == "iso-8859-1":
            res2.encoding = res2.apparent_encoding

        soup2 = BeautifulSoup(res2.text, "html.parser")

        selectors = [
            ("div", {"class": "se-main-container"}),
            ("div", {"id": "postViewArea"}),
            ("div", {"class": "post-view"}),
        ]

        for tag, attrs in selectors:
            content = soup2.find(tag, attrs=attrs)
            if content:
                return content.get_text("\n", strip=True)

        return soup2.get_text("\n", strip=True)

    return soup.get_text("\n", strip=True)


def extract_general_text(url: str, headers: dict) -> str:
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()

    if not res.encoding or res.encoding.lower() == "iso-8859-1":
        res.encoding = res.apparent_encoding

    soup = BeautifulSoup(res.text, "html.parser")

    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    selectors = [
        ("div", {"class": "entry-content"}),
        ("div", {"class": "tt_article_useless_p_margin"}),
        ("article", {}),
        ("main", {}),
        ("div", {"id": "content"}),
    ]

    for tag, attrs in selectors:
        content = soup.find(tag, attrs=attrs)
        if content:
            text = content.get_text("\n", strip=True)
            if text:
                return text

    return soup.get_text("\n", strip=True)


def get_article_text(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/147.0.0.0 Safari/537.36"
        )
    }

    if "blog.naver.com" in url:
        return extract_naver_blog_text(url, headers)

    return extract_general_text(url, headers)


def fetch_content(item: dict):
    title = item["title"]
    url = item["url"]
    snippet = item["snippet"]

    try:
        content = get_article_text(url)
    except Exception as e:
        print(f"[본문 가져오기 실패] {url} / {e}")
        return None

    return {
        "title": title,
        "url": url,
        "snippet": snippet,
        "content": content,
    }


def crawl_genshin_best_party(
    name: str,
    max_workers: int = 5,
    max_docs: int = 10,
    request_delay: float = 1.0,
    min_content_length: int = 30,
) -> list[dict]:

    query_list = [
    f"{name} best team",
    f"{name} recommended team",
    f"{name} team build",
    f"{name} team composition",
    f"{name} comps"
]

    docs = []
    seen_urls = set()
    attempt = 0

    while len(docs) < max_docs:
        query = query_list[attempt % len(query_list)]
        attempt += 1

        print(f"[검색 시도 {attempt}] {query} / {len(docs)}/{max_docs}")

        try:
            search_results = search_web(query, max_results=max_docs * 5)
        except Exception as e:
            print(f"[검색 실패] {e}")
            time.sleep(request_delay)
            continue

        valid_items = []

        for item in search_results:
            url = item["url"]

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)
            valid_items.append(item)

        added_this_round = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(fetch_content, item) for item in valid_items]

            for future in as_completed(futures):
                if len(docs) >= max_docs:
                    break

                result = future.result()

                if result is None:
                    continue

                content = result["content"]

                if len(content.strip()) < min_content_length:
                    print(f"[본문 너무 짧음 패스] {result['title']}")
                    continue

                docs.append({
                    "index": len(docs) + 1,
                    "query": query,
                    **result
                })
                added_this_round += 1

        print(f"[추가됨] {added_this_round}개 / 총 {len(docs)}개")

        time.sleep(request_delay)

    return docs