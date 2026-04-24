from config import CHARACTER_DEFAULT_STATES


def init_party_state(members: list[str], active_char: str):
    chars = {}

    for c in members:
        default_states = set(CHARACTER_DEFAULT_STATES.get(c, set()))
        chars[c] = {
            "prev_action": None,
            "states": set(default_states),
            "recent_state_exit": set(),
            "skill_ready": True,
            "burst_ready": True,
            "energy": 100,
        }

    return {
        "time": 0.0,
        "active": active_char,
        "chars": chars,
    }


def get_char_state(party_state: dict, char: str) -> dict:
    return party_state["chars"][char]


def clear_recent_state_exit(char_state: dict):
    char_state["recent_state_exit"].clear()


def add_state(char_state: dict, state_name: str):
    char_state["states"].add(state_name)


def remove_state(char_state: dict, state_name: str):
    if state_name in char_state["states"]:
        char_state["states"].remove(state_name)
        char_state["recent_state_exit"].add(state_name)


def update_state_after_action(party_state: dict, char: str, action: str):
    char_state = get_char_state(party_state, char)

    clear_recent_state_exit(char_state)

    if action == "skill":
        char_state["skill_ready"] = False
        add_state(char_state, "skill_state")

    elif action == "burst":
        char_state["burst_ready"] = False
        char_state["energy"] = 0

    elif action in ("attack", "charge", "dash", "jump", "walk", "aim"):
        if "skill_state" in char_state["states"] and action in ("dash", "jump", "attack"):
            remove_state(char_state, "skill_state")

    elif action in ("low_plunge", "high_plunge"):
        pass

    char_state["prev_action"] = action
    party_state["active"] = char
    party_state["time"] += 0.7