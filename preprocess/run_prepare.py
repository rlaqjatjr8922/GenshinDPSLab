from preprocess.legal_actions_builder import build_legal_actions


def run(app_state, progress_callback=None, log_callback=None):
    def log(message: str):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    def set_progress(value: float):
        if progress_callback:
            progress_callback(value)

    log("[prepare] 2단계 시작")
    set_progress(0)

    try:
        characters = getattr(app_state, "characters", None)
        if not isinstance(characters, dict) or not characters:
            raise ValueError("app_state.characters 비어있음")

        result = build_legal_actions(
            app_state=app_state,
            progress_callback=progress_callback,
            log_callback=log_callback,
        )

        app_state.stage2 = {
            "status": "done",
            "success_count": result.get("success_count", 0),
            "failed_count": result.get("failed_count", 0),
            "json_path": str(result.get("json_path", "")),
            "csv_path": str(result.get("csv_path", "")),
        }

        set_progress(100)
        log("[prepare] 2단계 완료")
        return app_state.stage2

    except Exception as e:
        log(f"[prepare][오류] {e}")
        app_state.stage2 = {
            "status": "error",
            "error": str(e),
        }
        return app_state.stage2