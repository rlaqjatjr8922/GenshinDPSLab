from tkinter import ttk


def create_header(parent, status_var):
    frame = ttk.Frame(parent, padding=12)
    frame.columnconfigure(1, weight=1)

    ttk.Label(
        frame,
        text="원신 dps 시뮬레이터",
        font=("맑은 고딕", 18, "bold"),
    ).grid(row=0, column=0, sticky="w")

    ttk.Label(
        frame,
        textvariable=status_var,
        font=("맑은 고딕", 11),
    ).grid(row=0, column=1, sticky="e")

    return frame