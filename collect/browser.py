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
            max_results=max_results,
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


def should_skip_item(
    item: dict,
    ignore_keywords: list[str],
    block_sites: list[str],
) -> bool:
    title = (item.get("title") or "").lower()
    url = (item.get("url") or "").lower()
    snippet = (item.get("snippet") or "").lower()

    joined = f"{title} {url} {snippet}"

    for site in block_sites:
        if str(site).lower() in url:
            return True

    for keyword in ignore_keywords:
        if str(keyword).lower() in joined:
            return True

    return False


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


def build_query_list(
    name: str,
    search_keywords: list[str],
    search_suffixes: list[str],
) -> list[str]:
    queries = []

    if search_keywords and search_suffixes:
        for keyword in search_keywords:
            for suffix in search_suffixes:
                queries.append(f"{name} {keyword} {suffix}")

    elif search_keywords:
        for keyword in search_keywords:
            queries.append(f"{name} {keyword}")

    else:
        queries = [
            f"{name} best team",
            f"{name} recommended team",
            f"{name} team build",
            f"{name} team composition",
            f"{name} comps",
        ]

    return queries


def crawl_genshin_best_party(
    name: str,
    max_workers: int = 4,
    max_docs: int = 8,
    min_content_length: int = 300,
    search_result_limit: int = 10,
    ignore_keywords: list[str] | None = None,
    block_sites: list[str] | None = None,
    search_keywords: list[str] | None = None,
    search_suffixes: list[str] | None = None,
    progress_callback=None,
) -> list[dict]:

    ignore_keywords = ignore_keywords or []
    block_sites = block_sites or []
    search_keywords = search_keywords or []
    search_suffixes = search_suffixes or []

    query_list = build_query_list(
        name=name,
        search_keywords=search_keywords,
        search_suffixes=search_suffixes,
    )

    docs = []
    seen_urls = set()

    if progress_callback:
        progress_callback(0, max_docs)

    for attempt, query in enumerate(query_list, start=1):
        if len(docs) >= max_docs:
            break

        print(f"[검색 시도 {attempt}] {query} / {len(docs)}/{max_docs}")

        try:
            search_results = search_web(
                query,
                max_results=search_result_limit,
            )
        except Exception as e:
            print(f"[검색 실패] {e}")
            continue

        valid_items = []

        for item in search_results:
            url = item.get("url", "")

            if not url:
                continue

            if url in seen_urls:
                continue

            if should_skip_item(item, ignore_keywords, block_sites):
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
                    **result,
                })

                added_this_round += 1

                if progress_callback:
                    progress_callback(len(docs), max_docs)

        print(f"[추가됨] {added_this_round}개 / 총 {len(docs)}개")

    return docs