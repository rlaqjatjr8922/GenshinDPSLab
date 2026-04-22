from tkinter import ttk


def create_progress_panel(
    parent,
    total_progress_var,
    current_progress_var,
    total_progress_text_var,
    current_progress_text_var,
    status_var,
    start_full_run_callback,
    request_stop_callback,
    reset_progress_callback,
    reload_data_callback,
):
    container = ttk.Frame(parent, padding=8)
    container.columnconfigure(0, weight=1)

    progress_box = ttk.LabelFrame(container, text="진행도", padding=10)
    progress_box.grid(row=0, column=0, sticky="ew")
    progress_box.columnconfigure(0, weight=1)

    ttk.Label(progress_box, textvariable=total_progress_text_var).grid(
        row=0, column=0, sticky="w", pady=(0, 4)
    )
    total_bar = ttk.Progressbar(
        progress_box,
        maximum=100,
        variable=total_progress_var,
    )
    total_bar.grid(row=1, column=0, sticky="ew", pady=(0, 12))

    ttk.Label(progress_box, textvariable=current_progress_text_var).grid(
        row=2, column=0, sticky="w", pady=(0, 4)
    )
    current_bar = ttk.Progressbar(
        progress_box,
        maximum=100,
        variable=current_progress_var,
    )
    current_bar.grid(row=3, column=0, sticky="ew", pady=(0, 12))

    ttk.Label(progress_box, textvariable=status_var).grid(
        row=4, column=0, sticky="w"
    )

    control_box = ttk.LabelFrame(container, text="실행 제어", padding=10)
    control_box.grid(row=1, column=0, sticky="ew", pady=(10, 0))
    control_box.columnconfigure((0, 1, 2, 3), weight=1)

    ttk.Button(control_box, text="전체 실행", command=start_full_run_callback).grid(
        row=0, column=0, sticky="ew", padx=(0, 4)
    )
    ttk.Button(control_box, text="중지", command=request_stop_callback).grid(
        row=0, column=1, sticky="ew", padx=4
    )
    ttk.Button(control_box, text="초기화", command=reset_progress_callback).grid(
        row=0, column=2, sticky="ew", padx=4
    )
    ttk.Button(control_box, text="자료 새로고침", command=reload_data_callback).grid(
        row=0, column=3, sticky="ew", padx=(4, 0)
    )

    return container