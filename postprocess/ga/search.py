from config.config import (
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
    progress_callback=None,
):
    global_best_result = None
    global_best_dps = float("-inf")
    drop_streak = 0
    history = []

    for total_tokens in range(T_START, T_MAX + 1):
        if progress_callback:
            progress_callback(
                total_tokens,
                T_MAX,
                0,
                1,
            )

        result = evolve_one_T(
            main_name=main_name,
            party=party,
            main_dps_idx=main_dps_idx,
            total_tokens=total_tokens,
            legal_db=legal_db,
            note_map=note_map,
            dps_runner=dps_runner,
            progress_callback=progress_callback,
        )

        current_dps = result["best_dps"]
        history.append(result)

        if current_dps > global_best_dps:
            global_best_dps = current_dps
            global_best_result = result
            drop_streak = 0
        else:
            if (
                global_best_dps > 0
                and current_dps <= global_best_dps * (1 - EARLY_STOP_DROP_RATIO)
            ):
                drop_streak += 1
            else:
                drop_streak = 0

        if drop_streak >= EARLY_STOP_STREAK:
            break

    return global_best_result, history