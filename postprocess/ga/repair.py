import random

from core.state import init_party_state, update_state_after_action, get_char_state
from core.legal import get_legal_actions_for_character


def repair_individual(
    individual: dict[str, list[str]],
    token_split: dict[str, int],
    legal_db: dict,
    note_map: dict,
) -> dict[str, list[str]]:
    repaired = {}
    party_members = list(individual.keys())

    for ch, seq in individual.items():
        target_len = token_split[ch]
        party_state = init_party_state(party_members, ch)
        new_seq = []

        for act in seq:
            candidates = get_legal_actions_for_character(
                char=ch,
                legal_db=legal_db,
                note_map=note_map,
                party_state=party_state,
                get_char_state=get_char_state,
            )

            if not candidates:
                break

            base = act.split("[")[0]
            matched = None

            for cand in candidates:
                if cand == act or cand.split("[")[0] == base:
                    matched = cand
                    break

            if matched is None:
                matched = random.choice(candidates)

            new_seq.append(matched)

            update_state_after_action(
                party_state=party_state,
                char=ch,
                action=matched.split("[")[0],
            )

            if len(new_seq) >= target_len:
                break

        while len(new_seq) < target_len:
            candidates = get_legal_actions_for_character(
                char=ch,
                legal_db=legal_db,
                note_map=note_map,
                party_state=party_state,
                get_char_state=get_char_state,
            )

            if not candidates:
                break

            picked = random.choice(candidates)
            new_seq.append(picked)

            update_state_after_action(
                party_state=party_state,
                char=ch,
                action=picked.split("[")[0],
            )

        repaired[ch] = new_seq[:target_len]

    return repaired