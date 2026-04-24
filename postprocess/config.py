import os

# 현재 파일(main.py 기준)의 절대 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 데이터/출력 폴더 경로
DATA_DIR = os.path.join(BASE_DIR, "data")          # 입력 데이터 폴더
OUTPUT_DIR = os.path.join(BASE_DIR, "output")      # 결과 저장 폴더
GENERATED_ROTATIONS_DIR = os.path.join(OUTPUT_DIR, "generated_rotations")  # 생성된 로테이션 저장

# 입력 데이터 파일 경로
BEST_ORDERS_JSON = os.path.join(DATA_DIR, "best_orders.json")  # 캐릭터별 파티 구성
GEAR_JSON = os.path.join(DATA_DIR, "gear.json")                # 무기/성유물 정보
LEGAL_ACTIONS_JSON = os.path.join(DATA_DIR, "gcsim_legal_actions_all.json")  # 행동 가능 목록
LEGAL_PARSER_JSON = os.path.join(DATA_DIR, "gcsim_legal_actions_parser.json") # 행동 조건 파싱용

# 외부 실행 파일 및 상태 저장
GCSIM_EXE = os.path.join(BASE_DIR, "gcsim.exe")   # gcsim 실행 파일
PROGRESS_JSON = os.path.join(BASE_DIR, "progress.json")  # 완료된 캐릭터 기록
TIMEOUT_CHARACTERS_JSON = os.path.join(BASE_DIR, "timeout_characters.json")  # 타임아웃 기록

# =========================
# 토큰 / 행동 관련
# =========================

WORKERS = 4  
# 병렬 처리 워커 수 (CPU 코어 수에 맞게 조절)

MAIN_DPS_BONUS = 2.0  
# 메인 딜러에게 가중치 (토큰 분배 시 우선순위)

SUPPORT_WEIGHT = 1.0  
# 서포터 캐릭터 기본 가중치

MAX_TOKEN_RATIO = 0.5  
# 한 캐릭터가 가져갈 수 있는 최대 토큰 비율 (T의 50%)

ACTION_BLACKLIST = {"swap"}  
# 절대 사용하지 않을 행동 (예: swap 금지)

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
# 모든 가능한 행동 타입 목록

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
# 행동 선택 시 가중치 (높을수록 더 자주 선택됨)

CHARACTER_DEFAULT_STATES = {}
# 캐릭터 시작 상태 (버프/특수 상태 초기값)
# 예: {"xianyun": {"airborne_buff"}}

# =========================
# GA 설정
# =========================

POP_SIZE = 100  
# 한 세대당 개체 수 (클수록 정확하지만 느림)

GENERATIONS = 50
# 세대 반복 횟수 (클수록 더 오래 탐색)

MUTATION_PROB = 0.15  
# 돌연변이 확률 (0.15 = 15%)

SURVIVAL_RATIO = 0.20  
# 상위 몇 %만 생존할지 (0.20 = 상위 20%)

RANDOM_INJECTION_RATIO = 0.15  
# 매 세대에 랜덤 개체 추가 비율 (탐색 다양성 유지)

# =========================
# T 탐색
# =========================

T_START = 4  
# 탐색 시작 토큰 수

T_MAX = 30  
# 최대 토큰 수 (이 이상은 탐색 안함)

EARLY_STOP_DROP_RATIO = 0.05  
# 최고 DPS 대비 몇 % 이상 떨어지면 “성능 하락”으로 판단 (5%)

EARLY_STOP_STREAK = 3  
# 성능 하락이 몇 번 연속 발생하면 T 증가 탐색 중단
ELITE_RATIO = 0.05
