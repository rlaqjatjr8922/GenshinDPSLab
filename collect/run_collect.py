from collect.app_context import build_collect_context
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

    # 🔥 핵심 변경: app_state에서 직접 가져옴
    characters = list((app_state.characters or {}).keys())

    if not characters:
        raise ValueError("characters.json 비어있음")

    # 🔥 context 생성 (파일 읽기 없음)
    ctx = build_collect_context(app_state)

    total_characters = len(characters)
    expected_docs = ctx["config"].get("max_docs", 10)

    summary_rows = []

    log(f"[collect] 시작 / 캐릭터 수: {total_characters}")

    if ui:
        ui.set_total_progress_text(f"전체 진행도: 0 / {total_characters}")
        ui.set_current_progress_text(f"문서: 0 / {expected_docs}")

    for index, character in enumerate(characters, start=1):
        completed = index - 1
        percent = (completed / total_characters) * 100

        if progress_callback:
            progress_callback(percent)

        if ui:
            ui.set_total_progress(percent)
            ui.set_total_progress_text(f"{completed}/{total_characters}")
            ui.set_current_progress(0)
            ui.set_status(f"{character} 수집 중")

        saved_count = count_saved_result_files(character)

        # ✅ 이미 있으면 재사용
        if saved_count >= expected_docs:
            log(f"[skip] {character}")

            summary_row = build_summary_row_from_saved_results(
                character,
                all_characters=ctx["character_names"],
                all_weapons=ctx["weapon_names"],
                all_sets=ctx["set_names"],
                all_character_aliases=ctx["character_alias_map"],
                all_weapon_aliases=ctx["weapon_alias_map"],
                all_set_aliases=ctx["set_alias_map"],
            )

        else:
            try:
                log(f"[collect] {character}")

                def on_doc_progress(done, total):
                    if ui:
                        ui.set_current_progress((done / total) * 100)

                summary_row = process_character(
                    character,
                    config=ctx["config"],
                    all_characters=ctx["character_names"],
                    all_character_aliases=ctx["character_alias_map"],
                    all_weapons=ctx["weapon_names"],
                    all_weapon_aliases=ctx["weapon_alias_map"],
                    all_sets=ctx["set_names"],
                    all_set_aliases=ctx["set_alias_map"],
                    current_index=index,
                    total_characters=total_characters,
                    doc_progress_callback=on_doc_progress,
                )

            except Exception as e:
                log(f"[오류] {character}: {e}")
                summary_row = build_empty_summary_row(character, party="오류")

        summary_rows.append(summary_row)

        # 🔥 핵심: app_state 기반 저장
        append_summary_row(summary_row)
        upsert_collect_outputs(app_state, summary_row, log_callback=log)

    result = {
        "status": "done",
        "summary_rows": summary_rows,
        "count": total_characters,
    }

    # ⚠️ stage 필드는 그냥 동적 추가
    app_state.stage1 = result

    if ui:
        ui.set_total_progress(100)
        ui.set_current_progress(100)

    log("[collect] 완료")

    return result