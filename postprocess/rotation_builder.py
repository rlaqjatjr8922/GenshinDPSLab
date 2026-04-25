import os
import sys
import csv
from functools import partial

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "postprocess")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ERROR_FILE = os.path.join(OUTPUT_DIR, "errors.txt")
BEST_CSV_FILE = os.path.join(OUTPUT_DIR, "best_results.csv")

from ga.search import search_best_rotation
from gcsim.gcsim_runner import run_dps as gcsim_run_dps


MAIN_DPS_IDX = 0


def norm(s: str) -> str:
    return str(s).strip().lower().replace(" ", "")


def log_error(msg: str):
    print(msg, flush=True)

    with open(ERROR_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def normalize_best_orders(raw: dict) -> dict:
    result = {}

    for main_name, party in (raw or {}).items():
        key = norm(main_name)

        if isinstance(party, str):
            members = [norm(x) for x in party.split("/") if str(x).strip()]
        elif isinstance(party, list):
            members = [norm(x) for x in party if str(x).strip()]
        else:
            continue

        if len(members) == 4:
            result[key] = members

    return result


def normalize_gear(raw: dict) -> dict:
    result = {}

    for char_name, info in (raw or {}).items():
        if not isinstance(info, dict):
            continue

        weapon = info.get("weapon")
        set_name = info.get("set_name")

        if not weapon or not set_name:
            continue

        result[norm(char_name)] = {
            "weapon": norm(weapon),
            "set_name": norm(set_name),
        }

    return result


def normalize_legal_actions(raw: dict) -> dict:
    result = {}

    for char_name, actions in (raw or {}).items():
        if isinstance(actions, dict):
            result[norm(char_name)] = actions

    return result


def build_note_map(raw_parser) -> dict:
    note_map = {}

    if isinstance(raw_parser, dict):
        for note, condition in raw_parser.items():
            note = str(note).strip()
            if note:
                note_map[note] = condition
        return note_map

    if isinstance(raw_parser, list):
        for item in raw_parser:
            if not isinstance(item, dict):
                continue

            note = str(item.get("note", "")).strip()
            condition = item.get("condition")

            if note:
                note_map[note] = condition

    return note_map


def load_existing_results_csv():
    results_map = {}

    if not os.path.exists(BEST_CSV_FILE):
        return results_map

    with open(BEST_CSV_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            main_name = (row.get("main_name") or "").strip()
            if not main_name:
                continue

            try:
                t_value = int(float(row.get("T", 0)))
            except Exception:
                t_value = 0

            try:
                best_dps = float(row.get("DPS", 0))
            except Exception:
                best_dps = 0.0

            best_individual = {}

            for key, value in row.items():
                if key in {"main_name", "T", "DPS"}:
                    continue

                value = (value or "").strip()
                if not value:
                    continue

                actions = [x.strip() for x in value.split("|") if x.strip()]
                if actions:
                    best_individual[key] = actions

            results_map[main_name] = {
                "T": t_value,
                "best_dps": best_dps,
                "best_individual": best_individual,
            }

    return results_map


def save_best_results_csv(results_map: dict):
    all_chars = set()

    for best_result in results_map.values():
        for char in best_result.get("best_individual", {}).keys():
            all_chars.add(char)

    fieldnames = ["main_name", "T", "DPS"] + sorted(all_chars)
    rows = []

    for main_name, best_result in results_map.items():
        row = {
            "main_name": main_name,
            "T": best_result["T"],
            "DPS": round(best_result["best_dps"], 2),
        }

        for char in all_chars:
            row[char] = ""

        for char, actions in best_result.get("best_individual", {}).items():
            row[char] = "|".join(actions)

        rows.append(row)

    with open(BEST_CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_summary_csv(main_name: str, history: list, output_dir: str):
    char_dir = os.path.join(output_dir, main_name)
    os.makedirs(char_dir, exist_ok=True)

    path = os.path.join(char_dir, "summary.csv")

    history_sorted = sorted(history or [], key=lambda x: x.get("T", 0))

    if not history_sorted:
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write("")
        return

    max_gen = max(len(result.get("generation_logs", [])) for result in history_sorted)
    lines = []

    for gen_idx in range(max_gen):
        parts = []

        for result in history_sorted:
            t_value = result.get("T", "")
            gen_logs = result.get("generation_logs", [])

            if gen_idx >= len(gen_logs):
                continue

            log = gen_logs[gen_idx]
            best_ind = log.get("best_individual", {})

            parts.append(f"T={t_value}")
            parts.append(f"Gen={gen_idx + 1}")

            for char in sorted(best_ind.keys()):
                actions = best_ind[char]
                parts.append(f"{char}:{'|'.join(actions)}")

        lines.append(", ".join(parts))

    with open(path, "w", encoding="utf-8-sig") as f:
        for line in lines:
            f.write(line + "\n")


def run_dps_for_character(
    individual,
    legal_db,
    note_map,
    main_name: str,
    output_dir: str,
    gear_map: dict,
):
    try:
        def load_gear_from_app_state():
            return gear_map

        dps = gcsim_run_dps(
            individual=individual,
            output_dir=output_dir,
            load_gear_func=load_gear_from_app_state,
        )

        if dps is None or dps <= 0:
            return 0.0

        return dps

    except Exception as e:
        log_error(f"[DPS 오류] {main_name} | individual={individual}")
        log_error(f"[DPS 오류 내용] {e}")
        return 0.0


def run(app_state, progress_callback=None, log_callback=None):
    def log(msg: str):
        if log_callback:
            log_callback(msg)
        else:
            print(msg, flush=True)

    def set_progress(file_done, file_total, t_now=0, t_total=1, gen_now=0, gen_total=1):
        if progress_callback:
            progress_callback(
                file_done,
                file_total,
                t_now,
                t_total,
                gen_now,
                gen_total,
            )

    log("[rotation_builder] 시작")

    best_orders = normalize_best_orders(app_state.best_orders)
    gear_map = normalize_gear(app_state.gear)
    legal_db = normalize_legal_actions(app_state.gcsim_legal_actions_all)
    note_map = build_note_map(app_state.gcsim_legal_actions_parser)

    if not best_orders:
        raise ValueError("app_state.best_orders 비어 있음")

    if not gear_map:
        raise ValueError("app_state.gear 비어 있음")

    if not legal_db:
        raise ValueError("app_state.gcsim_legal_actions_all 비어 있음")

    if not note_map:
        raise ValueError("app_state.gcsim_legal_actions_parser 비어 있음")

    items = list(best_orders.items())
    total = len(items)

    set_progress(0, total, 0, 1, 0, 1)

    results_map = load_existing_results_csv()
    done_names = set(results_map.keys())

    log(f"파티 수: {total}")
    log(f"기존 완료 수: {len(done_names)}")

    success_count = 0
    failed = []

    for idx, (main_name, members) in enumerate(items, start=1):
        set_progress(idx - 1, total, 0, 1, 0, 1)

        if main_name in done_names:
            log(f"[{idx}/{total}] {main_name} → 이미 완료, 스킵")
            set_progress(idx, total, 1, 1, 1, 1)
            continue

        missing_gear = [m for m in members if m not in gear_map]
        if missing_gear:
            msg = f"{main_name} gear 없음: {missing_gear}"
            log(f"[스킵] {msg}")
            failed.append(msg)
            set_progress(idx, total, 1, 1, 1, 1)
            continue

        log(f"[{idx}/{total}] {main_name} → {members}")

        char_output_dir = os.path.join(OUTPUT_DIR, main_name)
        os.makedirs(char_output_dir, exist_ok=True)

        run_dps = partial(
            run_dps_for_character,
            main_name=main_name,
            output_dir=char_output_dir,
            gear_map=gear_map,
        )

        try:
            best_result, history = search_best_rotation(
                main_name=main_name,
                party=members,
                main_dps_idx=MAIN_DPS_IDX,
                legal_db=legal_db,
                note_map=note_map,
                dps_runner=run_dps,
                progress_callback=lambda t_now, t_total, gen_now, gen_total: set_progress(
                    idx - 1,
                    total,
                    t_now,
                    t_total,
                    gen_now,
                    gen_total,
                ),
            )

            save_summary_csv(main_name, history, OUTPUT_DIR)

            if best_result:
                log(
                    f"→ 최고 T={best_result['T']} | "
                    f"최고 DPS={best_result['best_dps']:.2f}"
                )

                results_map[main_name] = {
                    "T": best_result["T"],
                    "best_dps": best_result["best_dps"],
                    "best_individual": best_result.get("best_individual", {}),
                }

                save_best_results_csv(results_map)
                done_names.add(main_name)
                success_count += 1
            else:
                log("→ 실패")
                failed.append(main_name)

        except Exception as e:
            log_error(f"[메인 오류] {main_name}")
            log_error(str(e))
            failed.append(f"{main_name}: {e}")

        set_progress(idx, total, 1, 1, 1, 1)

    result = {
        "status": "done",
        "total": total,
        "success_count": success_count,
        "failed_count": len(failed),
        "output_dir": OUTPUT_DIR,
        "best_csv": BEST_CSV_FILE,
    }

    app_state.stage4 = result

    set_progress(total, total, 1, 1, 1, 1)
    log("[rotation_builder] 완료")

    return result


if __name__ == "__main__":
    import multiprocessing as mp
    from shared.data_loader import load_all

    mp.freeze_support()

    state = load_all()
    run(state)