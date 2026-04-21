import os

from config import (
    BEST_ORDERS_JSON,
    GEAR_JSON,
    LEGAL_ACTIONS_JSON,
    LEGAL_PARSER_JSON,
)
from core.utils import load_json


def check_required_files():
    for path, label in [
        (BEST_ORDERS_JSON, "best_orders.json"),
        (GEAR_JSON, "gear.json"),
        (LEGAL_ACTIONS_JSON, "gcsim_legal_actions_all.json"),
        (LEGAL_PARSER_JSON, "gcsim_legal_actions_parser.json"),
    ]:
        if not os.path.exists(path):
            print(f"[오류] {label} 없음")
            print(path)
            return False
    return True


def load_best_orders():
    data = load_json(BEST_ORDERS_JSON)
    result = {}

    for main_name, party in data.items():
        key = main_name.strip().lower()

        if isinstance(party, str):
            members = [x.strip().lower() for x in party.split("/") if x.strip()]
        elif isinstance(party, list):
            members = [x.strip().lower() for x in party]
        else:
            raise ValueError(f"best_orders.json 형식 이상: {main_name} -> {party}")

        result[key] = members

    return result


def load_gear():
    raw = load_json(GEAR_JSON)
    result = {}

    for char_name, info in raw.items():
        key = char_name.strip().lower()
        result[key] = {
            "weapon": info["weapon"].strip().lower(),
            "set_name": info["set_name"].strip().lower(),
        }

    return result


def load_legal_actions():
    raw = load_json(LEGAL_ACTIONS_JSON)
    result = {}

    for char_name, actions in raw.items():
        key = char_name.strip().lower()
        result[key] = actions

    return result


def build_note_parser():
    parser_list = load_json(LEGAL_PARSER_JSON)
    note_map = {}

    for item in parser_list:
        note = item.get("note", "").strip()
        condition = item.get("condition")
        if note:
            note_map[note] = condition

    return note_map