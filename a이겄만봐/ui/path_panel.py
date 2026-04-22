from tkinter import ttk


def _add_readonly_path(parent, row, label, variable):
    ttk.Label(parent, text=label).grid(
        row=row, column=0, sticky="w", padx=(0, 8), pady=3
    )
    entry = ttk.Entry(parent, textvariable=variable, state="readonly")
    entry.grid(row=row, column=1, sticky="ew", pady=3)


def create_path_panel(parent, base_dir_var, data_dir_var, output_dir_var, gcsim_var):
    frame = ttk.LabelFrame(parent, text="경로 설정", padding=10)
    frame.columnconfigure(1, weight=1)

    _add_readonly_path(frame, 0, "베이스", base_dir_var)
    _add_readonly_path(frame, 1, "데이터", data_dir_var)
    _add_readonly_path(frame, 2, "출력", output_dir_var)
    _add_readonly_path(frame, 3, "gcsim", gcsim_var)

    return frame