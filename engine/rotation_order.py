import json
import itertools
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from config.config import CONFIGS_DIR, BEST_ORDERS_JSON, GCSIM_EXE


def make_rotation(order):
    lines = []
    for m in order:
        lines.append(f"{m} skill;")
        lines.append(f"{m} burst;")
        lines.append(f"{m} attack;")
    return "\n".join(lines)


def extract_dps(text):
    try:
        data = json.loads(text)
        return float(data["statistics"]["dps"]["mean"])
    except Exception:
        patterns = [
            r'"mean"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
            r'"dps"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
            r'DPS\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)',
            r'resulting in\s*([0-9]+(?:\.[0-9]+)?)\s*dps',
        ]

        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return float(m.group(1))

    return 0.0


def run_gcsim(path):
    if not GCSIM_EXE.exists():
        raise FileNotFoundError(f"gcsim.exe 없음: {GCSIM_EXE}")

    result = subprocess.run(
        [str(GCSIM_EXE), "-c", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    output = (result.stdout or "").strip()
    err = (result.stderr or "").strip()

    if result.returncode != 0:
        raise RuntimeError(f"gcsim 실행 실패:\n{err}")

    dps = extract_dps(output)

    if dps <= 0.0:
        raise RuntimeError("DPS 추출 실패")

    return dps


def load_best_orders():
    if BEST_ORDERS_JSON.exists():
        try:
            with open(BEST_ORDERS_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_best_orders(data):
    BEST_ORDERS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(BEST_ORDERS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_all_orders(
    main_name: str,
    base_code: str,
    party_members: list[str],
    progress_callback=None,
    max_workers: int = 1,
):
    CONFIGS_DIR.mkdir(parents=True, exist_ok=True)

    char_dir = CONFIGS_DIR / main_name
    char_dir.mkdir(parents=True, exist_ok=True)

    all_orders = list(itertools.permutations(party_members))
    total_orders = len(all_orders)

    best_dps = -1.0
    best_order = None
    done = 0

    # =========================================
    # 1. 시작할 때 한 번만 검사
    # =========================================
    existing = set()

    for j in range(1, total_orders + 1):
        path = char_dir / f"{main_name}_{j}.txt"
        if path.exists():
            existing.add(j)

    # =========================================
    # 2. 남은 작업만 분리
    # =========================================
    remaining = [
        (j, list(order))
        for j, order in enumerate(all_orders, start=1)
        if j not in existing
    ]

    # =========================================
    # 3. 기존 것은 진행률만 처리 (실행 X)
    # =========================================
    done += len(existing)

    if progress_callback:
        progress_callback(done, total_orders)

    # =========================================
    # 4. 병렬 실행
    # =========================================
    def worker(j, order):
        path = char_dir / f"{main_name}_{j}.txt"

        if not path.exists():
            rotation_code = make_rotation(order)

            final_code = (
                base_code
                + "\n# Entry Order\n"
                + f"# {' -> '.join(order)}\n"
                + rotation_code
            )

            with open(path, "w", encoding="utf-8") as f:
                f.write(final_code)

        dps = run_gcsim(path)
        return j, order, dps

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, j, order) for j, order in remaining]

        for future in as_completed(futures):
            j, order, dps = future.result()
            done += 1

            print(f"{main_name}_{j} → DPS: {dps}")

            if dps > best_dps:
                best_dps = dps
                best_order = order

            if progress_callback:
                progress_callback(done, total_orders)

    # =========================================
    # 5. 결과 저장
    # =========================================
    if best_order is None:
        raise RuntimeError(f"{main_name} 최고 DPS 없음")

    best_orders = load_best_orders()
    best_orders[main_name] = best_order
    save_best_orders(best_orders)

    print(f"🔥 {main_name} 최고 DPS: {best_dps}")
    print(f"🔥 최고 순서: {best_order}")

    return {
        "main_name": main_name,
        "best_dps": best_dps,
        "best_order": best_order,
    }