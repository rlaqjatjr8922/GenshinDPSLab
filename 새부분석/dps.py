import sys
import json
import os
import tempfile

from config import GEAR_JSON
from core.utils import load_json

from gcsim.builder import convert_seq_map_to_action_lines, make_base_code
from gcsim.runner import run_gcsim, extract_dps


def main():
    # GA에서 넘어온 individual
    individual = json.loads(sys.argv[1])

    # 파티 구성 (순서 유지 중요)
    members = list(individual.keys())

    # gear 로드
    gear_map = load_json(GEAR_JSON)

    # seq_map = individual 그대로 사용
    seq_map = individual

    # gcsim 코드 생성
    base_code = make_base_code(
        main_name=members[0],
        members=members,
        gear_map=gear_map,
    )

    action_lines = convert_seq_map_to_action_lines(
        seq_map=seq_map,
        members=members,
    )

    full_code = base_code + "\n" + "\n".join(action_lines)

    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as f:
        f.write(full_code)
        config_path = f.name

    try:
        output = run_gcsim(config_path)
        dps = extract_dps(output)
        print(dps)

    except Exception as e:
        # 실패하면 낮은 점수 반환
        print(0.0)

    finally:
        if os.path.exists(config_path):
            os.remove(config_path)


if __name__ == "__main__":
    main()