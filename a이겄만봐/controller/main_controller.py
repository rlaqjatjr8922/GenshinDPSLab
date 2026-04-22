import os
import threading
import queue

from tkinter import messagebox

from config.config import BASE_DIR, DATA_DIR, OUTPUT_DIR, GCSIM_EXE


class MainController:
    def __init__(self, ui, app_state):
        self.ui = ui
        self.app_state = app_state

        self.log_queue = queue.Queue()
        self.current_worker = None
        self.stop_requested = False
        self.completed_stages = [False, False, False, False]

    def log(self, message: str):
        self.log_queue.put(message)

    def poll_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self.ui.append_log(msg)

        running = self.current_worker is not None and self.current_worker.is_alive()
        self.ui.refresh_stage_buttons(running, self.completed_stages)

    def start_stage(self, stage_index: int):
        if self.current_worker and self.current_worker.is_alive():
            messagebox.showwarning("실행 중", "이미 작업이 실행 중입니다.")
            return

        if stage_index > 0 and not self.completed_stages[stage_index - 1]:
            messagebox.showwarning("비활성", "이전 단계를 먼저 완료해야 합니다.")
            return

        self.stop_requested = False
        self.current_worker = threading.Thread(
            target=self._run_single_stage_safe,
            args=(stage_index,),
            daemon=True,
        )
        self.current_worker.start()

    def start_full_run(self):
        if self.current_worker and self.current_worker.is_alive():
            messagebox.showwarning("실행 중", "이미 작업이 실행 중입니다.")
            return

        self.stop_requested = False
        self.current_worker = threading.Thread(
            target=self._run_full_pipeline_safe,
            daemon=True,
        )
        self.current_worker.start()

    def request_stop(self):
        self.stop_requested = True
        self.ui.set_status("중지 요청됨")
        self.log("[중지] 사용자 요청")

    def reset_progress(self):
        if self.current_worker and self.current_worker.is_alive():
            messagebox.showwarning("실행 중", "초기화 불가")
            return

        self.ui.set_total_progress(0)
        self.ui.set_current_progress(0)
        self.ui.set_status("대기 중")

        if hasattr(self.ui, "set_total_progress_text"):
            self.ui.set_total_progress_text("전체 진행도: 0 / 0 캐릭터 완료")
        if hasattr(self.ui, "set_current_progress_text"):
            self.ui.set_current_progress_text("현재 검색 진행도: 0 / 0 문서")

        self.completed_stages = [False, False, False, False]

        self.app_state.stage1 = None
        self.app_state.stage2 = None
        self.app_state.stage3 = None
        self.app_state.stage4 = None

        self.log("[초기화 완료]")

    def reload_data(self):
        try:
            from shared.data_loader import load_all

            self.app_state.data = load_all()
            self.log("[데이터] 재로드 완료")
            messagebox.showinfo("완료", "데이터 재로드 완료")
        except Exception as e:
            error_text = str(e)
            self.log(f"[오류] {error_text}")
            messagebox.showerror("오류", error_text)

    def validate_settings(self):
        missing = []

        if not BASE_DIR.exists():
            missing.append("BASE_DIR")
        if not DATA_DIR.exists():
            missing.append("DATA_DIR")
        if not OUTPUT_DIR.exists():
            missing.append("OUTPUT_DIR")
        if not GCSIM_EXE.exists():
            missing.append("gcsim.exe")

        if missing:
            messagebox.showwarning("설정 오류", "\n".join(missing))
            self.log(f"[설정 오류] {missing}")
        else:
            messagebox.showinfo("정상", "경로 정상")
            self.log("[설정 정상]")

    def open_output_folder(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(OUTPUT_DIR)

    def _run_single_stage_safe(self, idx):
        try:
            self._run_single_stage(idx)
        except Exception as e:
            error_text = str(e)
            self.ui.set_status("오류")
            self.log(f"[오류] {error_text}")
            self.ui.root.after(
                0,
                lambda msg=error_text: messagebox.showerror("오류", msg),
            )

    def _run_full_pipeline_safe(self):
        try:
            self._run_full_pipeline()
        except Exception as e:
            error_text = str(e)
            self.ui.set_status("오류")
            self.log(f"[오류] {error_text}")
            self.ui.root.after(
                0,
                lambda msg=error_text: messagebox.showerror("오류", msg),
            )

    def _run_single_stage(self, idx):
        title = self.ui.stage_titles[idx]

        self.ui.set_status(f"{title} 실행 중")
        self.ui.set_current_progress(0)

        self.log("=" * 40)
        self.log(f"[시작] {title}")

        if idx == 0:
            self._run_stage_1()
        elif idx == 1:
            self._run_stage_2()
        elif idx == 2:
            self._run_stage_3()
        elif idx == 3:
            self._run_stage_4()

        if not self.stop_requested:
            self.completed_stages[idx] = True
            self.ui.set_current_progress(100)
            self.ui.set_status(f"{title} 완료")
            self.log(f"[완료] {title}")

    def _run_full_pipeline(self):
        self.log("=" * 40)
        self.log("[전체 실행 시작]")

        for i in range(4):
            if self.stop_requested:
                self.ui.set_status("중지됨")
                self.log("[중지됨]")
                return

            if self.completed_stages[i]:
                continue

            self._run_single_stage(i)

        self.ui.set_current_progress(100)
        self.ui.set_status("전체 완료")
        self.log("[전체 완료]")

    def _set_progress(self, idx, val):
        self.ui.set_current_progress(val)

    def _run_stage_1(self):
        from collect.run_collect import run

        run(
            self.app_state,
            progress_callback=lambda p: self._set_progress(0, p),
            log_callback=self.log,
        )

    def _run_stage_2(self):
        from preprocess.run_prepare import run

        run(
            self.app_state,
            progress_callback=lambda p: self._set_progress(1, p),
            log_callback=self.log,
        )

    def _run_stage_3(self):
        from engine.run_engine import run

        run(
            self.app_state,
            progress_callback=lambda p: self._set_progress(2, p),
            log_callback=self.log,
        )

    def _run_stage_4(self):
        from postprocess.run_post import run

        run(
            self.app_state,
            progress_callback=lambda p: self._set_progress(3, p),
            log_callback=self.log,
        )