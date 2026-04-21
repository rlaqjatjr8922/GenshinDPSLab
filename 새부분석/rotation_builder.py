import os
from config import GENERATED_ROTATIONS_DIR
from core.utils import ensure_dir, norm


def save_all_orders(
    main_name: str,
    base_code: str,
    party_members: list[str],
    action_lines: list[str],
) -> str:
    ensure_dir(GENERATED_ROTATIONS_DIR)

    out_path = os.path.join(GENERATED_ROTATIONS_DIR, f"{norm(main_name)}.txt")

    lines = []
    lines.append(base_code.rstrip())
    lines.append("")
    lines.append("# =========================")
    lines.append("# 파티 정보")
    lines.append("# =========================")
    lines.append(f"# main = {norm(main_name)}")
    lines.append(f"# party = {' / '.join(party_members)}")
    lines.append("")
    lines.append("# =========================")
    lines.append("# 생성된 행동 로테이션")
    lines.append("# =========================")

    if action_lines:
        lines.extend(action_lines)
    else:
        lines.append("# action lines 없음")

    full_code = "\n".join(lines).rstrip() + "\n"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(full_code)
    return out_path