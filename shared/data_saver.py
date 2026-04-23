import json

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


DATA_PATHS = {
    "characters": CHARACTERS_JSON,
    "weapons": WEAPONS_JSON,
    "sets": SETS_JSON,
    "teams": TEAMS_JSON,
    "gear": GEAR_JSON,
    "best_orders": BEST_ORDERS_JSON,
    "legal_actions": LEGAL_ACTIONS_JSON,
    "legal_parser": LEGAL_PARSER_JSON,
}


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_data(name: str, data, app_state=None):
    if name not in DATA_PATHS:
        raise ValueError(f"지원하지 않는 데이터 이름: {name}")

    save_json(DATA_PATHS[name], data)

    if app_state is not None:
        if not hasattr(app_state, "data") or app_state.data is None:
            app_state.data = {}
        app_state.data[name] = data


def save_many(data_map: dict, app_state=None):
    for name, data in data_map.items():
        save_data(name, data, app_state=app_state)