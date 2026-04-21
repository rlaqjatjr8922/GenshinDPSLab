import os
import time
import shutil
import csv

from io_utils.loader import (
    check_required_files,
    load_best_orders,
    load_gear,
    load_legal_actions,
    build_note_parser,
)
from ga.search import search_best_rotation


# =========================
# 경로 설정
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
FAILED_DIR = os.path.join(OUTPUT_DIR, "failed_configs")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FAILED_DIR, exist_ok=True)

LOG_FILE = os.path.join(OUTPUT_DIR, "logs.txt")
ERROR_FILE = os.path.join(OUTPUT_DIR, "errors.txt")
BEST_RESULT_FILE = os.path.join(OUTPUT_DIR, "best_results.txt")

MAIN_DPS_IDX = 0


# =========================
# 로그
# =========================
def log(msg: str):
    print(msg, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def log_error(msg: str):
    print(msg, flush=True)
    with open(ERROR_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


# =========================
# TXT 결과 저장
# =========================
def save_best_result(main_name: str, best_result: dict):
    with open(BEST_RESULT_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{main_name}]\n")
        f.write(f"DPS: {best_result['best_dps']:.2f}\n")
        f.write(f"T: {best_result['T']}\n")
        f.write("행동로직:\n")

        best_individual = best_result.get("best_individual", {})
        for char, actions in best_individual.items():
            action_str = ", ".join(actions)
            f.write(f"  {char}: {action_str}\n")

        f.write("\n" + "=" * 50 + "\n\n")


# =========================
# CSV 저장
# =========================
def save_csv_result(main_name: str, best_result: dict):
    csv_dir = os.path.join(OUTPUT_DIR, "csv")
    os.makedirs(csv_dir, exist_ok=True)

    csv_path = os.path.join(csv_dir, f"{main_name}.csv")

    T = best_result["T"]
    dps = best_result["best_dps"]
    individual = best_result["best_individual"]

    row_data = {
        "T": T,
        "DPS": round(dps, 2),
    }

    for char, actions in individual.items():
        row_data[char] = "|".join(actions)

    file_exists = os.path.exists(csv_path)

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row_data.keys())

        if not file_exists:
            writer.writeheader()

        writer.writerow(row_data)


# =========================
# DPS 실행 (gcsim)
# =========================
def run_dps(individual, legal_db, note_map):
    from gcsim.builder import make_base_code, convert_seq_map_to_action_lines
    from gcsim.runner import run_gcsim, extract_dps

    config_path = None

    try:
        members = list(individual.keys())
        gear_map = load_gear()

        base_code = make_base_code(
            main_name=members[0],
            members=members,
            gear_map=gear_map,
        )

        action_lines = convert_seq_map_to_action_lines(
            seq_map=individual,
            members=members,
        )

        ts = int(time.time() * 1000)
        config_path = os.path.join(OUTPUT_DIR, f"temp_{ts}.txt")

        with open(config_path, "w", encoding="utf-8") as f:
            f.write(base_code)
            f.write("\n")
            f.write("\n".join(action_lines))

        output = run_gcsim(config_path)
        dps = extract_dps(output)
        return dps

    except Exception as e:
        log_error(f"[DPS 오류] individual={individual}")
        log_error(f"[DPS 오류 내용] {e}")

        if config_path and os.path.exists(config_path):
            os.makedirs(FAILED_DIR, exist_ok=True)  # 🔥 폴더 보장
            fail_name = f"fail_{int(time.time() * 1000)}.txt"
            fail_path = os.path.join(FAILED_DIR, fail_name)
            shutil.copy(config_path, fail_path)
            log_error(f"[실패 config 저장] {fail_path}")

        return -1.0

    finally:
        if config_path and os.path.exists(config_path):
            os.remove(config_path)


# =========================
# 메인
# =========================
def main():
    if not check_required_files():
        return

    best_orders = load_best_orders()
    legal_db = load_legal_actions()
    note_map = build_note_parser()

    items = list(best_orders.items())

    log(f"파티 수: {len(items)}")

    for idx, (main_name, members) in enumerate(items, start=1):
        log(f"\n[{idx}/{len(items)}] {main_name} → {members}")

        try:
            best_result, _ = search_best_rotation(
                main_name=main_name,
                party=members,
                main_dps_idx=MAIN_DPS_IDX,
                legal_db=legal_db,
                note_map=note_map,
                dps_runner=run_dps,
            )

            if best_result:
                log(f"→ T={best_result['T']} | DPS={best_result['best_dps']:.2f}")

                save_best_result(main_name, best_result)
                save_csv_result(main_name, best_result)

            else:
                log("→ 실패")

        except Exception as e:
            log_error(f"[메인 오류] {main_name}")
            log_error(str(e))


if __name__ == "__main__":
    main()