import json
import random

from core.state import init_party_state, update_state_after_action, get_char_state
from core.legal import get_legal_actions_for_character


def generate_character_sequence(
    character_name: str,
    token_count: int,
    members: list[str],
    legal_db: dict,
    note_map: dict,
) -> list[str]:
    party_state = init_party_state(members, character_name)
    sequence = []

    for _ in range(token_count):
        candidates = get_legal_actions_for_character(
            char=character_name,
            legal_db=legal_db,
            note_map=note_map,
            party_state=party_state,
            get_char_state=get_char_state,
        )

        if not candidates:
            break

        chosen = random.choice(candidates)
        sequence.append(chosen)

        base_action = chosen.split("[")[0]
        update_state_after_action(
            party_state=party_state,
            char=character_name,
            action=base_action,
        )

    return sequence


def create_random_individual(
    party: list[str],
    token_split: dict[str, int],
    legal_db: dict,
    note_map: dict,
) -> dict[str, list[str]]:
    return {
        ch: generate_character_sequence(
            character_name=ch,
            token_count=token_split[ch],
            members=party,
            legal_db=legal_db,
            note_map=note_map,
        )
        for ch in party
    }


def serialize_individual(individual: dict[str, list[str]]) -> str:
    normalized = {k: individual[k] for k in sorted(individual.keys())}
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True)