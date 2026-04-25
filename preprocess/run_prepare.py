from config.config import PREPROCESS_SETTINGS
from preprocess.legal_actions_builder import build_legal_actions


def run(app_state, progress_callback=None, log_callback=None):
    def log(message: str):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    log("[prepare] 2단계 시작")

    ui = getattr(app_state, "ui", None)
    controller = getattr(ui, "controller", None)

    def update_total_progress(done, total):
        percent = (done / total) * 100 if total else 0

        if controller:
            controller.set_stage2_progress(done, total)
        elif progress_callback:
            progress_callback(percent)

    try:
        characters = getattr(app_state, "characters", None)
        if not isinstance(characters, dict) or not characters:
            raise ValueError("characters 없음")

        total = len(characters)
        max_workers = PREPROCESS_SETTINGS.get("MAX_WORKERS", 4)

        log(f"[prepare] MAX_WORKERS={max_workers}")
        log("[prepare] 표시: 전체 진행도만")

        update_total_progress(0, total)

        result = build_legal_actions(
            app_state=app_state,
            max_workers=max_workers,
            progress_callback=update_total_progress,
            log_callback=log,
        )

        done_count = result.get("success_count", 0) + result.get("failed_count", 0)

        update_total_progress(done_count, total)

        app_state.stage2 = {
            "status": "done",
            "success_count": result.get("success_count", 0),
            "failed_count": result.get("failed_count", 0),
            "json_path": str(result.get("json_path", "")),
            "csv_path": str(result.get("csv_path", "")),
            "max_workers": max_workers,
        }

        if ui:
            ui.set_status("2단계 완료")

        log("[prepare] 완료")
        return app_state.stage2

    except Exception as e:
        log(f"[prepare][오류] {e}")

        app_state.stage2 = {
            "status": "error",
            "error": str(e),
        }

        return app_state.stage2