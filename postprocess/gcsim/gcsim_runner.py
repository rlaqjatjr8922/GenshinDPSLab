import os
import time

from gcsim.builder import make_base_code, convert_seq_map_to_action_lines
from gcsim.runner import run_gcsim, extract_dps


def run_dps(individual, output_dir, load_gear_func):
    config_path = None

    try:
        members = list(individual.keys())
        gear_map = load_gear_func()

        base_code = make_base_code(
            main_name=members[0],
            members=members,
            gear_map=gear_map,
        )

        action_lines = convert_seq_map_to_action_lines(
            seq_map=individual,
            members=members,
        )

        ts = time.time_ns()
        pid = os.getpid()
        config_path = os.path.join(output_dir, f"temp_{ts}_{pid}.txt")

        with open(config_path, "w", encoding="utf-8") as f:
            f.write(base_code)
            f.write("\n")
            f.write("\n".join(action_lines))

        output = run_gcsim(config_path)
        dps = extract_dps(output)
        return dps

    finally:
        if config_path and os.path.exists(config_path):
            os.remove(config_path)