from config import (
    T_START,
    T_MAX,
    EARLY_STOP_DROP_RATIO,
    EARLY_STOP_STREAK,
)

from ga.evolution import evolve_one_T


def search_best_rotation(
    main_name: str,
    party: list[str],
    main_dps_idx: int,
    legal_db: dict,
    note_map: dict,
    dps_runner,
):
    global_best_result = None
    global_best_dps = float("-inf")
    drop_streak = 0
    history = []

    for total_tokens in range(T_START, T_MAX + 1):
        print(f"[탐색] [{main_name}] T={total_tokens} 시작")

        result = evolve_one_T(
            main_name=main_name,
            party=party,
            main_dps_idx=main_dps_idx,
            total_tokens=total_tokens,
            legal_db=legal_db,
            note_map=note_map,
            dps_runner=dps_runner,
        )

        current_dps = result["best_dps"]
        history.append(result)

        print(
            f"[결과] [{main_name}] "
            f"T={total_tokens} | DPS={current_dps:.2f} | "
            f"split={result['token_split']}"
        )

        if current_dps > global_best_dps:
            global_best_dps = current_dps
            global_best_result = result
            drop_streak = 0

            print(
                f"[최고 갱신] [{main_name}] "
                f"T={total_tokens} | DPS={current_dps:.2f}"
            )
        else:
            if global_best_dps > 0 and current_dps <= global_best_dps * (1 - EARLY_STOP_DROP_RATIO):
                drop_streak += 1
                print(
                    f"[하락 감지] [{main_name}] "
                    f"{drop_streak}/{EARLY_STOP_STREAK} | "
                    f"기준={global_best_dps * (1 - EARLY_STOP_DROP_RATIO):.2f}, "
                    f"현재={current_dps:.2f}"
                )
            else:
                drop_streak = 0

        if drop_streak >= EARLY_STOP_STREAK:
            print(
                f"[종료] [{main_name}] "
                f"T 증가 탐색 중단 | "
                f"최고 DPS 대비 {int(EARLY_STOP_DROP_RATIO * 100)}% 이상 하락 연속 발생"
            )
            break

    return global_best_result, history