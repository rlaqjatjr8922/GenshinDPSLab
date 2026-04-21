def evaluate_one_individual(
    individual: dict[str, list[str]],
    legal_db: dict,
    note_map: dict,
    dps_runner,
) -> tuple[dict[str, list[str]], float]:
    dps = dps_runner(
        individual=individual,
        legal_db=legal_db,
        note_map=note_map,
    )
    return individual, dps


def evaluate_population(
    population: list[dict[str, list[str]]],
    legal_db: dict,
    note_map: dict,
    dps_runner,
) -> list[tuple[dict[str, list[str]], float]]:
    scored_population = []

    for individual in population:
        scored = evaluate_one_individual(
            individual=individual,
            legal_db=legal_db,
            note_map=note_map,
            dps_runner=dps_runner,
        )
        scored_population.append(scored)

    return scored_population