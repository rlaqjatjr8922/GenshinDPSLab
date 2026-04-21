import random
from config import (
    ACTION_KEYS,
    DEFAULT_ACTION_WEIGHTS,
    MAIN_DPS_BONUS,
    SUPPORT_WEIGHT,
    MAX_TOKEN_RATIO,
    MUTATION_RATE,
)


def create_random_token_split(members: list[str], total_tokens: int, main_idx: int = 0) -> list[int]:
    n = len(members)
    if total_tokens < n:
        raise ValueError(f"total_tokens({total_tokens})는 파티 인원수({n}) 이상이어야 함")

    tokens = [1] * n
    remain = total_tokens - n

    weights = [SUPPORT_WEIGHT] * n
    weights[main_idx] = MAIN_DPS_BONUS

    max_per_char = max(1, int(total_tokens * MAX_TOKEN_RATIO))

    for _ in range(remain):
        candidates = [i for i in range(n) if tokens[i] < max_per_char]
        if not candidates:
            break

        cand_weights = [weights[i] for i in candidates]
        chosen = random.choices(candidates, weights=cand_weights, k=1)[0]
        tokens[chosen] += 1

    while sum(tokens) < total_tokens:
        candidates = [i for i in range(n) if tokens[i] < max_per_char]
        if not candidates:
            raise ValueError("토큰 분배 실패")
        tokens[random.choice(candidates)] += 1

    return tokens


def create_random_weights(scale: float = 0.35) -> dict:
    weights = {}
    for action in ACTION_KEYS:
        base = DEFAULT_ACTION_WEIGHTS.get(action, 0.5)
        delta = random.uniform(-scale, scale)
        weights[action] = max(0.05, base + delta)
    return weights


def create_random_genome(members: list[str], total_tokens: int) -> dict:
    return {
        "token_split": create_random_token_split(members, total_tokens, main_idx=0),
        "main_weights": create_random_weights(),
        "support_weights": create_random_weights(),
        "fitness": None,
    }


def normalize_token_split(token_split: list[int], total_tokens: int, main_idx: int = 0) -> list[int]:
    n = len(token_split)
    token_split = [max(1, int(x)) for x in token_split]

    max_per_char = max(1, int(total_tokens * MAX_TOKEN_RATIO))
    token_split = [min(x, max_per_char) for x in token_split]

    while sum(token_split) < total_tokens:
        candidates = [i for i in range(n) if token_split[i] < max_per_char]
        if not candidates:
            break

        weights = [MAIN_DPS_BONUS if i == main_idx else SUPPORT_WEIGHT for i in candidates]
        chosen = random.choices(candidates, weights=weights, k=1)[0]
        token_split[chosen] += 1

    while sum(token_split) > total_tokens:
        candidates = [i for i in range(n) if token_split[i] > 1]
        if not candidates:
            break
        chosen = random.choice(candidates)
        token_split[chosen] -= 1

    return token_split