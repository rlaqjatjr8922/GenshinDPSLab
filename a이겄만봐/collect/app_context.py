import json

from config.config import CHARACTERS_JSON, WEAPONS_JSON, SETS_JSON
from config.settings import SETTINGS

config = SETTINGS["collect"]


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


characters_data = _load_json(CHARACTERS_JSON)
weapons_data = _load_json(WEAPONS_JSON)
sets_data = _load_json(SETS_JSON)


def _extract_list(data, key_candidates):
    for key in key_candidates:
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


def _extract_group_map(data, key_candidates):
    for key in key_candidates:
        value = data.get(key)
        if isinstance(value, dict):
            result = {}

            for canonical, aliases in value.items():
                canonical_norm = canonical.strip().lower().replace(" ", "")
                group = []

                if isinstance(aliases, list):
                    for alias in aliases:
                        alias_norm = alias.strip().lower()
                        if alias_norm:
                            group.append(alias_norm)
                            compact = alias_norm.replace(" ", "")
                            if compact not in group:
                                group.append(compact)

                if canonical_norm and canonical_norm not in group:
                    group.append(canonical_norm)

                result[canonical_norm] = group

            return result
    return {}


def _build_character_group_map(data):
    result = {}
    characters_obj = data.get("characters", {})

    if isinstance(characters_obj, dict):
        for canonical, aliases in characters_obj.items():
            canonical_norm = canonical.strip().lower()
            group = []

            if isinstance(aliases, list):
                for alias in aliases:
                    alias_norm = alias.strip().lower()
                    if alias_norm:
                        group.append(alias_norm)

            if canonical_norm and canonical_norm not in group:
                group.append(canonical_norm)

            result[canonical_norm] = group

    return result


def _build_item_group_map(data, items_key):
    result = {}
    items_obj = data.get(items_key, [])

    if isinstance(items_obj, list):
        for item in items_obj:
            raw = item.strip().lower()
            compact = raw.replace(" ", "")

            group = []
            if raw:
                group.append(raw)
            if compact and compact not in group:
                group.append(compact)

            if compact:
                result[compact] = group

    elif isinstance(items_obj, dict):
        for canonical, aliases in items_obj.items():
            canonical_norm = canonical.strip().lower().replace(" ", "")
            group = []

            if isinstance(aliases, list):
                for alias in aliases:
                    alias_norm = alias.strip().lower()
                    if alias_norm:
                        group.append(alias_norm)
                        compact = alias_norm.replace(" ", "")
                        if compact not in group:
                            group.append(compact)

            if canonical_norm and canonical_norm not in group:
                group.append(canonical_norm)

            result[canonical_norm] = group

    return result


# 캐릭터
character_names = _extract_list(characters_data, ["names", "items"])

if not character_names:
    characters_obj = characters_data.get("characters", {})
    if isinstance(characters_obj, dict):
        character_names = [k.strip().lower() for k in characters_obj.keys()]

character_alias_map = _extract_group_map(
    characters_data,
    ["character_aliases", "aliases", "alias_map"],
)

if not character_alias_map:
    character_alias_map = _build_character_group_map(characters_data)


# 무기
weapon_names = _extract_list(weapons_data, ["weapons", "names", "items"])

weapon_alias_map = _extract_group_map(
    weapons_data,
    ["weapon_aliases", "aliases", "alias_map"],
)

if not weapon_alias_map:
    weapon_alias_map = _build_item_group_map(weapons_data, "weapons")


# 세트
set_names = _extract_list(sets_data, ["sets", "names", "items"])

set_alias_map = _extract_group_map(
    sets_data,
    ["set_aliases", "aliases", "alias_map"],
)

if not set_alias_map:
    set_alias_map = _build_item_group_map(sets_data, "sets")


print("[DEBUG] character_alias_map:", len(character_alias_map))
print("[DEBUG] weapon_alias_map:", len(weapon_alias_map))
print("[DEBUG] set_alias_map:", len(set_alias_map))