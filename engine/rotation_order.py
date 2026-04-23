import json
import itertools
import subprocess
import re

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
        print(f"[오류] gcsim.exe 없음: {GCSIM_EXE}")
        return 0.0

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
        print(f"[오류] gcsim 실행 실패: {path}")
        print("===== stdout =====")
        print(result.stdout)
        print("===== stderr =====")
        print(result.stderr)
        return 0.0

    if not output:
        print(f"[오류] 출력 없음: {path}")
        print("===== stderr =====")
        print(err)
        return 0.0

    dps = extract_dps(output)

    if dps == 0.0:
        print(f"[오류] DPS 추출 실패: {path}")
        print("===== raw output =====")
        print(output[:3000])
        if err:
            print("===== stderr =====")
            print(err[:3000])

    return dps


def load_best_orders():
    if BEST_ORDERS_JSON.exists():
        try:
            with open(BEST_ORDERS_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_best_orders(data):
    BEST_ORDERS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(BEST_ORDERS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_all_orders(main_name: str, base_code: str, party_members: list[str]):
    CONFIGS_DIR.mkdir(parents=True, exist_ok=True)

    char_dir = CONFIGS_DIR / main_name
    char_dir.mkdir(parents=True, exist_ok=True)

    all_orders = list(itertools.permutations(party_members))

    best_dps = -1.0
    best_order = None

    for j, order in enumerate(all_orders, start=1):
        order = list(order)

        rotation_code = make_rotation(order)
        order_comment = " -> ".join(order)

        final_code = (
            base_code
            + "\n# =========================\n# Entry Order\n# =========================\n"
            + f"# {order_comment}\n"
            + "\n# =========================\n# Rotation\n# =========================\n"
            + rotation_code
            + "\n"
        )

        filename = f"{main_name}_{j}.txt"
        path = char_dir / filename

        with open(path, "w", encoding="utf-8") as f:
            f.write(final_code)

        dps = run_gcsim(path)
        print(f"{main_name}_{j} → DPS: {dps}")

        if dps > best_dps:
            best_dps = dps
            best_order = order

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