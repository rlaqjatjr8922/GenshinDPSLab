import json
import os

from config import PROGRESS_JSON


def load_progress():
    if not os.path.exists(PROGRESS_JSON):
        return {"completed": []}

    with open(PROGRESS_JSON, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_progress(progress: dict):
    with open(PROGRESS_JSON, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def mark_completed(progress: dict, main_name: str):
    if "completed" not in progress:
        progress["completed"] = []

    if main_name not in progress["completed"]:
        progress["completed"].append(main_name)