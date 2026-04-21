import json
import os

from config import TIMEOUT_CHARACTERS_JSON


def load_timeout_data():
    if not os.path.exists(TIMEOUT_CHARACTERS_JSON):
        return {"timeout_characters": {}}

    with open(TIMEOUT_CHARACTERS_JSON, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def save_timeout_data(data: dict):
    with open(TIMEOUT_CHARACTERS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def mark_timeout_character(timeout_data: dict, main_name: str, total_tokens: int, reason: str):
    if "timeout_characters" not in timeout_data:
        timeout_data["timeout_characters"] = {}

    timeout_data["timeout_characters"][main_name] = {
        "total_tokens": total_tokens,
        "reason": reason,
    }