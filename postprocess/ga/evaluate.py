import multiprocessing as mp

from config import WORKERS


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


def _evaluate_one_individual_for_pool(args):
    individual, legal_db, note_map, dps_runner = args

    return evaluate_one_individual(
        individual=individual,
        legal_db=legal_db,
        note_map=note_map,
        dps_runner=dps_runner,
    )


def evaluate_population(
    population: list[dict[str, list[str]]],
    legal_db: dict,
    note_map: dict,
    dps_runner,
) -> list[tuple[dict[str, list[str]], float]]:
    jobs = [
        (individual, legal_db, note_map, dps_runner)
        for individual in population
    ]

    with mp.Pool(processes=WORKERS) as pool:
        scored_population = pool.map(_evaluate_one_individual_for_pool, jobs)

    return scored_population