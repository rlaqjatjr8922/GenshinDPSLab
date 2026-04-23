from tkinter import ttk


def create_stage_buttons(parent, stage_titles, start_stage_callback):
    frame = ttk.LabelFrame(parent, text="단계 실행", padding=10)

    for i in range(len(stage_titles)):
        frame.columnconfigure(i, weight=1)

    buttons = []
    for i, title in enumerate(stage_titles):
        btn = ttk.Button(
            frame,
            text=title,
            command=lambda idx=i: start_stage_callback(idx),
        )
        btn.grid(row=0, column=i, sticky="ew", padx=4)
        buttons.append(btn)

    return frame, buttons