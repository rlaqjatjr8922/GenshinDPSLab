import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
GENERATED_ROTATIONS_DIR = os.path.join(OUTPUT_DIR, "generated_rotations")

BEST_ORDERS_JSON = os.path.join(DATA_DIR, "best_orders.json")
GEAR_JSON = os.path.join(DATA_DIR, "gear.json")
LEGAL_ACTIONS_JSON = os.path.join(DATA_DIR, "gcsim_legal_actions_all.json")
LEGAL_PARSER_JSON = os.path.join(DATA_DIR, "gcsim_legal_actions_parser.json")

GCSIM_EXE = os.path.join(BASE_DIR, "gcsim.exe")
PROGRESS_JSON = os.path.join(BASE_DIR, "progress.json")
TIMEOUT_CHARACTERS_JSON = os.path.join(BASE_DIR, "timeout_characters.json")
DEFAULT_TOTAL_TOKENS = 12
MAIN_DPS_BONUS = 2.0
SUPPORT_WEIGHT = 1.0
MAX_TOKEN_RATIO = 0.5

ACTION_BLACKLIST = {"swap"}

DEFAULT_ACTION_WEIGHTS = {
    "attack": 1.0,
    "charge": 0.7,
    "aim": 0.2,
    "skill": 1.3,
    "burst": 1.4,
    "dash": 0.4,
    "jump": 0.3,
    "walk": 0.1,
    "low_plunge": 0.6,
    "high_plunge": 0.8,
}

CHARACTER_DEFAULT_STATES = {
    # 예:
    # "xianyun": {"cloud_transmogrification"},
}

POPULATION_SIZE = 48
GENERATIONS = 30
ELITE_RATIO = 0.20
MUTATION_RATE = 0.15

ACTION_KEYS = [
    "attack",
    "charge",
    "aim",
    "skill",
    "burst",
    "dash",
    "jump",
    "walk",
    "low_plunge",
    "high_plunge",
]

EARLY_STOP_DROP_RATIO = 0.95
EARLY_STOP_STREAK = 3

T_START = 4
T_MAX = 30