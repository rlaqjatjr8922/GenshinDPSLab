import os
import subprocess
from multiprocessing import Pool
import time
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GCSIM_PATH = os.path.join(BASE_DIR, "gcsim.exe")

def extract_dps(text):
    m = re.search(r"resulting in\s+([\d.]+)\s+dps", text, re.IGNORECASE)
    if not m:
        return 0.0
    return float(m.group(1))

def run(cfg_name):
    cfg_path = os.path.join(BASE_DIR, cfg_name)

    start = time.time()
    result = subprocess.run(
        [GCSIM_PATH, "-c", cfg_path],
        capture_output=True,
        text=True
    )
    end = time.time()

    dps = extract_dps(result.stdout) if result.returncode == 0 else 0.0

    return {
        "config": cfg_name,
        "time": round(end - start, 2),
        "returncode": result.returncode,
        "dps": dps,
        "stdout": result.stdout[:300],
        "stderr": result.stderr[:300],
    }

if __name__ == "__main__":
    configs = ["config1.txt", "config2.txt", "config3.txt", "config4.txt"]

    total_start = time.time()

    with Pool(4) as p:
        results = p.map(run, configs)

    total_end = time.time()

    print("총 시간:", round(total_end - total_start, 2), "초")
    print()

    for r in results:
        print("=" * 60)
        print("config:", r["config"])
        print("time:", r["time"])
        print("returncode:", r["returncode"])
        print("dps:", r["dps"])
        print("stderr:", r["stderr"])