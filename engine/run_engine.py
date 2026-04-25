import json

from config.config import DATA_DIR, OUTPUT_DIR
from engine.rotation_order import save_all_orders


TEAMS_JSON = DATA_DIR / "teams.json"
GEAR_JSON = DATA_DIR / "gear.json"

FAILED_CSV_PATH = OUTPUT_DIR / "failed_runs.csv"
FAILED_JSON_PATH = OUTPUT_DIR / "failed_runs.json"


def norm(s: str) -> str:
    return str(s).strip().lower().replace(" ", "")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_failed_csv(failed_set):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    failed_list = sorted(failed_set)

    with open(FAILED_CSV_PATH, "w", encoding="utf-8") as f:
        f.write(",".join(failed_list))


def save_failed_json(failed_set):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    failed_list = sorted(failed_set)

    with open(FAILED_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(failed_list, f, ensure_ascii=False, indent=2)


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
        else:
            print(message)

    def set_ui_progress(bar_index: int, percent: float, text: str = ""):
        ui = getattr(app_state, "ui", None)
        if not ui:
            return

        ui.set_progress(bar_index, percent)

        if text:
            ui.set_progress_text(bar_index, text)

    log("[engine] 3단계 시작")

    if not TEAMS_JSON.exists():
        raise FileNotFoundError(f"teams.json 없음: {TEAMS_JSON}")

    if not GEAR_JSON.exists():
        raise FileNotFoundError(f"gear.json 없음: {GEAR_JSON}")

    teams_map = load_json(TEAMS_JSON)
    gear_map = load_json(GEAR_JSON)

    items = list(teams_map.items())
    total_chars = len(items)

    if total_chars == 0:
        raise ValueError("teams.json이 비어 있습니다.")

    set_ui_progress(0, 0, f"캐릭터 진행도: 0 / {total_chars}")
    set_ui_progress(1, 0, "시뮬레이션 진행도: 0 / 24")

    if progress_callback:
        progress_callback(0)

    results = []
    failed_set = set()

    for i, (main_name, members) in enumerate(items, start=1):
        char_percent = ((i - 1) / total_chars) * 100.0

        set_ui_progress(
            0,
            char_percent,
            f"캐릭터 진행도: {i - 1} / {total_chars}",
        )
        set_ui_progress(
            1,
            0,
            f"{main_name} 시뮬레이션: 0 / 24",
        )

        if main_name in failed_set:
            log(f"[스킵] {main_name} (이미 실패)")
            continue

        try:
            log(f"[{i}/{total_chars}] {main_name} 시작")

            main_name, base_code, members = make_gcsim(
                main_name,
                members,
                gear_map,
            )

            def sim_progress_callback(done, sim_total):
                percent = (done / sim_total) * 100.0

                set_ui_progress(
                    1,
                    percent,
                    f"{main_name} 시뮬레이션: {done} / {sim_total}",
                )

            result = save_all_orders(
                main_name=main_name,
                base_code=base_code,
                party_members=members,
                progress_callback=sim_progress_callback,
            )

            results.append(result)
            log(f"[{i}/{total_chars}] {main_name} 완료")

        except Exception as e:
            log(f"[오류] {main_name}: {e}")
            failed_set.add(main_name)
            save_failed_csv(failed_set)
            save_failed_json(failed_set)
            log(f"[engine] 실패 저장 완료: {main_name}")

        char_percent = (i / total_chars) * 100.0

        set_ui_progress(
            0,
            char_percent,
            f"캐릭터 진행도: {i} / {total_chars}",
        )

        if progress_callback:
            progress_callback(char_percent)

    app_state.stage3 = {
        "status": "done",
        "results": results,
        "count": len(results),
        "failed_count": len(failed_set),
        "failed_csv_path": str(FAILED_CSV_PATH) if failed_set else "",
        "failed_json_path": str(FAILED_JSON_PATH) if failed_set else "",
    }

    set_ui_progress(0, 100, f"캐릭터 진행도: {total_chars} / {total_chars}")
    set_ui_progress(1, 100, "시뮬레이션 진행도 완료")

    if progress_callback:
        progress_callback(100)

    log("[engine] 3단계 완료")
    return app_state.stage3