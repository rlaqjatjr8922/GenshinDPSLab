import csv
import json
import re
import time
from urllib.parse import urljoin

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
    "Traveler (Anemo)": "traveleranemo",
    "Traveler (Dendro)": "travelerdendro",
    "Traveler (Electro)": "travelerelectro",
    "Traveler (Geo)": "travelergeo",
    "Traveler (Hydro)": "travelerhydro",
    "Traveler (Pyro)": "travelerpyro",
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

        action = cols[0].strip()
        legal = cols[1].strip()
        notes = cols[2].strip()

        result[action] = {
            "legal": legal,
            "notes": notes,
        }

    if not result:
        raise Exception("행동 데이터 비어있음")

    return result


def load_existing_json() -> dict:
    if not LEGAL_ACTIONS_JSON.exists():
        return {}

    try:
        with open(LEGAL_ACTIONS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

        return {}

    except Exception:
        return {}


def save_legal_actions_json(data: dict):
    LEGAL_ACTIONS_JSON.parent.mkdir(parents=True, exist_ok=True)

    with open(LEGAL_ACTIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_failed_csv(failed_rows: list[dict]):
    FAILED_ACTIONS_CSV.parent.mkdir(parents=True, exist_ok=True)

    with open(FAILED_ACTIONS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["character", "official_name", "slug", "error"],
        )
        writer.writeheader()
        writer.writerows(failed_rows)


def build_legal_actions(app_state, progress_callback=None, log_callback=None):
    def log(message: str):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    def set_progress(value: float):
        if progress_callback:
            progress_callback(value)

    characters = getattr(app_state, "characters", None)
    if not isinstance(characters, dict) or not characters:
        raise ValueError("app_state.characters 비어있음")

    all_data = load_existing_json()
    failed_rows = []

    items = list(characters.items())
    total = len(items)

    log(f"[prepare] 기존 저장 데이터: {len(all_data)}개")

    for idx, (char_key_raw, aliases) in enumerate(items, start=1):
        char_key = norm(char_key_raw)
        official_name = ""
        slug = ""

        try:
            if isinstance(aliases, list) and len(aliases) >= 2:
                official_name = str(aliases[1]).strip()
            elif isinstance(aliases, str):
                official_name = aliases.strip()
            else:
                official_name = char_key_raw

            slug = name_to_slug(official_name)

            log(f"[prepare] ({idx}/{total}) {char_key} → {slug}")

            data = fetch_legal_actions(slug)

            all_data[char_key] = data

            # 핵심: 캐릭터 하나 성공할 때마다 바로 저장
            save_legal_actions_json(all_data)

            log(f"[prepare][성공/저장] {char_key}")

        except Exception as e:
            failed_rows.append({
                "character": char_key,
                "official_name": official_name,
                "slug": slug,
                "error": str(e),
            })

            # 실패도 바로 CSV 저장
            save_failed_csv(failed_rows)

            log(f"[prepare][실패/저장] {char_key} → {e}")

        set_progress((idx / total) * 100)
        time.sleep(0.15)

    if failed_rows:
        save_failed_csv(failed_rows)

    result = {
        "success_count": len(all_data),
        "failed_count": len(failed_rows),
        "json_path": LEGAL_ACTIONS_JSON,
        "csv_path": FAILED_ACTIONS_CSV if failed_rows else "",
    }

    log(f"[prepare] JSON 저장 완료: {LEGAL_ACTIONS_JSON}")
    if failed_rows:
        log(f"[prepare] CSV 저장 완료: {FAILED_ACTIONS_CSV}")

    return result