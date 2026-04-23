import csv
import json
import re
from pathlib import Path

from config.config import DATA_DIR, COLLECTED_DIR


TOKEN_RE = re.compile(r"^\s*(.*?)\((\d+)\)\s*$")


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path: Path):
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_reverse_alias_map(data: dict):
    reverse_map = {}

    for canonical, aliases in (data or {}).items():
        canonical_norm = str(canonical).strip().lower().replace(" ", "")
        if not canonical_norm:
            continue

        reverse_map[canonical_norm] = canonical_norm

        if isinstance(aliases, list):
            for alias in aliases:
                alias_raw = str(alias).strip().lower()
                alias_compact = alias_raw.replace(" ", "")

                if alias_raw:
                    reverse_map[alias_raw] = canonical_norm
                if alias_compact:
                    reverse_map[alias_compact] = canonical_norm

    return reverse_map


def normalize_to_canonical(text: str, reverse_alias_map: dict):
    raw = str(text).strip().lower()
    compact = raw.replace(" ", "")

    if raw in reverse_alias_map:
        return reverse_alias_map[raw]
    if compact in reverse_alias_map:
        return reverse_alias_map[compact]

    return ""


def parse_ranked_tokens(text: str):
    result = []

    if not text:
        return result

    for chunk in str(text).split("/"):
        part = chunk.strip()
        if not part:
            continue

        m = TOKEN_RE.match(part)
        if not m:
            continue

        name = m.group(1).strip()
        score = int(m.group(2))

        if name:
            result.append((name, score))

    return result


def pick_top_party_members(party_text: str, character_reverse_map: dict, limit: int = 4):
    ranked = parse_ranked_tokens(party_text)
    members = []

    if ranked:
        for name, _ in ranked:
            norm = normalize_to_canonical(name, character_reverse_map)
            if norm and norm not in members:
                members.append(norm)
            if len(members) >= limit:
                break
        return members

    for chunk in str(party_text or "").split("/"):
        part = chunk.strip()
        if not part:
            continue

        norm = normalize_to_canonical(part, character_reverse_map)
        if norm and norm not in members:
            members.append(norm)

        if len(members) >= limit:
            break

    return members


def pick_top_one(text: str, reverse_alias_map: dict):
    if not text:
        return ""

    ranked = parse_ranked_tokens(text)
    if ranked:
        return normalize_to_canonical(ranked[0][0], reverse_alias_map)

    first = str(text).split("/")[0].split(",")[0].strip()
    return normalize_to_canonical(first, reverse_alias_map)


def append_summary_row(summary_row: dict, filename: str = "summary.csv"):
    COLLECTED_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = COLLECTED_DIR / filename
    file_exists = csv_path.exists()

    fieldnames = ["캐릭터", "파티", "무기", "성유물 이름"]

    with open(csv_path, "a", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists or csv_path.stat().st_size == 0:
            writer.writeheader()

        writer.writerow({
            "캐릭터": summary_row.get("캐릭터", "모름"),
            "파티": summary_row.get("파티", "모름"),
            "무기": summary_row.get("무기", "모름"),
            "성유물 이름": summary_row.get("성유물 이름", "모름"),
        })


def upsert_collect_outputs(app_state, summary_row: dict, log_callback=None):
    def log(msg: str):
        if log_callback:
            log_callback(msg)

    character_reverse_map = build_reverse_alias_map(app_state.characters or {})
    weapon_reverse_map = build_reverse_alias_map(app_state.weapons or {})
    set_reverse_map = build_reverse_alias_map(app_state.sets or {})

    teams_path = DATA_DIR / "teams.json"
    gear_path = DATA_DIR / "gear.json"

    teams = load_json(teams_path)
    gear = load_json(gear_path)

    character = (
        summary_row.get("character")
        or summary_row.get("name")
        or summary_row.get("캐릭터")
    )

    party_text = summary_row.get("파티")
    weapon_text = summary_row.get("무기")
    set_text = summary_row.get("성유물 이름")

    if not character:
        log("[skip] character 없음")
        return

    char_key = normalize_to_canonical(character, character_reverse_map)
    if not char_key:
        log(f"[skip] 캐릭터 정규화 실패: {character}")
        return

    top_party = pick_top_party_members(party_text, character_reverse_map, 4)
    if len(top_party) == 4:
        teams[char_key] = top_party
    else:
        log(f"[skip party] {char_key}: {party_text}")

    top_weapon = pick_top_one(weapon_text, weapon_reverse_map)
    top_set = pick_top_one(set_text, set_reverse_map)

    if top_weapon and top_set:
        gear[char_key] = {
            "weapon": top_weapon,
            "set_name": top_set,
        }
    else:
        log(f"[skip gear] {char_key}: weapon={weapon_text}, set={set_text}")

    save_json(teams_path, teams)
    save_json(gear_path, gear)

    log(f"[saved] {char_key}")
    log(f"[collect] teams: {len(teams)}개")
    log(f"[collect] gear: {len(gear)}개")