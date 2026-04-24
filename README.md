# 🔥 Genshin Auto DPS Analyzer

## 📌 프로젝트 소개

이 프로젝트는 **원신 캐릭터의 최적 파티 구성과 행동 순서를 자동으로 분석**하는 프로그램입니다.

웹 데이터를 수집하고, 행동 조건을 생성한 뒤,
gcsim 시뮬레이션을 통해 **가장 높은 DPS를 내는 파티 순서**를 찾아냅니다.

---

## ⚙️ 기능 (1 ~ 4 단계)

### 1️⃣ 데이터 수집 (Collect)

* 캐릭터별 웹 검색
* 파티 / 무기 / 성유물 정보 추출
* 텍스트 분석 및 정리

### 2️⃣ 전처리 (Preprocess)

* gcsim Legal Actions 크롤링
* 행동 가능 조건 생성
* notes 및 조건 데이터 정리

### 3️⃣ 엔진 (Engine)

* 파티 순서 모든 경우 생성 (Permutation)
* gcsim 실행
* 메인 딜러 기준 DPS 평가
* 최고 순서 선택

### 4️⃣ 새부분석 (Postprocess)

* 최종 결과 정리
* 실패 캐릭 제외
* JSON / CSV 결과 저장

---

## 📂 폴더 구조

```text
main.py
controller/
postprocess/
ui/
data/
output/
external_postprocess/
```

### 주요 폴더 설명

```text
controller/ : 버튼 → 실행 연결
ui/ : UI 구성
data/ : 입력/중간 데이터
output/ : 결과 및 로그
external_postprocess/ : gcsim + GA 분석 엔진
```

---

## ▶️ 실행 방법

```bash
python main.py
```

### 실행 순서

```text
1 → 데이터 수집
2 → 전처리
3 → 엔진 실행
4 → 결과 생성
```

또는 UI에서 버튼 클릭으로 실행

---

## ⚙️ 설정값

### 1️⃣ Collect 설정

```text
MAX_WORKERS
SEARCH_RESULT_LIMIT
MAX_DOCS_PER_CHARACTER
MIN_TEXT_LENGTH
SAVE_RAW_TEXT
IGNORE_KEYWORDS
BLOCK_SITES
```

---

### 2️⃣ Preprocess 설정

```text
MAX_WORKERS
```

---

### 3️⃣ Engine 설정

```text
MAX_WORKERS
ITERATION
DURATION
GCSIM_TIMEOUT
```

---

### 4️⃣ 새부분석 설정

```text
MAX_WORKERS
POP_SIZE
GENERATIONS
T_START
T_MAX
GCSIM_TIMEOUT
ITERATION
DURATION
```

---

## 📊 결과 파일 설명

### data/

```text
teams.json → 캐릭터별 파티
gear.json → 무기 / 성유물
best_orders.json → 최고 DPS 순서
gcsim_legal_actions_all.json → 행동 데이터
```

---

### output/

```text
failed_runs.csv → 실패 캐릭 목록
final_results.csv → 최종 결과
로그 파일
gcsim config 파일
```

---

## 🔥 핵심 알고리즘

```text
1. 파티 고정
2. 순서 모든 경우 생성
3. gcsim 실행
4. DPS 계산
5. 최고 결과 선택
```

---

## 🚀 특징

* 자동 데이터 수집
* 조건 기반 행동 생성
* GA + 시뮬레이션 기반 최적화
* 병렬 처리 지원
* 실패 자동 처리 및 스킵

---

## 📌 한줄 요약

```text
원신 파티와 행동 순서를 자동으로 최적화하는 DPS 분석 엔진
```
을 만들고있는중임니다
