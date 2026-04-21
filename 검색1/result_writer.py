import csv
from pathlib import Path

from app_context import SAVE_DIR, config
from text_analysis import count_occurrences_per_doc, format_counter_all


def clean_filename(name: str, max_length: int = 40) -> str:
    invalid_chars = r'\/:*?"<>|'

    for ch in invalid_chars:
        name = name.replace(ch, "_")

    name = name.strip()

    if len(name) > max_length:
        name = name[:max_length]

    if not name:
        name = "untitled"

    return name


def get_unique_file_path(folder: Path, filename: str) -> Path:
    file_path = folder / filename

    if not file_path.exists():
        return file_path

    stem = file_path.stem
    suffix = file_path.suffix
    count = 1

    while True:
        new_path = folder / f"{stem}_{count}{suffix}"
        if not new_path.exists():
            return new_path
        count += 1


def save_results(character: str, docs: list[dict]):
    char_dir = SAVE_DIR / character
    char_dir.mkdir(parents=True, exist_ok=True)

    print(f"[저장 시작] {char_dir} / {len(docs)}개")

    for doc in docs:
        title = (doc.get("title") or "untitled").strip()
        content = (doc.get("content") or "").strip()

        if not content:
            content = (doc.get("snippet") or "내용없음").strip()

        filename = clean_filename(
            title,
            max_length=config.get("max_filename_length", 40),
        ) + ".txt"

        file_path = get_unique_file_path(char_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[저장 완료] {file_path}")


def count_saved_result_files(character: str) -> int:
    char_dir = SAVE_DIR / character

    if not char_dir.exists():
        return 0

    return sum(1 for path in char_dir.iterdir() if path.is_file() and path.suffix == ".txt")


def load_saved_results(character: str) -> list[dict]:
    char_dir = SAVE_DIR / character

    if not char_dir.exists():
        return []

    docs = []

    for path in sorted(char_dir.glob("*.txt")):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        docs.append(
            {
                "title": path.stem,
                "snippet": "",
                "content": content,
            }
        )

    return docs


def build_summary_row_from_saved_results(
    character: str,
    *,
    all_characters: list[str],
    all_character_aliases: dict[str, str],
    all_weapons: list[str],
    all_weapon_aliases: dict[str, str],
    all_sets: list[str],
    all_set_aliases: dict[str, str],
) -> dict:
    docs = load_saved_results(character)

    if not docs:
        return {
            "캐릭터": character,
            "파티": "모름",
            "무기": "모름",
            "성유물 이름": "모름",
        }

    party_counter = count_occurrences_per_doc(docs, all_character_aliases)
    weapon_counter = count_occurrences_per_doc(docs, all_weapon_aliases)
    set_counter = count_occurrences_per_doc(docs, all_set_aliases)

    return {
        "캐릭터": character,
        "파티": format_counter_all(party_counter),
        "무기": format_counter_all(weapon_counter),
        "성유물 이름": format_counter_all(set_counter),
    }


def _extract_top_names(value: str, limit: int) -> str:
    if not value or value == "모름":
        return "모름"

    items = []

    for part in value.split(" / "):
        name = part.rsplit("(", 1)[0].strip()
        if name:
            items.append(name)
        if len(items) >= limit:
            break

    return " / ".join(items) if items else "모름"


def build_top_summary_rows(summary_rows: list[dict]) -> list[dict]:
    top_rows = []

    for row in summary_rows:
        top_rows.append(
            {
                "캐릭터": row.get("캐릭터", "모름"),
                "파티상위 4명": _extract_top_names(row.get("파티", ""), 4),
                "무기상위 1개": _extract_top_names(row.get("무기", ""), 1),
                "성유물 이름상위 1개": _extract_top_names(row.get("성유물 이름", ""), 1),
            }
        )

    return top_rows


def save_summary_to_csv(summary_rows: list[dict], filename: str = "summary.csv"):
    if not summary_rows:
        print("[CSV 저장 건너뜀] 요약 데이터가 없습니다.")
        return

    csv_path = SAVE_DIR / filename

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as csvfile:
        fieldnames = ["캐릭터", "파티", "무기", "성유물 이름"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"[CSV 저장 완료] {csv_path}")


def save_top_summary_to_csv(summary_rows: list[dict], filename: str = "summary_top.csv"):
    if not summary_rows:
        print("[CSV 저장 건너뜀] 요약 데이터가 없습니다.")
        return

    top_rows = build_top_summary_rows(summary_rows)
    csv_path = SAVE_DIR / filename

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as csvfile:
        fieldnames = ["캐릭터", "파티상위 4명", "무기상위 1개", "성유물 이름상위 1개"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(top_rows)

    print(f"[CSV 저장 완료] {csv_path}")
