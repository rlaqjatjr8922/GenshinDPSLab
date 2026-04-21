import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_name_list(data, root_key=None):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        if root_key and root_key in data and isinstance(data[root_key], list):
            data = data[root_key]

        if isinstance(data, list):
            return data

        names = []

        for value in data.values():
            if isinstance(value, str):
                names.append(value)
            elif isinstance(value, list):
                names.extend(str(item) for item in value if isinstance(item, str))

        return names

    return []


def build_name_mappings(data, root_key=None):
    alias_to_canonical = {}
    canonical_names = []

    if isinstance(data, list):
        for name in data:
            if isinstance(name, str):
                canonical_names.append(name)
                alias_to_canonical[name] = name
        return canonical_names, alias_to_canonical

    if isinstance(data, dict):
        if root_key and root_key in data and isinstance(data[root_key], dict):
            data = data[root_key]

        for canonical, value in data.items():
            if canonical not in canonical_names:
                canonical_names.append(canonical)

            alias_to_canonical[canonical] = canonical

            if isinstance(value, str):
                alias_to_canonical[value] = canonical
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        alias_to_canonical[item] = canonical

        return canonical_names, alias_to_canonical

    return canonical_names, alias_to_canonical


config = load_json(BASE_DIR / "config.json")
characters_data = load_json(DATA_DIR / "characters.json")
weapons_data = load_json(DATA_DIR / "weapons.json")
sets_data = load_json(DATA_DIR / "sets.json")

character_names, character_alias_map = build_name_mappings(characters_data, "characters")
weapon_names, weapon_alias_map = build_name_mappings(weapons_data, "weapons")
set_names, set_alias_map = build_name_mappings(sets_data, "sets")


save_dir_value = config.get("save_dir", "결과")
SAVE_DIR = Path(save_dir_value)

if not SAVE_DIR.is_absolute():
    SAVE_DIR = BASE_DIR / SAVE_DIR

SAVE_DIR.mkdir(parents=True, exist_ok=True)
