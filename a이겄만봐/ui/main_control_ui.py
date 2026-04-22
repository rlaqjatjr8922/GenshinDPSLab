import tkinter as tk
from tkinter import ttk

from config.config import BASE_DIR, DATA_DIR, OUTPUT_DIR, GCSIM_EXE
from controller.main_controller import MainController

from ui.header import create_header
from ui.stage_buttons import create_stage_buttons
from ui.progress_panel import create_progress_panel
from ui.log_panel import create_log_panel
from ui.path_panel import create_path_panel


class MainControllerUI:
    def __init__(self, root: tk.Tk, app_state):
        self.root = root
        self.app_state = app_state

        self.root.title("LOLSTERT 메인 컨트롤")
        self.root.geometry("1260x780")
        self.root.minsize(1080, 720)

        self.status_var = tk.StringVar(value="대기 중")

        self.total_progress_var = tk.DoubleVar(value=0)
        self.current_progress_var = tk.DoubleVar(value=0)

        self.total_progress_text_var = tk.StringVar(
            value="전체 진행도: 0 / 0 캐릭터 완료"
        )
        self.current_progress_text_var = tk.StringVar(
            value="현재 검색 진행도: 0 / 0 문서"
        )

        self.base_dir_var = tk.StringVar(value=str(BASE_DIR))
        self.data_dir_var = tk.StringVar(value=str(DATA_DIR))
        self.output_dir_var = tk.StringVar(value=str(OUTPUT_DIR))
        self.gcsim_var = tk.StringVar(value=str(GCSIM_EXE))

        self.stage_titles = [
            "1 돌림",
            "2 활성화",
            "2 돌림",
            "3 활성화",
        ]

        self.stage_buttons = []
        self.log_text = None

        self.controller = MainController(self, app_state)

        self._build_layout()
        self.after_log_poll()

    def _build_layout(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        header = create_header(self.root, self.status_var)
        header.grid(row=0, column=0, sticky="ew")

        top_buttons, self.stage_buttons = create_stage_buttons(
            self.root,
            self.stage_titles,
            self.controller.start_stage,
        )
        top_buttons.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))

        body = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        body.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

        left = ttk.Frame(body, padding=8)
        right = ttk.Frame(body, padding=8)

        body.add(left, weight=3)
        body.add(right, weight=2)

        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)

        progress_panel = create_progress_panel(
            left,
            self.total_progress_var,
            self.current_progress_var,
            self.total_progress_text_var,
            self.current_progress_text_var,
            self.status_var,
            self.controller.start_full_run,
            self.controller.request_stop,
            self.controller.reset_progress,
            self.controller.reload_data,
        )
        progress_panel.grid(row=0, column=0, sticky="nsew")

        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        path_panel = create_path_panel(
            right,
            self.base_dir_var,
            self.data_dir_var,
            self.output_dir_var,
            self.gcsim_var,
        )
        path_panel.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        log_panel, self.log_text = create_log_panel(
            right,
            self.clear_log,
            self.controller.open_output_folder,
            self.controller.validate_settings,
        )
        log_panel.grid(row=1, column=0, sticky="nsew")

    def after_log_poll(self):
        self.controller.poll_log_queue()
        self.root.after(100, self.after_log_poll)

    def append_log(self, message: str):
        if self.log_text is None:
            return
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def clear_log(self):
        if self.log_text is None:
            return
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

    def set_current_progress(self, percent: float):
        self.current_progress_var.set(percent)

    def set_total_progress(self, percent: float):
        self.total_progress_var.set(percent)

    def set_total_progress_text(self, text: str):
        self.total_progress_text_var.set(text)

    def set_current_progress_text(self, text: str):
        self.current_progress_text_var.set(text)

    def set_status(self, text: str):
        self.status_var.set(text)

    def refresh_stage_buttons(self, worker_running: bool, completed_stages):
        for i, btn in enumerate(self.stage_buttons):
            if worker_running:
                btn.state(["disabled"])
                continue

            if i == 0:
                btn.state(["!disabled"])
            elif completed_stages[i - 1]:
                btn.state(["!disabled"])
            else:
                btn.state(["disabled"])


if __name__ == "__main__":
    class DummyState:
        def __init__(self):
            self.data = {}
            self.stage1 = None
            self.stage2 = None
            self.stage3 = None
            self.stage4 = None
            self.ui = None

    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    dummy = DummyState()
    app = MainControllerUI(root, dummy)
    dummy.ui = app

    root.mainloop()