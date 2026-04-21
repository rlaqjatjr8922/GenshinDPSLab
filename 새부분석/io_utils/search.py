from config import (
    T_START,
    T_MAX,
    EARLY_STOP_DROP_RATIO,
    EARLY_STOP_STREAK,
)

from core.state import init_party_state, get_char_state, update_state_after_action
from core.legal import get_legal_actions_for_character
from core.actions import build_party_sequence

from ga.genome import create_random_genome
from ga.genome import normalize_token_split
from ga.operators import crossover_genomes, mutate_genome
from ga.evolution import evolve_population

from gcsim.builder import convert_seq_map_to_action_lines, make_base_code


def build_one_rotation_with_T(
    main_name: str,
    members: list[str],
    gear_map: dict,
    legal_db: dict,
    note_map: dict,
    total_tokens: int,
):
    if len(members) != 4:
        raise ValueError(f"파티 인원 4명이 아님: {main_name} -> {members}")

    for c in members:
        if c not in gear_map:
            raise ValueError(f"gear.json에 없음: {c}")
        if c not in legal_db:
            raise ValueError(f"gcsim_legal_actions_all.json에 없음: {c}")

    best_genome, best_result = evolve_population(
        main_name=main_name,
        members=members,
        gear_map=gear_map,
        legal_db=legal_db,
        note_map=note_map,
        total_tokens=total_tokens,
        create_random_genome=create_random_genome,
        crossover_genomes=lambda parent1, parent2, total_tokens: crossover_genomes(
            parent1=parent1,
            parent2=parent2,
            total_tokens=total_tokens,
            normalize_token_split=normalize_token_split,
        ),
        mutate_genome=lambda genome, total_tokens: mutate_genome(
            genome=genome,
            total_tokens=total_tokens,
            normalize_token_split=normalize_token_split,
        ),
        build_party_sequence=lambda members, token_split, legal_db, note_map, genome: build_party_sequence(
            members=members,
            token_split=token_split,
            legal_db=legal_db,
            note_map=note_map,
            genome=genome,
            init_party_state=init_party_state,
            get_legal_actions_for_character=lambda char, legal_db, note_map, party_state: get_legal_actions_for_character(
                char=char,
                legal_db=legal_db,
                note_map=note_map,
                party_state=party_state,
                get_char_state=get_char_state,
            ),
            update_state_after_action=update_state_after_action,
        ),
        convert_seq_map_to_action_lines=convert_seq_map_to_action_lines,
        make_base_code=make_base_code,
    )

    return {
        "main_name": main_name,
        "members": members,
        "token_split": best_genome["token_split"],
        "seq_map": best_result["seq_map"],
        "base_code": best_result["base_code"],
        "action_lines": best_result["action_lines"],
        "fitness": best_genome["fitness"],
        "total_tokens": total_tokens,
    }


def build_best_rotation_across_T(
    main_name: str,
    members: list[str],
    gear_map: dict,
    legal_db: dict,
    note_map: dict,
):
    global_best_result = None
    global_best_dps = float("-inf")
    bad_streak = 0

    for total_tokens in range(T_START, T_MAX + 1):
        print(f"[탐색] [{main_name}] T={total_tokens} 탐색 시작")

        result = build_one_rotation_with_T(
            main_name=main_name,
            members=members,
            gear_map=gear_map,
            legal_db=legal_db,
            note_map=note_map,
            total_tokens=total_tokens,
        )

        current_dps = result["fitness"]
        print(f"[결과] [{main_name}] T={total_tokens} 결과 DPS={current_dps:.2f}")

        if current_dps > global_best_dps:
            global_best_dps = current_dps
            global_best_result = result
            bad_streak = 0
            print(f"[최고] [{main_name}] 최고 갱신 | T={total_tokens} | DPS={current_dps:.2f}")
        else:
            if global_best_dps > 0 and current_dps <= global_best_dps * EARLY_STOP_DROP_RATIO:
                bad_streak += 1
                print(
                    f"[하락] [{main_name}] T 증가 하락 감지 "
                    f"({bad_streak}/{EARLY_STOP_STREAK}) | "
                    f"기준={global_best_dps * EARLY_STOP_DROP_RATIO:.2f}, 현재={current_dps:.2f}"
                )
            else:
                bad_streak = 0

        if bad_streak >= EARLY_STOP_STREAK:
            print(
                f"[종료] [{main_name}] T 증가 기준 자동 종료 | "
                f"최고 DPS 대비 {int((1 - EARLY_STOP_DROP_RATIO) * 100)}% 이상 낮은 상태가 연속 발생"
            )
            break

    return global_best_result