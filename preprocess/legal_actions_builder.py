import json
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from config.config import (
    CHARACTERS_JSON,
    LEGAL_ACTIONS_JSON,
    FAILED_DIR,
)

BASE = "https://docs.gcsim.app/reference/characters/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

FAILED_JSON = FAILED_DIR / "gcsim_legal_actions_failed_characters.json"


# -------------------------
# slug 예외 처리
# -------------------------
SPECIAL_SLUGS = {
    "Kamisato Ayaka": "ayaka",
    "Kamisato Ayato": "ayato",
    "Shikanoin Heizou": "heizou",
    "Arataki Itto": "itto",
    "Kaedehara Kazuha": "kazuha",
    "Sangonomiya Kokomi": "kokomi",
    "Kuki Shinobu": "kuki",
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


# -------------------------
# 유틸
# -------------------------
def norm(s: str) -> str:
    return s.strip().lower()


def load_characters_map(path) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    if "characters" not in data:
        raise ValueError("characters.json에 'characters' 키가 없습니다.")

    result = {}
    for internal_key, aliases in data["characters"].items():
        if not isinstance(aliases, list) or len(aliases) < 2:
            raise ValueError(f"형식 이상: {internal_key} -> {aliases}")

        # 예: "raiden": ["raiden", "Raiden Shogun"]
        official_name = aliases[1].strip()
        result[norm(internal_key)] = official_name

    return result


def name_to_slug(name: str) -> str:
    if name in SPECIAL_SLUGS:
        return SPECIAL_SLUGS[name]

    slug = name.lower()
    slug = re.sub(r"\(.*?\)", "", slug)
    slug = slug.replace("'", "")
    slug = slug.replace("-", "")
    slug = re.sub(r"[^a-z0-9]+", "", slug)
    return slug


# -------------------------
# 크롤링
# -------------------------
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
        raise Exception("행동 데이터가 비어 있음")

    return result


# -------------------------
# 실행 함수
# -------------------------
def build_legal_actions(progress_callback=None, log_callback=None):
    def log(message: str):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    def set_progress(value: float):
        if progress_callback:
            progress_callback(value)

    char_map = load_characters_map(CHARACTERS_JSON)

    all_data = {}
    failed = {}

    items = list(char_map.items())
    total = len(items)

    for i, (internal_key, official_name) in enumerate(items, start=1):
        slug = name_to_slug(official_name)
        log(f"[{i}/{total}] {internal_key} -> {official_name} -> {slug}")

        try:
            data = fetch_legal_actions(slug)
            all_data[internal_key] = data
            log("  ✅ OK")
        except Exception as e:
            failed[internal_key] = {
                "official_name": official_name,
                "slug": slug,
                "error": str(e),
            }
            log(f"  ❌ FAIL: {e}")

        set_progress((i / total) * 100.0)
        time.sleep(0.2)

    LEGAL_ACTIONS_JSON.parent.mkdir(parents=True, exist_ok=True)
    FAILED_JSON.parent.mkdir(parents=True, exist_ok=True)

    with open(LEGAL_ACTIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    if failed:
        with open(FAILED_JSON, "w", encoding="utf-8") as f:
            json.dump(failed, f, ensure_ascii=False, indent=2)

    log("")
    log("[legal_actions] 완료")
    log(f"성공: {len(all_data)}")
    log(f"실패: {len(failed)}")
    log(f"출력 파일: {LEGAL_ACTIONS_JSON}")
    if failed:
        log(f"실패 파일: {FAILED_JSON}")

    return {
        "all_data": all_data,
        "failed": failed,
    }


def main():
    build_legal_actions()


if __name__ == "__main__":
    main()