import importlib
import os
import queue
import threading

from tkinter import messagebox

from config.config import BASE_DIR, DATA_DIR, OUTPUT_DIR, GCSIM_EXE


class MainController:
    # 버튼 누르면 단계마다 보일 진행바 개수
    STAGE_BAR_COUNTS = {
        0: 2,  # 1 돌림
        1: 1,  # 2 활성화
        2: 2,  # 2 돌림
        3: 3,  # 3 활성화
    }

    # 단계별 진행바 텍스트
    STAGE_PROGRESS_LABELS = {
        0: ["1단계 진행도 A", "1단계 진행도 B", ""],
        1: ["2단계 진행도", "", ""],
        2: ["3단계 진행도 A", "3단계 진행도 B", ""],
        3: ["4단계 진행도 A", "4단계 진행도 B", "4단계 진행도 C"],
    }

    # 실제 실행 모듈 경로
    STAGE_MODULES = {
        0: "collect.run_collect",
        1: "preprocess.run_prepare",
        2: "engine.run_engine",
        3: "postprocess.run_post",
    }

    def __init__(self, ui, app_state):
        self.ui = ui
        self.app_state = app_state

        self.log_queue = queue.Queue()
        self.current_worker = None
        self.stop_requested = False
        self.completed_stages = [False, False, False, False]

    def log(self, message: str):
        self.log_queue.put(message)

    def get_stage_enabled_states(self):
        s = self.app_state

        stage1_enabled = (
            bool(s.weapons)
            and bool(s.sets)
            and bool(s.characters)
        )

        stage2_enabled = bool(s.characters)

        stage3_enabled = (
            bool(s.teams)
            and bool(s.gear)
        )

        stage4_enabled = (
            bool(s.gcsim_legal_actions_all)
            and bool(s.gcsim_legal_actions_parser)
            and bool(s.best_orders)
            and bool(s.gear)
        )

        return [
            stage1_enabled,
            stage2_enabled,
            stage3_enabled,
            stage4_enabled,
        ]

    def poll_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self.ui.append_log(msg)

        running = self.current_worker is not None and self.current_worker.is_alive()
        enabled_states = self.get_stage_enabled_states()
        self.ui.refresh_stage_buttons(running, enabled_states)

    def start_stage(self, stage_index: int):
        if self.current_worker and self.current_worker.is_alive():
            messagebox.showwarning("실행 중", "이미 작업이 실행 중입니다.")
            return

        enabled_states = self.get_stage_enabled_states()
        if not enabled_states[stage_index]:
            messagebox.showwarning("비활성", "필수 내부 데이터가 비어 있습니다.")
            return

        self._prepare_stage_ui(stage_index)

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

        self.ui.show_progress_bars(1)
        self.ui.set_progress(0, 0)
        self.ui.set_progress(1, 0)
        self.ui.set_progress(2, 0)
        self.ui.set_progress_text(0, "전체 진행도")
        self.ui.set_progress_text(1, "")
        self.ui.set_progress_text(2, "")

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

        self.ui.show_progress_bars(1)
        self.ui.set_progress(0, 0)
        self.ui.set_progress(1, 0)
        self.ui.set_progress(2, 0)

        self.ui.set_progress_text(0, "기본 진행도")
        self.ui.set_progress_text(1, "")
        self.ui.set_progress_text(2, "")

        self.ui.set_status("대기 중")

        self.completed_stages = [False, False, False, False]

        if hasattr(self.app_state, "stage1"):
            self.app_state.stage1 = None
        if hasattr(self.app_state, "stage2"):
            self.app_state.stage2 = None
        if hasattr(self.app_state, "stage3"):
            self.app_state.stage3 = None
        if hasattr(self.app_state, "stage4"):
            self.app_state.stage4 = None

        self.log("[초기화 완료]")

        enabled_states = self.get_stage_enabled_states()
        self.ui.refresh_stage_buttons(False, enabled_states)

    def reload_data(self):
        try:
            from shared.data_loader import load_all

            self.app_state = load_all()
            self.log("[데이터] 재로드 완료")

            enabled_states = self.get_stage_enabled_states()
            running = self.current_worker is not None and self.current_worker.is_alive()
            self.ui.refresh_stage_buttons(running, enabled_states)

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

    def _prepare_stage_ui(self, idx: int):
        bar_count = self.STAGE_BAR_COUNTS.get(idx, 1)
        labels = self.STAGE_PROGRESS_LABELS.get(idx, ["", "", ""])

        self.ui.show_progress_bars(bar_count)

        for i in range(3):
            self.ui.set_progress(i, 0)
            self.ui.set_progress_text(i, labels[i])

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

        self._prepare_stage_ui(idx)

        self.ui.set_status(f"{title} 실행 중")
        self.log("=" * 40)
        self.log(f"[시작] {title}")

        self._run_stage(idx)

        if not self.stop_requested:
            try:
                from shared.data_loader import load_all
                self.app_state = load_all()
            except Exception as e:
                self.log(f"[경고] 데이터 재로드 실패: {e}")

            self.completed_stages[idx] = True

            visible_count = self.STAGE_BAR_COUNTS.get(idx, 1)
            for i in range(visible_count):
                self.ui.set_progress(i, 100)

            self.ui.set_status(f"{title} 완료")
            self.log(f"[완료] {title}")

            enabled_states = self.get_stage_enabled_states()
            self.ui.refresh_stage_buttons(False, enabled_states)

    def _run_full_pipeline(self):
        self.log("=" * 40)
        self.log("[전체 실행 시작]")

        completed = 0
        runnable = 0

        initial_enabled_states = self.get_stage_enabled_states()
        for i in range(4):
            if initial_enabled_states[i]:
                runnable += 1

        if runnable == 0:
            self.ui.set_status("실행 가능 단계 없음")
            self.log("[중단] 실행 가능한 단계가 없습니다.")
            return

        for i in range(4):
            if self.stop_requested:
                self.ui.set_status("중지됨")
                self.log("[중지됨]")
                return

            enabled_states = self.get_stage_enabled_states()
            if not enabled_states[i]:
                self.log(f"[건너뜀] {self.ui.stage_titles[i]} - 내부 데이터 부족")
                continue

            self._run_single_stage(i)
            completed += 1

            percent = (completed / runnable) * 100
            self.ui.show_progress_bars(1)
            self.ui.set_progress(0, percent)
            self.ui.set_progress_text(0, f"전체 진행도: {completed} / {runnable}")

        self.ui.set_status("전체 완료")
        self.log("[전체 완료]")

    def _set_progress(self, val):
        self.ui.set_progress(0, val)

        current_text = self.ui.progress_text_vars[0].get()
        if current_text:
            if ":" in current_text:
                label = current_text.split(":")[0]
                self.ui.set_progress_text(0, f"{label}: {int(val)}%")
            else:
                self.ui.set_progress_text(0, f"{current_text} {int(val)}%")
        else:
            self.ui.set_progress_text(0, f"진행도: {int(val)}%")

    def _run_stage(self, idx: int):
        module_name = self.STAGE_MODULES[idx]

        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as e:
            self.ui.set_status("오류")
            self.log(f"[오류] {e}")
            return

        run = getattr(module, "run", None)
        if run is None:
            self.ui.set_status("오류")
            self.log(f"[오류] {module_name} 에 run 함수가 없습니다.")
            return

        run(
            self.app_state,
            progress_callback=self._set_progress,
            log_callback=self.log,
        )