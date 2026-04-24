import json
from pathlib import Path

from config.config import (
    CHARACTERS_JSON,
    WEAPONS_JSON,
    SETS_JSON,
    TEAMS_JSON,
    GEAR_JSON,
    BEST_ORDERS_JSON,
    LEGAL_ACTIONS_JSON,
    LEGAL_PARSER_JSON,
)
from shared.app_state import AppState


def load_json(path: Path):
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_all() -> AppState:
    app_state = AppState()

    app_state.characters = load_json(CHARACTERS_JSON)
    app_state.weapons = load_json(WEAPONS_JSON)
    app_state.sets = load_json(SETS_JSON)

    app_state.teams = load_json(TEAMS_JSON)
    app_state.gear = load_json(GEAR_JSON)
    app_state.best_orders = load_json(BEST_ORDERS_JSON)

    app_state.gcsim_legal_actions_all = load_json(LEGAL_ACTIONS_JSON)
    app_state.gcsim_legal_actions_parser = load_json(LEGAL_PARSER_JSON)

    return app_state