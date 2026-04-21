import os
import json

from config import (
    BEST_ORDERS_JSON,
    GEAR_JSON,
    LEGAL_ACTIONS_JSON,
    LEGAL_PARSER_JSON,
    PROGRESS_JSON,
    TIMEOUT_CHARACTERS_JSON,
    T_START,
    T_MAX,
    EARLY_STOP_DROP_RATIO,
    EARLY_STOP_STREAK,
)

from core.utils import load_json
from core.state import init_party_state, get_char_state, update_state_after_action
from core.legal import get_legal_actions_for_character
from core.actions import build_party_sequence

from ga.genome import create_random_genome
from ga.genome import normalize_token_split
from ga.operators import crossover_genomes, mutate_genome
from ga.evolution import evolve_population

from gcsim.builder import convert_seq_map_to_action_lines, make_base_code
from rotation_builder import save_all_orders


def check_required_files():
    for path, label in [
        (BEST_ORDERS_JSON, "best_orders.json"),
        (GEAR_JSON, "gear.json"),
        (LEGAL_ACTIONS_JSON, "gcsim_legal_actions_all.json"),
        (LEGAL_PARSER_JSON, "gcsim_legal_actions_parser.json"),
    ]:
        if not os.path.exists(path):
            print(f"[오류] {label} 없음")
            print(path)
            return False
    return True


def load_progress():
    if not os.path.exists(PROGRESS_JSON):
        return {"completed": []}

    with open(PROGRESS_JSON, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_progress(progress: dict):
    with open(PROGRESS_JSON, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def mark_completed(progress: dict, main_name: str):
    if "completed" not in progress:
        progress["completed"] = []

    if main_name not in progress["completed"]:
        progress["completed"].append(main_name)


def load_timeout_data():
    if not os.path.exists(TIMEOUT_CHARACTERS_JSON):
        return {"timeout_characters": {}}

    with open(TIMEOUT_CHARACTERS_JSON, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_timeout_data(data: dict):
    with open(TIMEOUT_CHARACTERS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def mark_timeout_character(timeout_data: dict, main_name: str, total_tokens: int, reason: str):
    if "timeout_characters" not in timeout_data:
        timeout_data["timeout_characters"] = {}

    timeout_data["timeout_characters"][main_name] = {
        "total_tokens": total_tokens,
        "reason": reason,
    }


def load_best_orders():
    data = load_json(BEST_ORDERS_JSON)
    result = {}

    for main_name, party in data.items():
        key = main_name.strip().lower()

        if isinstance(party, str):
            members = [x.strip().lower() for x in party.split("/") if x.strip()]
        elif isinstance(party, list):
            members = [x.strip().lower() for x in party]
        else:
            raise ValueError(f"best_orders.json 형식 이상: {main_name} -> {party}")

        result[key] = members

    return result


def load_gear():
    raw = load_json(GEAR_JSON)
    result = {}

    for char_name, info in raw.items():
        key = char_name.strip().lower()
        result[key] = {
            "weapon": info["weapon"].strip().lower(),
            "set_name": info["set_name"].strip().lower(),
        }

    return result


def load_legal_actions():
    raw = load_json(LEGAL_ACTIONS_JSON)
    result = {}

    for char_name, actions in raw.items():
        key = char_name.strip().lower()
        result[key] = actions

    return result


def build_note_parser():
    parser_list = load_json(LEGAL_PARSER_JSON)
    note_map = {}

    for item in parser_list:
        note = item.get("note", "").strip()
        condition = item.get("condition")
        if note:
            note_map[note] = condition

    return note_map


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
    print(f"이미 완료된 캐릭 수: {len(completed_set)}")
    print(f"timeout 캐릭 수: {len(timeout_set)}")

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
            result = build_best_rotation_across_T(
                main_name=main_name,
                members=members,
                gear_map=gear_map,
                legal_db=legal_db,
                note_map=note_map,
            )

            if result is None:
                raise ValueError("유효한 결과 없음")

            save_all_orders(
                main_name=result["main_name"],
                base_code=result["base_code"],
                party_members=result["members"],
                action_lines=result["action_lines"],
            )

            mark_completed(progress, main_name)
            save_progress(progress)

            done_count += 1
            print(
                f"[완료] {main_name} ({done_count}/{total_count}) | "
                f"최종 T={result['total_tokens']} | DPS={result['fitness']:.2f}"
            )

        except TimeoutError as e:
            mark_timeout_character(timeout_data, main_name, -1, str(e))
            save_timeout_data(timeout_data)
            print(f"[스킵] timeout: {main_name}")

        except Exception as e:
            print(f"[오류] {main_name}")
            print(e)


if __name__ == "__main__":
    main()
