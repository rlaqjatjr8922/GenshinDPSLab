from config import POPULATION_SIZE, GENERATIONS, ELITE_RATIO
from rotation_builder import save_all_orders
from gcsim.runner import run_gcsim, extract_dps
import subprocess


def evaluate_genome(
    genome: dict,
    main_name: str,
    members: list[str],
    gear_map: dict,
    legal_db: dict,
    note_map: dict,
    build_party_sequence,
    convert_seq_map_to_action_lines,
    make_base_code,
):
    seq_map = build_party_sequence(
        members=members,
        token_split=genome["token_split"],
        legal_db=legal_db,
        note_map=note_map,
        genome=genome,
    )

    action_lines = convert_seq_map_to_action_lines(seq_map, members)
    base_code = make_base_code(main_name, members, gear_map)

    config_path = save_all_orders(
        main_name=main_name,
        base_code=base_code,
        party_members=members,
        action_lines=action_lines,
    )

    try:
        output = run_gcsim(config_path)
        dps = extract_dps(output)
    except subprocess.TimeoutExpired as e:
        raise TimeoutError(f"{main_name} timeout: {e}") from e
    except Exception:
        dps = 0.0

    genome["fitness"] = dps

    return {
        "fitness": dps,
        "seq_map": seq_map,
        "action_lines": action_lines,
        "base_code": base_code,
        "config_path": config_path,
    }


def clone_genome(genome: dict) -> dict:
    return {
        "token_split": list(genome["token_split"]),
        "main_weights": dict(genome["main_weights"]),
        "support_weights": dict(genome["support_weights"]),
        "fitness": genome.get("fitness"),
    }


def evolve_population(
    main_name: str,
    members: list[str],
    gear_map: dict,
    legal_db: dict,
    note_map: dict,
    total_tokens: int,
    create_random_genome,
    crossover_genomes,
    mutate_genome,
    build_party_sequence,
    convert_seq_map_to_action_lines,
    make_base_code,
):
    population = [
        create_random_genome(members, total_tokens)
        for _ in range(POPULATION_SIZE)
    ]

    elite_count = max(2, int(POPULATION_SIZE * ELITE_RATIO))

    best_genome = None
    best_result = None
    best_fitness = float("-inf")

    for generation in range(GENERATIONS):
        evaluated = []

        for genome in population:
            result = evaluate_genome(
                genome=genome,
                main_name=main_name,
                members=members,
                gear_map=gear_map,
                legal_db=legal_db,
                note_map=note_map,
                build_party_sequence=build_party_sequence,
                convert_seq_map_to_action_lines=convert_seq_map_to_action_lines,
                make_base_code=make_base_code,
            )

            evaluated.append((genome, result))

            if result["fitness"] > best_fitness:
                best_fitness = result["fitness"]
                best_genome = clone_genome(genome)
                best_result = result

        evaluated.sort(key=lambda x: x[1]["fitness"], reverse=True)
        elites = [item[0] for item in evaluated[:elite_count]]

        gen_best = evaluated[0][1]["fitness"]
        gen_avg = sum(r["fitness"] for _, r in evaluated) / len(evaluated)

        print(f"[진화] [{main_name}] T={total_tokens} {generation + 1}세대 완료 | 최고={gen_best:.2f} | 평균={gen_avg:.2f}")

        next_population = [clone_genome(e) for e in elites]

        import random
        while len(next_population) < POPULATION_SIZE:
            p1 = random.choice(elites)
            p2 = random.choice(elites)

            child = crossover_genomes(p1, p2, total_tokens)
            mutate_genome(child, total_tokens)
            next_population.append(child)

        population = next_population

    return best_genome, best_result
