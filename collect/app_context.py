from config.settings import SETTINGS

config = SETTINGS["collect"]


def _normalize_alias(text: str) -> str:
    return str(text).strip().lower()


def _normalize_canonical(text: str) -> str:
    return str(text).strip().lower()


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


def build_collect_context(app_state):
    characters_data = app_state.characters or {}
    weapons_data = app_state.weapons or {}
    sets_data = app_state.sets or {}

    return {
        "config": config,

        "character_names": _build_names(characters_data),
        "weapon_names": _build_names(weapons_data),
        "set_names": _build_names(sets_data),

        "character_alias_map": _build_alias_map(characters_data),
        "weapon_alias_map": _build_alias_map(weapons_data),
        "set_alias_map": _build_alias_map(sets_data),
    }