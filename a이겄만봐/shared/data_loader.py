import json
from pathlib import Path

from config.config import (
    DATA_DIR,
    CHARACTERS_JSON,
    WEAPONS_JSON,
    SETS_JSON,
    GEAR_JSON,
    BEST_ORDERS_JSON,
    LEGAL_ACTIONS_JSON,
    LEGAL_PARSER_JSON,
)


DEFAULT_DATA = {
    CHARACTERS_JSON: {},
    WEAPONS_JSON: {},
    SETS_JSON: {},
    GEAR_JSON: {},
    BEST_ORDERS_JSON: {},
    LEGAL_ACTIONS_JSON: {},
    LEGAL_PARSER_JSON: {},
}


def _ensure_json_file(path: Path, default_value):
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_value, f, ensure_ascii=False, indent=2)
        return default_value

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_value, f, ensure_ascii=False, indent=2)
        return default_value


def load_json(path: Path):
    default_value = DEFAULT_DATA.get(path, {})
    return _ensure_json_file(path, default_value)


def load_all():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    return {
        "characters": load_json(CHARACTERS_JSON),
        "weapons": load_json(WEAPONS_JSON),
        "sets": load_json(SETS_JSON),
        "gear": load_json(GEAR_JSON),
        "best_orders": load_json(BEST_ORDERS_JSON),
        "legal_actions": load_json(LEGAL_ACTIONS_JSON),
        "legal_parser": load_json(LEGAL_PARSER_JSON),
    }