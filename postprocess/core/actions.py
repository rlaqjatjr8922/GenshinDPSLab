import random
from config import DEFAULT_ACTION_WEIGHTS


def get_action_weight(action_name: str, is_main_dps: bool, genome: dict) -> float:
    if genome is not None:
        if is_main_dps:
            return max(0.01, genome["main_weights"].get(action_name, DEFAULT_ACTION_WEIGHTS.get(action_name, 0.5)))
        else:
            return max(0.01, genome["support_weights"].get(action_name, DEFAULT_ACTION_WEIGHTS.get(action_name, 0.5)))

    # fallback (genome 없이 사용 시)
    base = DEFAULT_ACTION_WEIGHTS.get(action_name, 0.5)
    if is_main_dps:
        if action_name in ("attack", "charge", "skill", "burst", "low_plunge", "high_plunge"):
            base *= 1.2
    else:
        if action_name in ("skill", "burst"):
            base *= 1.15
        if action_name in ("attack", "charge"):
            base *= 0.8

    return max(base, 0.01)


def choose_one_action(legal_actions: list[str], is_main_dps: bool, genome: dict | None) -> str:
    weights = [get_action_weight(act, is_main_dps, genome) for act in legal_actions]
    return random.choices(legal_actions, weights=weights, k=1)[0]


def generate_actions_for_character(
    char: str,
    token_count: int,
    legal_db: dict,
    note_map: dict,
    party_state: dict,
    is_main_dps: bool,
    genome: dict,
    get_legal_actions_for_character,
    update_state_after_action,
) -> list[str]:
    sequence = []

    for _ in range(token_count):
        legal_actions = get_legal_actions_for_character(char, legal_db, note_map, party_state)

        if not legal_actions:
            break

        chosen = choose_one_action(legal_actions, is_main_dps=is_main_dps, genome=genome)
        sequence.append(chosen)
        update_state_after_action(party_state, char, chosen)

    return sequence


def build_party_sequence(
    members: list[str],
    token_split: list[int],
    legal_db: dict,
    note_map: dict,
    genome: dict,
    init_party_state,
    get_legal_actions_for_character,
    update_state_after_action,
) -> dict:
    active = members[0]
    party_state = init_party_state(members, active_char=active)

    seq_map = {}

    for idx, char in enumerate(members):
        is_main_dps = (idx == 0)

        seq_map[char] = generate_actions_for_character(
            char=char,
            token_count=token_split[idx],
            legal_db=legal_db,
            note_map=note_map,
            party_state=party_state,
            is_main_dps=is_main_dps,
            genome=genome,
            get_legal_actions_for_character=get_legal_actions_for_character,
            update_state_after_action=update_state_after_action,
        )

    return seq_map