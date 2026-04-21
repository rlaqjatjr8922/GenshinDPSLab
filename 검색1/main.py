from app_context import (
    BASE_DIR,
    DATA_DIR,
    SAVE_DIR,
    characters_data,
    character_alias_map,
    character_names,
    config,
    set_alias_map,
    set_names,
    weapons_data,
    weapon_alias_map,
    weapon_names,
)
from character_pipeline import build_empty_summary_row, process_character
from result_writer import (
    build_summary_row_from_saved_results,
    count_saved_result_files,
    save_summary_to_csv,
    save_top_summary_to_csv,
)


def main():
    characters = characters_data.get("characters", [])
    all_characters = character_names
    all_weapons = weapon_names
    all_sets = set_names
    all_character_aliases = character_alias_map
    all_weapon_aliases = weapon_alias_map
    all_set_aliases = set_alias_map

    if not characters:
        print("[오류] characters.json의 characters가 비어 있습니다.")
        return

    print(f"[기준 폴더] {BASE_DIR}")
    print(f"[데이터 폴더] {DATA_DIR}")
    print(f"[저장 폴더] {SAVE_DIR}")
    print(f"[캐릭터 수] {len(characters)}")

    total_characters = len(characters)
    expected_docs = config.get("max_docs", 10)
    summary_rows = []

    for index, character in enumerate(characters, start=1):
        saved_file_count = count_saved_result_files(character)

        if saved_file_count >= expected_docs:
            print(f"[건너뜀] {character} ({index}/{total_characters}, 파일 {saved_file_count}개)")
            summary_rows.append(
                build_summary_row_from_saved_results(
                    character,
                    all_characters=all_characters,
                    all_weapons=all_weapons,
                    all_sets=all_sets,
                    all_character_aliases=all_character_aliases,
                    all_weapon_aliases=all_weapon_aliases,
                    all_set_aliases=all_set_aliases,
                )
            )
            continue

        try:
            summary_row = process_character(
                character,
                config=config,
                all_characters=all_characters,
                all_character_aliases=all_character_aliases,
                all_weapons=all_weapons,
                all_weapon_aliases=all_weapon_aliases,
                all_sets=all_sets,
                all_set_aliases=all_set_aliases,
                current_index=index,
                total_characters=total_characters,
            )
            summary_rows.append(summary_row)

        except Exception as e:
            print(f"[오류] {character}: {e}")
            summary_row = build_empty_summary_row(character, party=f"오류({e})")
            summary_rows.append(summary_row)

    save_summary_to_csv(summary_rows)
    save_top_summary_to_csv(summary_rows)
    print("\n모든 작업 완료")


if __name__ == "__main__":
    main()
