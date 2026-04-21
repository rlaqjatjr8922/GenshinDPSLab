import random
from config import ACTION_KEYS, MUTATION_RATE


def crossover_genomes(parent1: dict, parent2: dict, total_tokens: int, normalize_token_split) -> dict:
    n = len(parent1["token_split"])
    child_tokens = []

    for i in range(n):
        if random.random() < 0.5:
            child_tokens.append(parent1["token_split"][i])
        else:
            child_tokens.append(parent2["token_split"][i])

    child_tokens = normalize_token_split(child_tokens, total_tokens, main_idx=0)

    child_main_weights = {}
    child_support_weights = {}

    for action in ACTION_KEYS:
        child_main_weights[action] = (
            parent1["main_weights"][action]
            if random.random() < 0.5
            else parent2["main_weights"][action]
        )
        child_support_weights[action] = (
            parent1["support_weights"][action]
            if random.random() < 0.5
            else parent2["support_weights"][action]
        )

    return {
        "token_split": child_tokens,
        "main_weights": child_main_weights,
        "support_weights": child_support_weights,
        "fitness": None,
    }


def mutate_genome(genome: dict, total_tokens: int, normalize_token_split):
    if random.random() < MUTATION_RATE:
        i, j = random.sample(range(len(genome["token_split"])), 2)

        if genome["token_split"][j] > 1:
            genome["token_split"][j] -= 1
            genome["token_split"][i] += 1

        genome["token_split"] = normalize_token_split(
            genome["token_split"],
            total_tokens,
            main_idx=0,
        )

    for action in ACTION_KEYS:
        if random.random() < MUTATION_RATE:
            genome["main_weights"][action] = max(
                0.05,
                genome["main_weights"][action] + random.uniform(-0.25, 0.25),
            )

        if random.random() < MUTATION_RATE:
            genome["support_weights"][action] = max(
                0.05,
                genome["support_weights"][action] + random.uniform(-0.25, 0.25),
            )

    genome["fitness"] = None