from concurrent.futures import ThreadPoolExecutor, as_completed

from collect.app_context import build_collect_context
from collect.character_pipeline import (
    build_empty_summary_row,
    process_character,
)
from collect.save_collect_outputs import (
    append_summary_row,
    upsert_collect_outputs,
)


def norm_key(s: str) -> str:
    return str(s).strip().lower().replace(" ", "")


def run(app_state, progress_callback=None, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    def update_total_progress(done_count):
        percent = (done_count / total) * 100 if total else 0

        if controller:
            controller.set_stage1_progress(
                total_done=done_count,
                total_files=total,
                collect_done=0,
                collect_total=1,
            )
        elif progress_callback:
            progress_callback(percent)

    ui = getattr(app_state, "ui", None)
    controller = getattr(ui, "controller", None)

    characters = list((app_state.characters or {}).keys())

    if not characters:
        raise ValueError("characters.json 비어있음")

    ctx = build_collect_context(app_state)

    total = len(characters)
    max_workers = ctx["config"].get("max_workers", 4)

    summary_rows = []
    done = 0

    log(f"[collect] 시작 / 전체: {total}")
    log(f"[collect] MAX_WORKERS={max_workers}")
    log("[collect] 표시: 전체 진행도만")

    existing = set()

    for character in characters:
        key = norm_key(character)
        if key in (app_state.teams or {}) and key in (app_state.gear or {}):
            existing.add(character)

    remaining = [character for character in characters if character not in existing]

    done = len(existing)

    log(f"[skip] {len(existing)}개 이미 존재")
    log(f"[collect] 실행 대상: {len(remaining)}개")

    update_total_progress(done)

    if ui:
        ui.set_status(f"수집 중: {done}/{total}")

    def worker(character):
        try:
            result = process_character(
                character,
                config=ctx["config"],
                all_characters=ctx["character_names"],
                all_character_aliases=ctx["character_alias_map"],
                all_weapons=ctx["weapon_names"],
                all_weapon_aliases=ctx["weapon_alias_map"],
                all_sets=ctx["set_names"],
                all_set_aliases=ctx["set_alias_map"],
                current_index=None,
                total_characters=None,
                doc_progress_callback=None,
            )

            return character, result, None

        except Exception as e:
            return character, None, str(e)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, character) for character in remaining]

        for future in as_completed(futures):
            character, result, error = future.result()
            done += 1

            if error:
                log(f"[실패] {character}: {error}")
                summary_row = build_empty_summary_row(character, party="오류")
            else:
                log(f"[완료] {character}")
                summary_row = result
                upsert_collect_outputs(app_state, summary_row, log_callback=log)

            summary_rows.append(summary_row)
            append_summary_row(summary_row)

            update_total_progress(done)

            if ui:
                ui.set_status("")

    result = {
        "status": "done",
        "summary_rows": summary_rows,
        "count": total,
        "skipped_count": len(existing),
        "processed_count": len(remaining),
        "max_workers": max_workers,
    }

    app_state.stage1 = result

    update_total_progress(total)

    if ui:
        ui.set_status("1단계 수집 완료")

    log("[collect] 완료")
    return result