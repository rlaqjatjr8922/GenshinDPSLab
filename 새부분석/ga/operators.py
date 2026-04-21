import copy
import random

from core.state import init_party_state, update_state_after_action, get_char_state
from core.legal import get_legal_actions_for_character


def select_parents_weighted(
    scored_population: list[tuple[dict[str, list[str]], float]]
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    individuals = [x[0] for x in scored_population]
    scores = [max(x[1], 1.0) for x in scored_population]

    parent1 = random.choices(individuals, weights=scores, k=1)[0]
    parent2 = random.choices(individuals, weights=scores, k=1)[0]

    return copy.deepcopy(parent1), copy.deepcopy(parent2)


def crossover_individuals(
    parent1: dict[str, list[str]],
    parent2: dict[str, list[str]],
    token_split: dict[str, int],
) -> dict[str, list[str]]:
    child = {}

    for ch in parent1.keys():
        seq1 = parent1[ch]
        seq2 = parent2[ch]
        target_len = token_split[ch]

        if not seq1 and not seq2:
            child[ch] = []
            continue

        mode = random.choice(["by_character", "split"])

        if mode == "by_character":
            picked = seq1 if random.random() < 0.5 else seq2
            child[ch] = picked[:target_len]
        else:
            cut1 = random.randint(0, len(seq1)) if seq1 else 0
            cut2 = random.randint(0, len(seq2)) if seq2 else 0
            new_seq = seq1[:cut1] + seq2[cut2:]
            child[ch] = new_seq[:target_len]

    return child


def mutate_individual(
    individual: dict[str, list[str]],
    mutation_prob: float,
    legal_db: dict,
    note_map: dict,
) -> dict[str, list[str]]:
    new_ind = copy.deepcopy(individual)

    if random.random() >= mutation_prob:
        return new_ind

    target_char = random.choice(list(new_ind.keys()))
    old_seq = new_ind[target_char]

    if not old_seq:
        return new_ind

    idx = random.randrange(len(old_seq))
    party_members = list(new_ind.keys())
    party_state = init_party_state(party_members, target_char)

    for act in old_seq[:idx]:
        base_action = act.split("[")[0]
        update_state_after_action(
            party_state=party_state,
            char=target_char,
            action=base_action,
        )

    candidates = get_legal_actions_for_character(
        char=target_char,
        legal_db=legal_db,
        note_map=note_map,
        party_state=party_state,
        get_char_state=get_char_state,
    )

    if candidates:
        old_seq[idx] = random.choice(candidates)

    new_ind[target_char] = old_seq
    return new_ind