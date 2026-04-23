from collect.app_context import (
    character_alias_map,
    character_names,
    config,
    set_alias_map,
    set_names,
    weapon_alias_map,
    weapon_names,
)
from collect.character_pipeline import (
    build_empty_summary_row,
    process_character,
)
from collect.result_writer import (
    build_summary_row_from_saved_results,
    count_saved_result_files,
)
from collect.save_collect_outputs import (
    append_summary_row,
    upsert_collect_outputs,
)


def run(app_state, progress_callback=None, log_callback=None):
    def log(message: str):
        if log_callback:
            log_callback(message)

    ui = getattr(app_state, "ui", None)
    characters = list((app_state.characters or {}).keys())

    if not characters:
        raise ValueError("data/characters.json의 캐릭터 목록이 비어 있습니다.")

    total_characters = len(characters)
    expected_docs = config.get("max_docs", 10)
    summary_rows = []

    log(f"[collect] 시작 / 캐릭터 수: {total_characters}")

    if ui:
        ui.set_total_progress_text(f"전체 진행도: 0 / {total_characters} 캐릭터 완료")
        ui.set_current_progress_text(f"현재 검색 진행도: 0 / {expected_docs} 문서")

    for index, character in enumerate(characters, start=1):
        completed_count = index - 1
        total_percent = (completed_count / total_characters) * 100.0

        if progress_callback:
            progress_callback(total_percent)

        if ui:
            ui.set_total_progress(total_percent)
            ui.set_total_progress_text(
                f"전체 진행도: {completed_count} / {total_characters} 캐릭터 완료"
            )
            ui.set_current_progress(0)
            ui.set_current_progress_text(
                f"현재 검색 진행도: 0 / {expected_docs} 문서"
            )
            ui.set_status(f"{character} 검색 중")

        saved_file_count = count_saved_result_files(character)

        if saved_file_count >= expected_docs:
            log(
                f"[collect] 건너뜀 {character} "
                f"({index}/{total_characters}, 파일 {saved_file_count}개)"
            )

            if ui:
                ui.set_current_progress(100)
                ui.set_current_progress_text(
                    f"현재 검색 진행도: {expected_docs} / {expected_docs} 문서"
                )

            summary_row = build_summary_row_from_saved_results(
                character,
                all_characters=character_names,
                all_weapons=weapon_names,
                all_sets=set_names,
                all_character_aliases=character_alias_map,
                all_weapon_aliases=weapon_alias_map,
                all_set_aliases=set_alias_map,
            )

        else:
            try:
                log(f"[collect] 처리 중: {character} ({index}/{total_characters})")

                def on_doc_progress(done_docs: int, max_docs: int):
                    if ui:
                        percent = (done_docs / max_docs) * 100.0 if max_docs else 0.0
                        ui.set_current_progress(percent)
                        ui.set_current_progress_text(
                            f"현재 검색 진행도: {done_docs} / {max_docs} 문서"
                        )

                summary_row = process_character(
                    character,
                    config=config,
                    all_characters=character_names,
                    all_character_aliases=character_alias_map,
                    all_weapons=weapon_names,
                    all_weapon_aliases=weapon_alias_map,
                    all_sets=set_names,
                    all_set_aliases=set_alias_map,
                    current_index=index,
                    total_characters=total_characters,
                    doc_progress_callback=on_doc_progress,
                )

            except Exception as e:
                log(f"[collect][오류] {character}: {e}")
                summary_row = build_empty_summary_row(character, party=f"오류({e})")

            if ui:
                ui.set_current_progress(100)
                ui.set_current_progress_text(
                    f"현재 검색 진행도: {expected_docs} / {expected_docs} 문서"
                )

        summary_rows.append(summary_row)

        # 여기서 캐릭터 하나 끝날 때마다 바로 저장
        try:
            append_summary_row(summary_row)
            upsert_collect_outputs(app_state, summary_row, log_callback=log)
        except Exception as e:
            log(f"[collect][저장 오류] {character}: {e}")

    result = {
        "status": "done",
        "summary_rows": summary_rows,
        "character_count": total_characters,
    }

    app_state.stage1 = result

    if ui:
        ui.set_total_progress(100)
        ui.set_current_progress(100)
        ui.set_total_progress_text(
            f"전체 진행도: {total_characters} / {total_characters} 캐릭터 완료"
        )
        ui.set_current_progress_text(
            f"현재 검색 진행도: {expected_docs} / {expected_docs} 문서"
        )

    log("[collect] 완료")
    return result