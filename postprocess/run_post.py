def run(app_state, progress_callback=None, log_callback=None):
    def log(msg: str):
        if log_callback:
            log_callback(msg)

    def set_progress(v: float):
        if progress_callback:
            progress_callback(v)

    log("[postprocess] 시작")
    set_progress(0)

    legal_actions = app_state.gcsim_legal_actions_all
    best_orders = app_state.best_orders
    gear = app_state.gear
    legal_parser = app_state.gcsim_legal_actions_parser

    if not legal_actions:
        raise ValueError("gcsim_legal_actions_all 없음")

    if not best_orders:
        raise ValueError("best_orders 없음")

    if not gear:
        raise ValueError("gear 없음")

    if not legal_parser:
        raise ValueError("gcsim_legal_actions_parser 없음")

    set_progress(30)

    log(f"[postprocess] legal_actions: {len(legal_actions)}개")
    log(f"[postprocess] best_orders: {len(best_orders)}개")
    log(f"[postprocess] gear: {len(gear)}개")
    log(f"[postprocess] legal_parser: {len(legal_parser)}개")

    set_progress(70)

    result = {
        "status": "done",
        "legal_actions_count": len(legal_actions),
        "best_orders_count": len(best_orders),
        "gear_count": len(gear),
        "legal_parser_count": len(legal_parser),
    }

    app_state.stage4 = result

    set_progress(100)

    log("[postprocess] 완료")

    return result