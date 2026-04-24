import os
import re
import subprocess
from config import GCSIM_EXE


def run_gcsim(config_path: str) -> str:
    if not os.path.exists(GCSIM_EXE):
        raise FileNotFoundError(f"gcsim.exe 없음: {GCSIM_EXE}")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"config 없음: {config_path}")

    result = subprocess.run(
        [GCSIM_EXE, "-c", config_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
    )

    return (result.stdout or "") + "\n" + (result.stderr or "")


def extract_dps(output: str) -> float:
    patterns = [
        r"resulting in\s+([0-9]+(?:\.[0-9]+)?)\s*dps",
        r"([0-9]+(?:\.[0-9]+)?)\s*dps",
    ]

    for p in patterns:
        m = re.search(p, output, re.IGNORECASE)
        if m:
            return float(m.group(1))

    raise ValueError("DPS 추출 실패")