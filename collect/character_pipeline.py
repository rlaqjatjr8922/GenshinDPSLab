from collect.browser import crawl_genshin_best_party
from collect.result_writer import save_results
from collect.text_analysis import count_occurrences_per_doc, format_counter_all


def build_empty_summary_row(character: str, party: str = "모름") -> dict:
    return {
        "캐릭터": character,
        "파티": party,
        "무기": "모름",
        "성유물 이름": "모름",
    }


def process_character(
    character: str,
    *,
    config: dict,
    all_characters: list[str],
    all_character_aliases: dict[str, str],
    all_weapons: list[str],
    all_weapon_aliases: dict[str, str],
    all_sets: list[str],
    all_set_aliases: dict[str, str],
    current_index: int | None = None,
    total_characters: int | None = None,
    doc_progress_callback=None,
) -> dict:
    if current_index is not None and total_characters is not None:
        print(f"\n===== {character} 시작 ({current_index}/{total_characters}) =====")
    else:
        print(f"\n===== {character} 시작 =====")

    docs = crawl_genshin_best_party(
        name=character,

        # 🔥 기존
        max_workers=config.get("max_workers", 4),
        max_docs=config.get("max_docs", 8),
        min_content_length=config.get("min_content_length", 300),

        # 🔥 추가 (핵심)
        search_result_limit=config.get("search_result_limit", 10),
        ignore_keywords=config.get("ignore_keywords", []),
        block_sites=config.get("block_sites", []),
        search_keywords=config.get("search_keywords", []),
        search_suffixes=config.get("search_suffixes", []),

        progress_callback=doc_progress_callback,
    )

    print(f"[{character}] 수집 개수 = {len(docs)}")

    if not docs:
        print(f"[결과 없음] {character}")
        return build_empty_summary_row(character)

    # 🔥 필요할 때만 저장
    if config.get("save_raw_text", True):
        save_results(character, docs)

    party_counter = count_occurrences_per_doc(docs, all_character_aliases)
    weapon_counter = count_occurrences_per_doc(docs, all_weapon_aliases)
    set_counter = count_occurrences_per_doc(docs, all_set_aliases)

    return {
        "캐릭터": character,
        "파티": format_counter_all(party_counter),
        "무기": format_counter_all(weapon_counter),
        "성유물 이름": format_counter_all(set_counter),
    }