from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


def create_log_panel(
    parent,
    clear_log_callback,
    open_output_folder_callback,
    validate_settings_callback,
):
    frame = ttk.LabelFrame(parent, text="실행 로그", padding=10)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    log_text = ScrolledText(frame, wrap="word", font=("Consolas", 10))
    log_text.grid(row=0, column=0, sticky="nsew")
    log_text.configure(state="disabled")

    bottom_row = ttk.Frame(frame)
    bottom_row.grid(row=1, column=0, sticky="ew", pady=(8, 0))
    bottom_row.columnconfigure((0, 1, 2), weight=1)

    ttk.Button(bottom_row, text="로그 지우기", command=clear_log_callback).grid(
        row=0, column=0, sticky="ew", padx=(0, 4)
    )
    ttk.Button(
        bottom_row,
        text="출력 폴더 열기",
        command=open_output_folder_callback,
    ).grid(row=0, column=1, sticky="ew", padx=4)
    ttk.Button(
        bottom_row,
        text="설정 확인",
        command=validate_settings_callback,
    ).grid(row=0, column=2, sticky="ew", padx=(4, 0))

    return frame, log_text