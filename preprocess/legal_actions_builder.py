import csv
import json
import re
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from config.config import LEGAL_ACTIONS_JSON, FAILED_ACTIONS_CSV


BASE = "https://docs.gcsim.app/reference/characters/"
HEADERS = {"User-Agent": "Mozilla/5.0"}


SPECIAL_SLUGS = {
    "Kamisato Ayaka": "ayaka",
    "Kamisato Ayato": "ayato",
    "Shikanoin Heizou": "heizou",
    "Arataki Itto": "itto",
    "Kaedehara Kazuha": "kazuha",
    "Sangonomiya Kokomi": "kokomi",
    "Kuki Shinobu": "kukishinobu",
    "Raiden Shogun": "raiden",
    "Kujou Sara": "sara",
    "Yae Miko": "yaemiko",
    "Yun Jin": "yunjin",
    "Tartaglia": "tartaglia",
    "Yumemizuki Mizuki": "mizuki",
}


def norm(s: str) -> str:
    return str(s).strip().lower()


def name_to_slug(name: str) -> str:
    if name in SPECIAL_SLUGS:
        return SPECIAL_SLUGS[name]

    slug = name.lower()
    slug = re.sub(r"\(.*?\)", "", slug)
    slug = slug.replace("'", "")
    slug = slug.replace("-", "")
    slug = re.sub(r"[^a-z0-9]+", "", slug)
    return slug


def fetch_legal_actions(slug: str) -> dict:
    url = urljoin(BASE, f"{slug}/")
    res = requests.get(url, headers=HEADERS, timeout=20)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    header = None
    for tag in soup.find_all(["h2", "h3"]):
        if "legal actions" in tag.get_text().lower():
            header = tag
            break

    if not header:
        raise Exception("Legal Actions 섹션 없음")

    table = header.find_next("table")
    if table is None:
        raise Exception("Legal Actions 테이블 없음")

    rows = table.find_all("tr")
    result = {}

    for tr in rows[1:]:
        cols = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        if len(cols) < 3:
            continue

        result[cols[0]] = {
            "legal": cols[1],
            "notes": cols[2],
        }

    if not result:
        raise Exception("행동 데이터 비어있음")

    return result


def load_existing_json():
    if not LEGAL_ACTIONS_JSON.exists():
        return {}

    try:
        return json.load(open(LEGAL_ACTIONS_JSON, encoding="utf-8"))
    except:
        return {}


def save_json(data):
    LEGAL_ACTIONS_JSON.parent.mkdir(parents=True, exist_ok=True)
    json.dump(data, open(LEGAL_ACTIONS_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def save_failed(rows):
    FAILED_ACTIONS_CSV.parent.mkdir(parents=True, exist_ok=True)

    with open(FAILED_ACTIONS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["character", "error"])
        writer.writeheader()
        writer.writerows(rows)


def build_legal_actions(app_state, max_workers=4, progress_callback=None, log_callback=None):

    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    characters = getattr(app_state, "characters", {})
    items = list(characters.items())
    total = len(items)

    all_data = load_existing_json()
    failed = []

    done = 0

    # =========================================
    # 1. 처음 검사 (핵심)
    # =========================================
    existing = set(all_data.keys())

    remaining = [
        item for item in items
        if norm(item[0]) not in existing
    ]

    done += len(existing)

    if progress_callback:
        progress_callback(done, total)

    log(f"[skip] {len(existing)}개 이미 존재")

    # =========================================
    # 2. 병렬 실행
    # =========================================
    def worker(item):
        char_key_raw, aliases = item
        char_key = norm(char_key_raw)

        try:
            if isinstance(aliases, list) and len(aliases) >= 2:
                name = aliases[1]
            else:
                name = char_key_raw

            slug = name_to_slug(name)
            data = fetch_legal_actions(slug)

            return char_key, data, None

        except Exception as e:
            return char_key, None, str(e)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, item) for item in remaining]

        for future in as_completed(futures):
            char_key, data, err = future.result()
            done += 1

            if err:
                failed.append({"character": char_key, "error": err})
                log(f"[실패] {char_key}")
            else:
                all_data[char_key] = data
                log(f"[성공] {char_key}")

            save_json(all_data)

            if failed:
                save_failed(failed)

            if progress_callback:
                progress_callback(done, total)

    return {
        "success_count": len(all_data),
        "failed_count": len(failed),
        "json_path": LEGAL_ACTIONS_JSON,
        "csv_path": FAILED_ACTIONS_CSV if failed else "",
    }