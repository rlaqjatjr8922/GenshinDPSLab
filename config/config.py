from pathlib import Path

# =========================================
# 🔥 프로젝트 루트 (가장 중요)
# =========================================
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================
# 📁 기본 경로
# =========================================
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
BIN_DIR = BASE_DIR / "bin"

# =========================================
# ⚙ 실행 파일
# =========================================
GCSIM_EXE = BIN_DIR / "gcsim.exe"

# =========================================
# 📂 output 내부 구조
# =========================================
COLLECTED_DIR = OUTPUT_DIR / "collected"
CONFIGS_DIR = OUTPUT_DIR / "configs"
ROTATIONS_DIR = OUTPUT_DIR / "rotations"
RESULTS_DIR = OUTPUT_DIR / "results"
LOGS_DIR = OUTPUT_DIR / "logs"
FAILED_DIR = OUTPUT_DIR / "failed"

# =========================================
# 📄 data 파일 경로
# =========================================
CHARACTERS_JSON = DATA_DIR / "characters.json"
WEAPONS_JSON = DATA_DIR / "weapons.json"
SETS_JSON = DATA_DIR / "sets.json"
TEAMS_JSON = DATA_DIR / "teams.json"   # 추가
GEAR_JSON = DATA_DIR / "gear.json"
BEST_ORDERS_JSON = DATA_DIR / "best_orders.json"
LEGAL_ACTIONS_JSON = DATA_DIR / "gcsim_legal_actions_all.json"
LEGAL_PARSER_JSON = DATA_DIR / "gcsim_legal_actions_parser.json"

# =========================================
# 🧠 GA 설정 (나중에 사용)
# =========================================
POP_SIZE = 32
GENERATIONS = 10
MUTATION_PROB = 0.2
SURVIVAL_RATIO = 0.2
ELITE_RATIO = 0.1
RANDOM_INJECTION_RATIO = 0.1

# =========================================
# ⏱ 실행 옵션
# =========================================
TIMEOUT_SECONDS = 20
MAX_WORKERS = 4

# =========================================
# 📦 초기 폴더 생성 함수
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