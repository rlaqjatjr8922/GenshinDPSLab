from tkinter import ttk


def create_progress_panel(
    parent,
    progress_vars,
    progress_text_vars,
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

    progress_rows = []

    for i in range(3):
        label = ttk.Label(progress_box, textvariable=progress_text_vars[i])
        label.grid(row=i * 2, column=0, sticky="w", pady=(0, 4))

        bar = ttk.Progressbar(
            progress_box,
            maximum=100,
            variable=progress_vars[i],
        )
        bar.grid(row=i * 2 + 1, column=0, sticky="ew", pady=(0, 12))

        progress_rows.append((label, bar))

    ttk.Label(progress_box, textvariable=status_var).grid(
        row=6, column=0, sticky="w"
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

    return container, progress_rows