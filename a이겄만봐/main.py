import tkinter as tk

from config.config import ensure_dirs
from shared.app_state import AppState
from shared.data_loader import load_all
from ui.main_control_ui import MainControllerUI


def main():
    ensure_dirs()

    app_state = AppState()
    app_state.data = load_all()

    root = tk.Tk()
    app = MainControllerUI(root, app_state)
    app_state.ui = app

    root.mainloop()


if __name__ == "__main__":
    main()