from ga.genome import serialize_individual


def deduplicate_population(
    population: list[dict[str, list[str]]]
) -> list[dict[str, list[str]]]:
    seen = set()
    unique = []

    for ind in population:
        key = serialize_individual(ind)

        if key not in seen:
            seen.add(key)
            unique.append(ind)

    return unique