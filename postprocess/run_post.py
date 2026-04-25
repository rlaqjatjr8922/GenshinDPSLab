from postprocess.rotation_builder import run as run_rotation_builder


def run(app_state, progress_callback=None, log_callback=None):
    def log(msg: str):
        if log_callback:
            log_callback(msg)

    log("[postprocess] 시작")

    ui = getattr(app_state, "ui", None)
    controller = getattr(ui, "controller", None)

    # =========================
    # 필수 데이터 체크
    # =========================
    if not app_state.gcsim_legal_actions_all:
        raise ValueError("gcsim_legal_actions_all 없음")

    if not app_state.best_orders:
        raise ValueError("best_orders 없음")

    if not app_state.gear:
        raise ValueError("gear 없음")

    if not app_state.gcsim_legal_actions_parser:
        raise ValueError("gcsim_legal_actions_parser 없음")

    # =========================
    # 초기 진행 상태
    # =========================
    total_files = len(app_state.best_orders)

    if controller:
        controller.set_stage4_progress(
            file_done=0,
            file_total=total_files,
            t_now=0,
            t_total=0,
            gen_now=0,
            gen_total=0,
        )
    elif progress_callback:
        progress_callback(0)

    # =========================
    # 내부 콜백 (rotation_builder → UI 연결)
    # =========================
    def stage4_progress(file_done, file_total, t_now, t_total, gen_now, gen_total):
        if controller:
            controller.set_stage4_progress(
                file_done=file_done,
                file_total=file_total,
                t_now=t_now,
                t_total=t_total,
                gen_now=gen_now,
                gen_total=gen_total,
            )
        elif progress_callback:
            # fallback (퍼센트만)
            if file_total > 0:
                progress_callback((file_done / file_total) * 100)

    # =========================
    # 실행
    # =========================
    result = run_rotation_builder(
        app_state,
        progress_callback=stage4_progress,
        log_callback=log_callback,
    )

    app_state.stage4 = result

    # =========================
    # 완료 상태
    # =========================
    if controller:
        controller.set_stage4_progress(
            file_done=total_files,
            file_total=total_files,
            t_now=1,
            t_total=1,
            gen_now=1,
            gen_total=1,
        )
    elif progress_callback:
        progress_callback(100)

    log("[postprocess] 완료")
    return result