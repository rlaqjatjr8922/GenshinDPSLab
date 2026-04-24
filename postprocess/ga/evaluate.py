def evaluate_one_individual(
    individual: dict[str, list[str]],
    legal_db: dict,
    note_map: dict,
    dps_runner,
) -> tuple[dict[str, list[str]], float]:
    try:
        dps = dps_runner(
            individual=individual,
            legal_db=legal_db,
            note_map=note_map,
        )
        return individual, float(dps or 0.0)
    except Exception:
        return individual, 0.0


def evaluate_population(
    population: list[dict[str, list[str]]],
    legal_db: dict,
    note_map: dict,
    dps_runner,
) -> list[tuple[dict[str, list[str]], float]]:
    results = []

    for individual in population:
        results.append(
            evaluate_one_individual(
                individual=individual,
                legal_db=legal_db,
                note_map=note_map,
                dps_runner=dps_runner,
            )
        )

    return results