import json
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

BASE = "https://docs.gcsim.app/reference/characters/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 입력 파일
CHARACTERS_JSON = os.path.join(BASE_DIR, "characters.json")

# 출력 파일
OUT_JSON = os.path.join(BASE_DIR, "gcsim_legal_actions_all.json")
FAILED_JSON = os.path.join(BASE_DIR, "gcsim_legal_actions_failed.json")


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


def load_characters_map(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    if "characters" not in data:
        raise ValueError("characters.json에 'characters' 키가 없습니다.")

    result = {}
    for internal_key, aliases in data["characters"].items():
        if not isinstance(aliases, list) or len(aliases) < 2:
            raise ValueError(f"형식 이상: {internal_key} -> {aliases}")

        # 두 번째 값을 공식 이름으로 사용
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
            "notes": notes
        }

    if not result:
        raise Exception("행동 데이터가 비어 있음")

    return result


# -------------------------
# 메인
# -------------------------
def main():
    if not os.path.exists(CHARACTERS_JSON):
        print("❌ characters.json 없음")
        print(CHARACTERS_JSON)
        return

    char_map = load_characters_map(CHARACTERS_JSON)

    all_data = {}
    failed = {}

    items = list(char_map.items())

    for i, (internal_key, official_name) in enumerate(items, start=1):
        slug = name_to_slug(official_name)
        print(f"[{i}/{len(items)}] {internal_key} -> {official_name} -> {slug}")

        try:
            data = fetch_legal_actions(slug)
            all_data[internal_key] = data
            print("  ✅ OK")
        except Exception as e:
            failed[internal_key] = {
                "official_name": official_name,
                "slug": slug,
                "error": str(e),
            }
            print("  ❌ FAIL:", e)

        time.sleep(0.2)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    with open(FAILED_JSON, "w", encoding="utf-8") as f:
        json.dump(failed, f, ensure_ascii=False, indent=2)

    print("\n완료")
    print("성공:", len(all_data))
    print("실패:", len(failed))
    print("저장 위치:", BASE_DIR)
    print("출력 파일:", OUT_JSON)
    print("실패 파일:", FAILED_JSON)


if __name__ == "__main__":
    main()