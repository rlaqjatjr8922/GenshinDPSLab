import json
from config.config import LEGAL_ACTIONS_JSON, OUTPUT_DIR


def run():
    with open(LEGAL_ACTIONS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    notes_set = set()

    for char, actions in data.items():
        for action, info in actions.items():
            note = info.get("notes", "").strip()

            if note and note != "-":
                notes_set.add(note)

    # 정렬 (가독성 좋게)
    notes_list = sorted(notes_set)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "unique_notes.txt"

    with open(out_path, "w", encoding="utf-8") as f:
        for note in notes_list:
            f.write(note + "\n")

    print(f"[완료] notes 추출: {out_path}")
    print(f"총 {len(notes_list)}개")


if __name__ == "__main__":
    run()