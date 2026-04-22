import json

from config.config import DATA_DIR
from engine.rotation_order import save_all_orders


TEAMS_JSON = DATA_DIR / "teams.json"
GEAR_JSON = DATA_DIR / "gear.json"


def norm(s: str) -> str:
    return s.strip().lower()


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def make_gcsim(main_name: str, party_members: list[str], gear_map: dict):
    members = [norm(m) for m in party_members]
    active = members[0]

    blocks = []

    for idx, m in enumerate(members, start=1):
        if m not in gear_map:
            raise ValueError(f"gear.json에 장비 정보 없음: {m}")

        char_weapon = norm(gear_map[m]["weapon"])
        char_set = norm(gear_map[m]["set_name"])

        block = f"""
# =========================
# 캐릭터 {idx} ({m})
# =========================
{m} char lvl=90/90 cons=0 talent=9,9,9;
{m} add weapon="{char_weapon}" refine=1 lvl=90/90;
{m} add set="{char_set}" count=4;
"""
        blocks.append(block)

    base_code = f"""options iteration=1000 duration=10.5 swap_delay=6 workers=4;
options hitlag=true defhalt=false ignore_burst_energy=true;

target lvl=100 resist=0.1 pos=1,0 radius=3 freeze_resist=0;

active {active};
{''.join(blocks)}
"""

    return main_name, base_code, members


def run(app_state, progress_callback=None, log_callback=None):
    def log(message: str):
        if log_callback:
            log_callback(message)

    def set_progress(value: float):
        if progress_callback:
            progress_callback(value)

    if not TEAMS_JSON.exists():
        raise FileNotFoundError(f"teams.json 없음: {TEAMS_JSON}")

    if not GEAR_JSON.exists():
        raise FileNotFoundError(f"gear.json 없음: {GEAR_JSON}")

    teams_map = load_json(TEAMS_JSON)
    gear_map = load_json(GEAR_JSON)

    items = list(teams_map.items())
    total = len(items)

    if total == 0:
        raise ValueError("teams.json이 비어 있습니다.")

    results = []

    for i, (main_name, members) in enumerate(items, start=1):
        try:
            log(f"[{i}/{total}] {main_name} 시작")
            main_name, base_code, members = make_gcsim(main_name, members, gear_map)
            result = save_all_orders(
                main_name=main_name,
                base_code=base_code,
                party_members=members,
            )
            results.append(result)
            log(f"[{i}/{total}] {main_name} 완료")
        except Exception as e:
            log(f"[오류] {main_name}: {e}")

        set_progress((i / total) * 100.0)

    app_state.stage3 = {
        "status": "done",
        "results": results,
        "count": len(results),
    }

    log("[engine] 3단계 완료")
    return app_state.stage3