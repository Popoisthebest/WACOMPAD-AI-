YEEP Analyzer - React + FastAPI prototype

구성

- `web_server/` : FastAPI 백엔드 (CSV 업로드, 전처리, 모델 호출)
- `frontend/` : React 간단 UI (CSV 업로드 및 결과 표시)

로컬 실행 (macOS, zsh)

권장: 프로젝트 루트에서 Makefile 및 helper 스크립트를 사용하면 한 번에 시작/중지할 수 있습니다.

1. 초기 설치

```bash
# 백엔드 패키지 설치
python3 -m pip install -r web_server/requirements.txt

# 프론트엔드 패키지 설치
cd frontend && npm ci && cd -
```

2. 개발 서버 시작/중지 (간단)

```bash
# 실행 권한 부여 (처음 한 번만)
chmod +x scripts/*.sh
chmod +x ./dev

# 시작 (백엔드 + 프론트엔드) — 기본(백그라운드)
make dev-start

# 시작 및 로그 바로 보기 (한 줄 명령)
./dev

# 또는 Makefile 쇼트컷
make dev-start-foreground

# 중지
make dev-stop
```

3. 즉시 동작 확인 (샘플 스트로크 전송)

```bash
make test-stroke
```

(기존 방식)

```bash
# 백엔드 직접 실행 (venv가 있는 경우)
cd web_server
# venv가 있으면 아래 명령 사용
./venv/bin/python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

# 프론트엔드
cd frontend
npm start
```

설명

- 업로드된 CSV는 `web_server/uploads/`에 저장됩니다.
- `analysis_runner.py`가 전처리 및 모델 로드를 시도하고 JSON 결과를 반환합니다.
- 모델-스케일러 버전 불일치로 인해 예측이 제한될 수 있습니다. 이 경우 venv에서 scikit-learn 버전을 모델이 저장된 버전(예: 1.2.2)으로 변경하거나 제공된 패치 스크립트를 사용하세요.

설명

- 업로드된 CSV는 `web_server/uploads/`에 저장됩니다.
- `analysis_runner.py`가 전처리 및 모델 로드를 시도하고 JSON 결과를 반환합니다.
- 모델-스케일러 버전 불일치로 인해 예측이 제한될 수 있습니다. 이 경우 venv에서 scikit-learn 버전을 모델이 저장된 버전(예: 1.2.2)으로 변경하세요.
