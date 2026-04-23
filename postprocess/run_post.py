import json

from config.config import DATA_DIR


def norm(s: str) -> str:
    return s.strip().lower().replace(" ", "")


def extract_names(value: str, limit: int) -> list[str]:
    if not value or value == "모름":
        return []

    result = []

    for part in value.split(" / "):
        name = part.split("(")[0].strip()
        if name:
            result.append(norm(name))
        if len(result) >= limit:
            break

    return result


def extract_one(value: str) -> str:
    names = extract_names(value, 1)
    return names[0] if names else "모름"


def run(app_state, progress_callback=None, log_callback=None):
    def log(message: str):
        if log_callback:
            log_callback(message)

    def set_progress(value: float):
        if progress_callback:
            progress_callback(value)

    log("[postprocess] 4단계 시작")
    set_progress(0)

    stage1 = app_state.stage1
    if stage1 is None:
        raise ValueError("stage1 결과가 없습니다. 먼저 1단계를 실행하세요.")

    summary_rows = stage1.get("summary_rows", [])
    if not summary_rows:
        raise ValueError("summary_rows가 비어 있습니다.")

    set_progress(20)

    teams = {}
    gear = {}

    for row in summary_rows:
        character = row.get("캐릭터", "").strip()
        if not character:
            continue

        char_key = norm(character)

        party_value = row.get("파티", "")
        weapon_value = row.get("무기", "")
        set_value = row.get("성유물 이름", "")

        # teams.json용
        members = extract_names(party_value, 4)
        teams[char_key] = members

        # gear.json용
        gear[char_key] = {
            "weapon": extract_one(weapon_value),
            "set_name": extract_one(set_value),
        }

    set_progress(60)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    teams_path = DATA_DIR / "teams.json"
    gear_path = DATA_DIR / "gear.json"

    with open(teams_path, "w", encoding="utf-8") as f:
        json.dump(teams, f, ensure_ascii=False, indent=2)

    with open(gear_path, "w", encoding="utf-8") as f:
        json.dump(gear, f, ensure_ascii=False, indent=2)

    result = {
        "status": "done",
        "teams_path": str(teams_path),
        "gear_path": str(gear_path),
    }

    app_state.stage4 = result

    set_progress(100)
    log(f"[postprocess] teams.json 저장 완료: {teams_path}")
    log(f"[postprocess] gear.json 저장 완료: {gear_path}")
    log("[postprocess] 4단계 완료")

    return result