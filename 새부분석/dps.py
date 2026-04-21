import random

from io_utils.loader import (
    check_required_files,
    load_best_orders,
    load_legal_actions,
    build_note_parser,
)

from ga.search import search_best_rotation


def run_dps(individual, legal_db, note_map):
    return random.uniform(1000, 5000)


def main():
    if not check_required_files():
        return

    best_orders = load_best_orders()
    legal_db = load_legal_actions()
    note_map = build_note_parser()

    for main_name, members in best_orders.items():
        print(f"\n[시작] {main_name}")

        best_result, _ = search_best_rotation(
            main_name=main_name,
            party=members,
            main_dps_idx=0,
            legal_db=legal_db,
            note_map=note_map,
            dps_runner=run_dps,
        )

        print(
            f"[완료] {main_name} | "
            f"T={best_result['T']} | DPS={best_result['best_dps']:.2f}"
        )


if __name__ == "__main__":
    main()