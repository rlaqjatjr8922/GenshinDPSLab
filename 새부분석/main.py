import os
import sys
import json
import subprocess

from io_utils.loader import (
    check_required_files,
    load_best_orders,
    load_gear,
    load_legal_actions,
    build_note_parser,
)

from io_utils.progress import (
    load_progress,
    save_progress,
    mark_completed,
)

from io_utils.timeout_log import (
    load_timeout_data,
    save_timeout_data,
    mark_timeout_character,
)

from ga.search import search_best_rotation
from rotation_builder import save_all_orders


MAIN_DPS_IDX = 0


def run_dps(individual, legal_db, note_map):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dps_path = os.path.join(base_dir, "dps.py")

    payload = json.dumps(individual, ensure_ascii=False)

    try:
        result = subprocess.run(
            [sys.executable, dps_path, payload],
            capture_output=True,
            text=False,
            check=True,
            timeout=20,
        )

        raw_stdout = result.stdout.strip()

        try:
            stdout_text = raw_stdout.decode("utf-8")
        except UnicodeDecodeError:
            stdout_text = raw_stdout.decode("cp949", errors="replace")

        return float(stdout_text.strip())

    except subprocess.CalledProcessError as e:
        print("[DPS 오류] subprocess 실패")

        if e.stdout:
            try:
                print(e.stdout.decode("utf-8"))
            except UnicodeDecodeError:
                print(e.stdout.decode("cp949", errors="replace"))

        if e.stderr:
            try:
                print(e.stderr.decode("utf-8"))
            except UnicodeDecodeError:
                print(e.stderr.decode("cp949", errors="replace"))

        return -1.0

    except Exception as e:
        print("[DPS 오류]")
        print(e)
        return -1.0


def main():
    if not check_required_files():
        return

    best_orders = load_best_orders()
    gear_map = load_gear()
    legal_db = load_legal_actions()
    note_map = build_note_parser()

    progress = load_progress()
    completed_set = set(progress.get("completed", []))

    timeout_data = load_timeout_data()
    timeout_set = set(timeout_data.get("timeout_characters", {}).keys())

    print(f"파티 수: {len(best_orders)}")
    print(f"완료: {len(completed_set)} | timeout: {len(timeout_set)}")

    done_count = len(completed_set)
    total_count = len(best_orders)

    for main_name, members in best_orders.items():
        if main_name in completed_set:
            print(f"[스킵] {main_name} (완료)")
            continue

        if main_name in timeout_set:
            print(f"[스킵] {main_name} (timeout)")
            continue

        try:
            print(f"\n[시작] {main_name} → {members}")

            best_result, history = search_best_rotation(
                main_name=main_name,
                party=members,
                main_dps_idx=MAIN_DPS_IDX,
                legal_db=legal_db,
                note_map=note_map,
                dps_runner=run_dps,
            )

            if best_result is None:
                raise ValueError("유효한 결과 없음")

            save_all_orders(
                main_name=best_result["main_name"],
                base_code=best_result["base_code"],
                party_members=best_result["members"],
                action_lines=best_result["action_lines"],
            )

            mark_completed(progress, main_name)
            save_progress(progress)

            done_count += 1

            print(
                f"[완료] {main_name} ({done_count}/{total_count}) | "
                f"T={best_result['T']} | DPS={best_result['best_dps']:.2f}"
            )

        except TimeoutError as e:
            mark_timeout_character(timeout_data, main_name, -1, str(e))
            save_timeout_data(timeout_data)
            print(f"[타임아웃] {main_name}")

        except Exception as e:
            print(f"[오류] {main_name}")
            print(e)


if __name__ == "__main__":
    main()