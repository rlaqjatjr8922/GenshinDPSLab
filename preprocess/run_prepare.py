import json
from config.config import DATA_DIR


def norm(s: str) -> str:
    return str(s).strip().lower().replace(" ", "")


def run(app_state, progress_callback=None, log_callback=None):
    def log(message: str):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    def set_progress(value: float):
        if progress_callback:
            progress_callback(value)

    log("[postprocess] 4단계 시작")
    set_progress(0)

    characters = getattr(app_state, "characters", None)
    if not isinstance(characters, dict) or not characters:
        raise ValueError("app_state.characters가 비어 있습니다.")

    log(f"[postprocess] characters 개수: {len(characters)}")
    set_progress(20)

    teams = {}
    gear = {}

    total = len(characters)

    for idx, char_key_raw in enumerate(characters.keys(), start=1):
        char_key = norm(char_key_raw)

        teams[char_key] = []
        gear[char_key] = {
            "weapon": "모름",
            "set_name": "모름",
        }

        log(f"[postprocess] {char_key}")
        set_progress(20 + (idx / total) * 40)

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
        "teams_count": len(teams),
        "gear_count": len(gear),
    }

    app_state.stage4 = result

    set_progress(100)
    log(f"[postprocess] teams.json 저장 완료: {teams_path}")
    log(f"[postprocess] gear.json 저장 완료: {gear_path}")
    log(f"[postprocess] teams 개수: {len(teams)}")
    log(f"[postprocess] gear 개수: {len(gear)}")
    log("[postprocess] 4단계 완료")

    return result