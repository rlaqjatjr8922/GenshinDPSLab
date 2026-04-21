from config import ACTION_BLACKLIST


def check_condition(condition: dict, local_state: dict, next_action_name: str | None = None) -> bool:
    ctype = condition.get("type")

    if ctype == "prev_action_required":
        allowed = condition.get("value", [])
        return local_state.get("prev_action") in allowed

    if ctype == "forbidden_state":
        forbidden = set(condition.get("state", []))
        current_states = set(local_state.get("states", set()))
        return len(forbidden & current_states) == 0

    if ctype == "required_state":
        required = set(condition.get("state", []))
        current_states = set(local_state.get("states", set()))
        return required.issubset(current_states)

    if ctype == "required_recent_state_exit":
        target = condition.get("state")
        recent = set(local_state.get("recent_state_exit", set()))
        return target in recent

    if ctype == "character_required":
        allowed = condition.get("value", [])
        return local_state.get("character") in allowed

    if ctype == "action_forbidden":
        forbidden_action = condition.get("action")
        if next_action_name is None:
            return False
        return next_action_name != forbidden_action

    if ctype == "compound":
        all_conditions = condition.get("all", [])
        return all(check_condition(sub, local_state, next_action_name) for sub in all_conditions)

    if ctype == "or":
        any_conditions = condition.get("any", [])
        return any(check_condition(sub, local_state, next_action_name) for sub in any_conditions)

    if ctype == "walk_prev_action_whitelist":
        allowed_prev = set(condition.get("allowed_prev_actions", []))
        return local_state.get("prev_action") in allowed_prev

    if ctype == "walk_prev_action_whitelist_inverse":
        forbidden_prev = set(condition.get("forbidden_prev_actions", []))
        return local_state.get("prev_action") not in forbidden_prev

    if ctype == "sequence_whitelist":
        allowed_sequences = condition.get("allowed_sequences", [])
        prev = local_state.get("prev_action")
        for seq in allowed_sequences:
            if len(seq) == 2 and seq[0] == prev and seq[1] == next_action_name:
                return True
        return False

    if ctype in ("not_implemented", "special_option"):
        return False

    if ctype == "option_flag":
        return True

    return False


def is_action_legal(char: str, action_name: str, action_info: dict, note_map: dict, party_state: dict, get_char_state) -> bool:
    if action_name in ACTION_BLACKLIST:
        return False

    legal = action_info.get("legal")
    note = action_info.get("notes", "").strip()

    char_state = get_char_state(party_state, char)

    local_state = {
        "character": char,
        "prev_action": char_state.get("prev_action"),
        "states": set(char_state.get("states", set())),
        "recent_state_exit": set(char_state.get("recent_state_exit", set())),
    }

    if legal == "✔":
        return True

    if legal == "❌":
        return False

    if legal == "⚠":
        condition = note_map.get(note)
        if not condition:
            return False
        return check_condition(condition, local_state, next_action_name=action_name)

    return False


def get_legal_actions_for_character(char: str, legal_db: dict, note_map: dict, party_state: dict, get_char_state) -> list[str]:
    result = []
    char_actions = legal_db.get(char, {})

    for action_name, action_info in char_actions.items():
        if action_name in ACTION_BLACKLIST:
            continue

        if is_action_legal(char, action_name, action_info, note_map, party_state, get_char_state):
            result.append(action_name)

    return result