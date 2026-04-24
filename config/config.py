from pathlib import Path

# =========================================
# 프로젝트 루트
# =========================================
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================
# 기본 경로
# =========================================
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
BIN_DIR = BASE_DIR / "bin"

# =========================================
# 실행 파일
# =========================================
GCSIM_EXE = BIN_DIR / "gcsim.exe"

# =========================================
# output 내부 구조
# =========================================
COLLECTED_DIR = OUTPUT_DIR / "collected"
CONFIGS_DIR = OUTPUT_DIR / "configs"
ROTATIONS_DIR = OUTPUT_DIR / "rotations"
RESULTS_DIR = OUTPUT_DIR / "results"
LOGS_DIR = OUTPUT_DIR / "logs"
FAILED_DIR = OUTPUT_DIR / "failed"

# =========================================
# data 파일 경로
# =========================================
CHARACTERS_JSON = DATA_DIR / "characters.json"
WEAPONS_JSON = DATA_DIR / "weapons.json"
SETS_JSON = DATA_DIR / "sets.json"

TEAMS_JSON = DATA_DIR / "teams.json"
GEAR_JSON = DATA_DIR / "gear.json"
BEST_ORDERS_JSON = DATA_DIR / "best_orders.json"

LEGAL_ACTIONS_JSON = DATA_DIR / "gcsim_legal_actions_all.json"
LEGAL_PARSER_JSON = DATA_DIR / "gcsim_legal_actions_parser.json"

# =========================================
# 실패 파일
# =========================================
FAILED_ACTIONS_CSV = OUTPUT_DIR / "gcsim_legal_actions_failed.csv"

# =========================================
# 병렬 처리
# =========================================
WORKERS = 4

# =========================================
# 토큰 / 행동 관련
# =========================================
MAIN_DPS_BONUS = 2.0
SUPPORT_WEIGHT = 1.0
MAX_TOKEN_RATIO = 0.5

ACTION_BLACKLIST = {"swap"}

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

CHARACTER_DEFAULT_STATES = {}

# =========================================
# GA 설정
# =========================================
POP_SIZE = 100
GENERATIONS = 50
MUTATION_PROB = 0.15
SURVIVAL_RATIO = 0.20
ELITE_RATIO = 0.05
RANDOM_INJECTION_RATIO = 0.15

# =========================================
# T 탐색
# =========================================
T_START = 4
T_MAX = 30
EARLY_STOP_DROP_RATIO = 0.05
EARLY_STOP_STREAK = 3

# =========================================
# 초기 폴더 생성 함수
# =========================================
def ensure_dirs():
    dirs = [
        DATA_DIR,
        OUTPUT_DIR,
        COLLECTED_DIR,
        CONFIGS_DIR,
        ROTATIONS_DIR,
        RESULTS_DIR,
        LOGS_DIR,
        FAILED_DIR,
        BIN_DIR,
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)