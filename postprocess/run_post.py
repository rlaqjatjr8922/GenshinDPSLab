from postprocess.rotation_builder import run as run_rotation_builder


def run(app_state, progress_callback=None, log_callback=None):
    def log(msg: str):
        if log_callback:
            log_callback(msg)

    def set_progress(v: float):
        if progress_callback:
            progress_callback(v)

    log("[postprocess] 시작")
    set_progress(0)

    if not app_state.gcsim_legal_actions_all:
        raise ValueError("gcsim_legal_actions_all 없음")

    if not app_state.best_orders:
        raise ValueError("best_orders 없음")

    if not app_state.gear:
        raise ValueError("gear 없음")

    if not app_state.gcsim_legal_actions_parser:
        raise ValueError("gcsim_legal_actions_parser 없음")

    set_progress(5)

    result = run_rotation_builder(
        app_state,
        progress_callback=progress_callback,
        log_callback=log_callback,
    )

    app_state.stage4 = result

    set_progress(100)
    log("[postprocess] 완료")

    return result