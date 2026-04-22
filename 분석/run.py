import os
from rotation_order import save_all_orders

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_CSV = os.path.join(BASE_DIR, "summary_top.csv")


def norm(s: str) -> str:
    return s.strip().lower()


def load_character_gear(lines: list[str]):
    gear_map = {}

    for line in lines:
        char_name, party, weapon, set_name = [x.strip() for x in line.split(",", 3)]
        char_key = norm(char_name)

        gear_map[char_key] = {
            "weapon": norm(weapon),
            "set_name": norm(set_name),
        }

    return gear_map


def make_gcsim(line: str, gear_map: dict):
    main, party, weapon, set_name = [x.strip() for x in line.split(",", 3)]

    members = [norm(m) for m in party.split("/")]
    active = members[0]

    blocks = []

    for idx, m in enumerate(members, start=1):
        if m not in gear_map:
            raise ValueError(f"CSV에 장비 정보 없음: {m}")

        char_weapon = gear_map[m]["weapon"]
        char_set = gear_map[m]["set_name"]

        block = f"""
# =========================
# 캐릭터 {idx} ({m})
# =========================
{m} char lvl=90/90 cons=0 talent=9,9,9;
{m} add weapon="{char_weapon}" refine=1 lvl=90/90;
{m} add set="{char_set}" count=4;
"""
        blocks.append(block)

    base_code = f"""options iteration=1000 duration=10.5 swap_delay=6 workers=4;
options hitlag=true defhalt=false ignore_burst_energy=true;

target lvl=100 resist=0.1 pos=1,0 radius=3 freeze_resist=0;

active {active};
{''.join(blocks)}
"""

    return main, base_code, members


def main():
    if not os.path.exists(INPUT_CSV):
        print("❌ summary_top.csv 없음")
        print(INPUT_CSV)
        return

    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        lines = [line.strip() for line in f.readlines()[1:] if line.strip()]

    gear_map = load_character_gear(lines)

    for line in lines:
        try:
            main_name, base_code, members = make_gcsim(line, gear_map)
            save_all_orders(main_name=main_name, base_code=base_code, party_members=members)
        except Exception as e:
            print(f"❌ 오류: {line}")
            print(e)


if __name__ == "__main__":
    main()