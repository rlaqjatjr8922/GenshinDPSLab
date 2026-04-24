import os
import sys
import tkinter as tk


# =========================================
# 경로 보정 (multiprocessing 필수)
# =========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# =========================================
# imports
# =========================================
from config.config import ensure_dirs
from shared.data_loader import load_all
from ui.main_control_ui import MainControllerUI


# =========================================
# main
# =========================================
def main():
    ensure_dirs()

    app_state = load_all()

    root = tk.Tk()
    app = MainControllerUI(root, app_state)
    app_state.ui = app

    root.mainloop()


# =========================================
# entry point (Windows multiprocessing 필수)
# =========================================
if __name__ == "__main__":
    import multiprocessing as mp

    mp.freeze_support()  # 🔥 이거 없으면 spawn 오류남
    main()