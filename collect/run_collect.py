from collect.app_context import build_collect_context
from collect.character_pipeline import (
    build_empty_summary_row,
    process_character,
)
from collect.result_writer import (
    build_summary_row_from_saved_results,
)
from collect.save_collect_outputs import (
    append_summary_row,
    upsert_collect_outputs,
)


def norm_key(s: str) -> str:
    return str(s).strip().lower().replace(" ", "")


def run(app_state, progress_callback=None, log_callback=None):
    def log(message: str):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    ui = getattr(app_state, "ui", None)
    controller = getattr(ui, "controller", None)

    characters = list((app_state.characters or {}).keys())

    if not characters:
        raise ValueError("characters.json 비어있음")

    ctx = build_collect_context(app_state)

    total_files = len(characters)
    collect_total = ctx["config"].get("max_docs", 10)

    summary_rows = []

    log(f"[collect] 시작 / 전체 파일 수: {total_files}")
    log("[collect] 이어서하기 기준: teams.json + gear.json")

    if controller:
        controller.set_stage1_progress(
            total_done=0,
            total_files=total_files,
            collect_done=0,
            collect_total=collect_total,
        )
    elif progress_callback:
        progress_callback(0)

    for index, character in enumerate(characters, start=1):
        total_done = index - 1
        char_key = norm_key(character)

        already_done = (
            char_key in (app_state.teams or {})
            and char_key in (app_state.gear or {})
        )

        if controller:
            controller.set_stage1_progress(
                total_done=total_done,
                total_files=total_files,
                collect_done=0,
                collect_total=collect_total,
            )
        elif progress_callback:
            progress_callback((total_done / total_files) * 100)

        if ui:
            ui.set_status(f"{character} 확인 중")

        if already_done:
            log(f"[skip/json] {character} 이미 저장됨")

            if controller:
                controller.set_stage1_progress(
                    total_done=total_done,
                    total_files=total_files,
                    collect_done=collect_total,
                    collect_total=collect_total,
                )

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

                if ui:
                    ui.set_status(f"{character} 수집 중")

                def on_doc_progress(done, total):
                    if controller:
                        controller.set_stage1_progress(
                            total_done=total_done,
                            total_files=total_files,
                            collect_done=done,
                            collect_total=total,
                        )
                    elif progress_callback:
                        progress_callback((total_done / total_files) * 100)

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
                    total_characters=total_files,
                    doc_progress_callback=on_doc_progress,
                )

            except Exception as e:
                log(f"[오류] {character}: {e}")
                summary_row = build_empty_summary_row(character, party="오류")

        summary_rows.append(summary_row)

        append_summary_row(summary_row)
        upsert_collect_outputs(app_state, summary_row, log_callback=log)

        if controller:
            controller.set_stage1_progress(
                total_done=index,
                total_files=total_files,
                collect_done=collect_total,
                collect_total=collect_total,
            )
        elif progress_callback:
            progress_callback((index / total_files) * 100)

    result = {
        "status": "done",
        "summary_rows": summary_rows,
        "count": total_files,
    }

    app_state.stage1 = result

    if controller:
        controller.set_stage1_progress(
            total_done=total_files,
            total_files=total_files,
            collect_done=collect_total,
            collect_total=collect_total,
        )
    elif progress_callback:
        progress_callback(100)

    log("[collect] 완료")

    return result