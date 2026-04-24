import os
import csv
from functools import partial

from io_utils.loader import (
    check_required_files,
    load_best_orders,
    load_gear,
    load_legal_actions,
    build_note_parser,
)
from ga.search import search_best_rotation
from gcsim_runner import run_dps as gcsim_run_dps


# =========================
# 경로 설정
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

ERROR_FILE = os.path.join(OUTPUT_DIR, "errors.txt")
BEST_CSV_FILE = os.path.join(OUTPUT_DIR, "best_results.csv")

MAIN_DPS_IDX = 0


# =========================
# 에러 로그
# =========================
def log_error(msg: str):
    print(msg, flush=True)
    with open(ERROR_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


# =========================
# 기존 best_results.csv 읽기
# =========================
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
                T = int(float(row.get("T", 0)))
            except:
                T = 0

            try:
                best_dps = float(row.get("DPS", 0))
            except:
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
                "T": T,
                "best_dps": best_dps,
                "best_individual": best_individual,
            }

    return results_map


# =========================
# 최고 결과 CSV 저장
# =========================
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


# =========================
# summary.csv 저장
# 형식:
# T=4, Gen=1, albedo:..., bennett:..., T=5, Gen=1, ...
# T=4, Gen=2, albedo:..., bennett:..., T=5, Gen=2, ...
# =========================
def save_summary_csv(main_name: str, history: list, output_dir: str):
    char_dir = os.path.join(output_dir, main_name)
    os.makedirs(char_dir, exist_ok=True)

    path = os.path.join(char_dir, "summary.csv")

    history_sorted = sorted(history, key=lambda x: x.get("T", 0))
    if not history_sorted:
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write("")
        return

    max_gen = max(len(result.get("generation_logs", [])) for result in history_sorted)
    lines = []

    for gen_idx in range(max_gen):
        parts = []

        for result in history_sorted:
            T = result.get("T", "")
            gen_logs = result.get("generation_logs", [])

            if gen_idx >= len(gen_logs):
                continue

            log = gen_logs[gen_idx]
            best_ind = log.get("best_individual", {})

            parts.append(f"T={T}")
            parts.append(f"Gen={gen_idx + 1}")

            for char in sorted(best_ind.keys()):
                actions = best_ind[char]
                parts.append(f"{char}:{'|'.join(actions)}")

        lines.append(", ".join(parts))

    with open(path, "w", encoding="utf-8-sig") as f:
        for line in lines:
            f.write(line + "\n")


# =========================
# 병렬용 DPS 실행 함수
# main 밖 최상위 함수여야 pickle 가능
# =========================
def run_dps_for_character(
    individual,
    legal_db,
    note_map,
    main_name: str,
    output_dir: str,
):
    try:
        dps = gcsim_run_dps(
            individual=individual,
            output_dir=output_dir,
            load_gear_func=load_gear,
        )

        if dps is None or dps <= 0:
            return 0.0

        return dps

    except Exception as e:
        log_error(f"[DPS 오류] {main_name} | individual={individual}")
        log_error(f"[DPS 오류 내용] {e}")
        return 0.0


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

    results_map = load_existing_results_csv()
    done_names = set(results_map.keys())

    print(f"파티 수: {len(items)}", flush=True)
    print(f"기존 완료 수: {len(done_names)}", flush=True)

    for idx, (main_name, members) in enumerate(items, start=1):
        if main_name in done_names:
            print(f"\n[{idx}/{len(items)}] {main_name} → 이미 완료, 스킵", flush=True)
            continue

        print(f"\n[{idx}/{len(items)}] {main_name} → {members}", flush=True)

        char_output_dir = os.path.join(OUTPUT_DIR, main_name)
        os.makedirs(char_output_dir, exist_ok=True)

        run_dps = partial(
            run_dps_for_character,
            main_name=main_name,
            output_dir=char_output_dir,
        )

        try:
            best_result, history = search_best_rotation(
                main_name=main_name,
                party=members,
                main_dps_idx=MAIN_DPS_IDX,
                legal_db=legal_db,
                note_map=note_map,
                dps_runner=run_dps,
            )

            save_summary_csv(main_name, history, OUTPUT_DIR)

            if best_result:
                print(
                    f"→ 최고 T={best_result['T']} | 최고 DPS={best_result['best_dps']:.2f}",
                    flush=True
                )

                results_map[main_name] = {
                    "T": best_result["T"],
                    "best_dps": best_result["best_dps"],
                    "best_individual": best_result.get("best_individual", {}),
                }

                save_best_results_csv(results_map)
                done_names.add(main_name)
            else:
                print("→ 실패", flush=True)

        except Exception as e:
            log_error(f"[메인 오류] {main_name}")
            log_error(str(e))

    print("\n모든 캐릭터 최고 기록 저장 완료", flush=True)


if __name__ == "__main__":
    import multiprocessing as mp
    mp.freeze_support()
    main()