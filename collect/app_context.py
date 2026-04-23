import json

from config.config import CHARACTERS_JSON, WEAPONS_JSON, SETS_JSON
from config.settings import SETTINGS

config = SETTINGS["collect"]


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_alias(text: str) -> str:
    return text.strip().lower()


def _normalize_canonical(text: str) -> str:
    return text.strip().lower()


def _build_names(data: dict):
    if not isinstance(data, dict):
        return []
    return [_normalize_canonical(k) for k in data.keys()]


def _build_alias_map(data: dict):
    result = {}

    if not isinstance(data, dict):
        return result

    for canonical, aliases in data.items():
        canonical_norm = _normalize_canonical(canonical)

        group = []

        if isinstance(aliases, list):
            for alias in aliases:
                if not isinstance(alias, str):
                    continue

                alias_norm = _normalize_alias(alias)
                if alias_norm and alias_norm not in group:
                    group.append(alias_norm)

                compact = alias_norm.replace(" ", "")
                if compact and compact not in group:
                    group.append(compact)

        if canonical_norm and canonical_norm not in group:
            group.append(canonical_norm)

        canonical_compact = canonical_norm.replace(" ", "")
        if canonical_compact and canonical_compact not in group:
            group.append(canonical_compact)

        result[canonical_norm] = group

    return result


characters_data = _load_json(CHARACTERS_JSON)
weapons_data = _load_json(WEAPONS_JSON)
sets_data = _load_json(SETS_JSON)


# 캐릭터
character_names = _build_names(characters_data)
character_alias_map = _build_alias_map(characters_data)


# 무기
weapon_names = _build_names(weapons_data)
weapon_alias_map = _build_alias_map(weapons_data)


# 세트
set_names = _build_names(sets_data)
set_alias_map = _build_alias_map(sets_data)


print("[DEBUG] character_names:", len(character_names))
print("[DEBUG] weapon_names:", len(weapon_names))
print("[DEBUG] set_names:", len(set_names))

print("[DEBUG] character_alias_map:", len(character_alias_map))
print("[DEBUG] weapon_alias_map:", len(weapon_alias_map))
print("[DEBUG] set_alias_map:", len(set_alias_map))