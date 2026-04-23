import tkinter as tk

from controller.main_controller import MainController

from ui.header import create_header
from ui.stage_buttons import create_stage_buttons
from ui.progress_panel import create_progress_panel
from ui.log_panel import create_log_panel


class MainControllerUI:
    def __init__(self, root: tk.Tk, app_state):
        self.root = root
        self.app_state = app_state

        self.root.title("LOLSTERT 메인 컨트롤")
        self.root.geometry("1260x780")
        self.root.minsize(1080, 720)

        self.status_var = tk.StringVar(value="대기 중")

        # 진행바 최대 3개
        self.progress_vars = [
            tk.DoubleVar(value=0),
            tk.DoubleVar(value=0),
            tk.DoubleVar(value=0),
        ]

        self.progress_text_vars = [
            tk.StringVar(value="기본 진행도"),
            tk.StringVar(value=""),
            tk.StringVar(value=""),
        ]

        self.data_info_var = tk.StringVar(value="")

        self.stage_titles = [
            "1 돌림",
            "2 활성화",
            "2 돌림",
            "3 활성화",
        ]

        self.stage_buttons = []
        self.progress_rows = []
        self.log_text = None

        self.controller = MainController(self, app_state)

        self._build_layout()

        self.refresh_stage_buttons(
            False,
            self.controller.get_stage_enabled_states(),
        )
        self.update_data_info()

        # 기본은 1개만 보이게
        self.show_progress_bars(1)

        self.after_log_poll()

    def _build_layout(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

        header = create_header(self.root, self.status_var)
        header.grid(row=0, column=0, sticky="ew")

        top_buttons, self.stage_buttons = create_stage_buttons(
            self.root,
            self.stage_titles,
            self.controller.start_stage,
        )
        top_buttons.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))

        body = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        body.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

        left = tk.Frame(body, padx=8, pady=8)
        right = tk.Frame(body, padx=8, pady=8)

        body.add(left, stretch="always", minsize=420)
        body.add(right, stretch="always", minsize=520)

        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=1)

        progress_panel, self.progress_rows = create_progress_panel(
            left,
            self.progress_vars,
            self.progress_text_vars,
            self.status_var,
            self.controller.start_full_run,
            self.controller.request_stop,
            self.controller.reset_progress,
            self.controller.reload_data,
        )
        progress_panel.grid(row=0, column=0, sticky="nsew")

        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)

        data_panel = tk.LabelFrame(right, text="데이터 현황", padx=12, pady=12)
        data_panel.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        data_panel.grid_columnconfigure(0, weight=1)

        data_info_label = tk.Label(
            data_panel,
            textvariable=self.data_info_var,
            anchor="w",
            justify="left",
            font=("맑은 고딕", 11),
        )
        data_info_label.grid(row=0, column=0, sticky="nsew")

        log_panel, self.log_text = create_log_panel(
            right,
            self.clear_log,
            self.controller.open_output_folder,
            self.controller.validate_settings,
        )
        log_panel.grid(row=1, column=0, sticky="nsew")

    def after_log_poll(self):
        self.controller.poll_log_queue()
        self.update_data_info()
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

    def set_progress(self, index: int, percent: float):
        if 0 <= index < len(self.progress_vars):
            self.progress_vars[index].set(percent)

    def set_progress_text(self, index: int, text: str):
        if 0 <= index < len(self.progress_text_vars):
            self.progress_text_vars[index].set(text)

    # 기존 컨트롤러 호환용
    def set_current_progress(self, percent: float):
        self.set_progress(0, percent)

    def set_total_progress(self, percent: float):
        self.set_progress(1, percent)

    def set_total_progress_text(self, text: str):
        self.set_progress_text(1, text)

    def set_current_progress_text(self, text: str):
        self.set_progress_text(0, text)

    def set_status(self, text: str):
        self.status_var.set(text)

    def show_progress_bars(self, count: int):
        for i, (label, bar) in enumerate(self.progress_rows):
            if i < count:
                label.grid()
                bar.grid()
            else:
                label.grid_remove()
                bar.grid_remove()

    def update_data_info(self):
        s = self.app_state

        def count(x):
            if isinstance(x, (dict, list)):
                return len(x)
            return 0

        text = (
            f"characters: {count(s.characters)}\n"
            f"weapons: {count(s.weapons)}\n"
            f"sets: {count(s.sets)}\n"
            f"teams: {count(s.teams)}\n"
            f"gear: {count(s.gear)}\n"
            f"best_orders: {count(s.best_orders)}\n"
            f"legal_actions_all: {count(s.gcsim_legal_actions_all)}\n"
            f"legal_parser: {count(s.gcsim_legal_actions_parser)}"
        )

        self.data_info_var.set(text)

    def refresh_stage_buttons(self, worker_running: bool, enabled_states):
        for i, btn in enumerate(self.stage_buttons):
            if worker_running:
                try:
                    btn.config(state="disabled")
                except Exception:
                    pass
                continue

            try:
                btn.config(state="normal" if enabled_states[i] else "disabled")
            except Exception:
                pass