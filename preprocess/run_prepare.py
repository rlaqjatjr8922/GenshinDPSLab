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

    try:
        characters = getattr(app_state, "characters", None)
        if not isinstance(characters, dict) or not characters:
            raise ValueError("app_state.characters 비어있음")

        total_files = len(characters)

        if controller:
            controller.set_stage2_progress(0, total_files)
        elif progress_callback:
            progress_callback(0)

        def stage2_progress(done, total=None):
            total = total or total_files

            if controller:
                controller.set_stage2_progress(done, total)
            elif progress_callback:
                progress_callback((done / total) * 100 if total else 0)

        result = build_legal_actions(
            app_state=app_state,
            progress_callback=stage2_progress,
            log_callback=log_callback,
        )

        success_count = result.get("success_count", 0)
        failed_count = result.get("failed_count", 0)
        done_count = success_count + failed_count

        if controller:
            controller.set_stage2_progress(done_count, total_files)
        elif progress_callback:
            progress_callback(100)

        app_state.stage2 = {
            "status": "done",
            "success_count": success_count,
            "failed_count": failed_count,
            "json_path": str(result.get("json_path", "")),
            "csv_path": str(result.get("csv_path", "")),
        }

        log("[prepare] 2단계 완료")
        return app_state.stage2

    except Exception as e:
        log(f"[prepare][오류] {e}")
        app_state.stage2 = {
            "status": "error",
            "error": str(e),
        }
        return app_state.stage2