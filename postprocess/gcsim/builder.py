def build_character_blocks(members: list[str], gear_map: dict) -> str:
    blocks = []

    for idx, char in enumerate(members, start=1):
        if char not in gear_map:
            raise ValueError(f"gear.json에 장비 정보 없음: {char}")

        weapon = gear_map[char]["weapon"]
        set_name = gear_map[char]["set_name"]

        block = f"""
# =========================
# 캐릭터 {idx} ({char})
# =========================
{char} char lvl=90/90 cons=0 talent=9,9,9;
{char} add weapon="{weapon}" refine=1 lvl=90/90;
{char} add set="{set_name}" count=4;
"""
        blocks.append(block)

    return "".join(blocks)


def convert_seq_map_to_action_lines(seq_map: dict, members: list[str]) -> list[str]:
    lines = []

    for char in members:
        actions = seq_map.get(char, [])
        if not actions:
            continue

        action_str = ", ".join(actions)
        lines.append(f"{char} {action_str};")

    return lines


def make_base_code(main_name: str, members: list[str], gear_map: dict) -> str:
    active = members[0]
    char_blocks = build_character_blocks(members, gear_map)

    base_code = f"""options iteration=100 swap_delay=6;
options hitlag=true defhalt=false ignore_burst_energy=false;
energy every interval=600,601 amount=1;
target lvl=100 resist=0.1 pos=1,0 radius=3 freeze_resist=0 hp=1000000000;

active {active};
{char_blocks}"""

    return base_code