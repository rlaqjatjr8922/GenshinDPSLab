from config.config import COLLECT_SETTINGS


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


def build_collect_config():
    return {
        "max_workers": COLLECT_SETTINGS.get("MAX_WORKERS", 4),
        "search_result_limit": COLLECT_SETTINGS.get("SEARCH_RESULT_LIMIT", 10),
        "max_docs": COLLECT_SETTINGS.get("MAX_DOCS_PER_CHARACTER", 8),
        "min_content_length": COLLECT_SETTINGS.get("MIN_TEXT_LENGTH", 300),
        "save_raw_text": COLLECT_SETTINGS.get("SAVE_RAW_TEXT", True),
        "ignore_keywords": COLLECT_SETTINGS.get("IGNORE_KEYWORDS", []),
        "block_sites": COLLECT_SETTINGS.get("BLOCK_SITES", []),
        "search_keywords": COLLECT_SETTINGS.get("SEARCH_KEYWORDS", []),
        "search_suffixes": COLLECT_SETTINGS.get("SEARCH_SUFFIXES", []),
    }


# 기존 코드 호환용
config = build_collect_config()


def build_collect_context(app_state):
    characters_data = app_state.characters or {}
    weapons_data = app_state.weapons or {}
    sets_data = app_state.sets or {}

    return {
        "config": build_collect_config(),

        "character_names": _build_names(characters_data),
        "weapon_names": _build_names(weapons_data),
        "set_names": _build_names(sets_data),

        "character_alias_map": _build_alias_map(characters_data),
        "weapon_alias_map": _build_alias_map(weapons_data),
        "set_alias_map": _build_alias_map(sets_data),
    }