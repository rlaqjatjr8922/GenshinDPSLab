import copy

from config.config import (
    POP_SIZE,
    GENERATIONS,
    MUTATION_PROB,
    RANDOM_INJECTION_RATIO,
    SURVIVAL_RATIO,
    ELITE_RATIO,
)

from ga.distribute import distribute_tokens
from ga.genome import create_random_individual
from ga.operators import (
    select_parents_weighted,
    crossover_individuals,
    mutate_individual,
)
from ga.dedupe import deduplicate_population
from ga.repair import repair_individual
from ga.evaluate import evaluate_population


def make_random_population(
    party: list[str],
    token_split: dict[str, int],
    legal_db: dict,
    note_map: dict,
    size: int,
) -> list[dict[str, list[str]]]:
    return [
        create_random_individual(
            party=party,
            token_split=token_split,
            legal_db=legal_db,
            note_map=note_map,
        )
        for _ in range(size)
    ]


def evolve_one_T(
    main_name: str,
    party: list[str],
    main_dps_idx: int,
    total_tokens: int,
    legal_db: dict,
    note_map: dict,
    dps_runner,
):
    token_split = distribute_tokens(
        total_tokens=total_tokens,
        party=party,
        main_dps_idx=main_dps_idx,
    )

    population = make_random_population(
        party=party,
        token_split=token_split,
        legal_db=legal_db,
        note_map=note_map,
        size=POP_SIZE,
    )

    best_individual = None
    best_dps = 0.0
    generation_logs = []

    for gen_idx in range(GENERATIONS):
        scored_population = evaluate_population(
            population=population,
            legal_db=legal_db,
            note_map=note_map,
            dps_runner=dps_runner,
        )

        scored_population = [
            (ind, float(dps or 0.0))
            for ind, dps in scored_population
        ]

        scored_population.sort(key=lambda x: x[1], reverse=True)

        if not scored_population:
            generation_logs.append({
                "generation": gen_idx + 1,
                "best_dps": 0.0,
                "worst_dps": 0.0,
                "population_size": 0,
                "best_individual": {},
            })

            population = make_random_population(
                party=party,
                token_split=token_split,
                legal_db=legal_db,
                note_map=note_map,
                size=POP_SIZE,
            )
            continue

        current_best_individual = scored_population[0][0]
        current_best_dps = scored_population[0][1]
        current_worst_dps = scored_population[-1][1]

        if current_best_dps > best_dps or best_individual is None:
            best_dps = current_best_dps
            best_individual = copy.deepcopy(current_best_individual)

        generation_logs.append({
            "generation": gen_idx + 1,
            "best_dps": current_best_dps,
            "worst_dps": current_worst_dps,
            "population_size": len(scored_population),
            "best_individual": copy.deepcopy(current_best_individual),
        })

        survivor_count = max(1, int(POP_SIZE * SURVIVAL_RATIO))
        survivors = scored_population[:survivor_count]

        if not survivors:
            population = make_random_population(
                party=party,
                token_split=token_split,
                legal_db=legal_db,
                note_map=note_map,
                size=POP_SIZE,
            )
            continue

        elite_count = max(1, int(POP_SIZE * ELITE_RATIO))
        elite_count = min(elite_count, len(survivors))
        elites = [copy.deepcopy(x[0]) for x in survivors[:elite_count]]

        random_injection_count = max(1, int(POP_SIZE * RANDOM_INJECTION_RATIO))
        random_injection_count = min(random_injection_count, POP_SIZE - len(elites))

        new_population = []
        new_population.extend(elites)

        target_breed_count = POP_SIZE - random_injection_count

        while len(new_population) < target_breed_count:
            parent1, parent2 = select_parents_weighted(survivors)

            child = crossover_individuals(
                parent1=parent1,
                parent2=parent2,
                token_split=token_split,
            )

            child = repair_individual(
                individual=child,
                token_split=token_split,
                legal_db=legal_db,
                note_map=note_map,
            )

            child = mutate_individual(
                individual=child,
                mutation_prob=MUTATION_PROB,
                legal_db=legal_db,
                note_map=note_map,
            )

            child = repair_individual(
                individual=child,
                token_split=token_split,
                legal_db=legal_db,
                note_map=note_map,
            )

            new_population.append(child)

        for _ in range(random_injection_count):
            new_population.append(
                create_random_individual(
                    party=party,
                    token_split=token_split,
                    legal_db=legal_db,
                    note_map=note_map,
                )
            )

        new_population = deduplicate_population(new_population)

        while len(new_population) < POP_SIZE:
            new_population.append(
                create_random_individual(
                    party=party,
                    token_split=token_split,
                    legal_db=legal_db,
                    note_map=note_map,
                )
            )

        population = new_population[:POP_SIZE]

        print(
            f"[세대 완료] {main_name} | "
            f"T={total_tokens} | "
            f"Gen {gen_idx + 1}/{GENERATIONS} | "
            f"Best={current_best_dps:.2f}",
            flush=True,
        )

    if best_individual is None:
        best_individual = {}

    return {
        "main_name": main_name,
        "T": total_tokens,
        "token_split": token_split,
        "best_dps": best_dps,
        "best_individual": best_individual,
        "generation_logs": generation_logs,
    }