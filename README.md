# GCP Compute Engine 기반 Gemini 3.8 / 3.7 Flash 챗봇

Google Gemini 공식 웹 UI 스타일을 완벽하게 구현한 **Gemini 3.8 Flash**(기본) 및 **Gemini 3.7 Flash** 듀얼 모델 실시간 대화형 AI 웹 챗봇 프로젝트입니다.  
GCP Compute Engine 배포 관련 전체 소스코드와 자산들이 `compute_engine/` 디렉터리에 모듈화되어 있습니다.

---

## 📁 디렉터리 구조

```text
gcp_compute_engine_chatbot/
├── .gitignore                          # Git 무시 규칙 (보안 키, 가상환경, 로그 등)
├── README.md                           # 루트 프로젝트 안내 (본 문서)
├── run.bat                             # 루트 편의 실행 배치 파일 (compute_engine 챗봇 실행)
├── run.ps1                             # 루트 편의 실행 PowerShell 스크립트
└── compute_engine/                     # ⭐ Google Compute Engine 배포 및 애플리케이션 모듈
    ├── README.md                       # Compute Engine 상세 아키텍처 및 설정 가이드
    ├── app.py                          # FastAPI 백엔드 (Gemini 3.8/3.7 Flash, SSE 스트리밍, 웹검색)
    ├── requirements.txt                # 파이썬 의존성 패키지 목록
    ├── config.yaml                     # Google Cloud Ops Agent VM 모니터링 정책 설정
    ├── deploy_to_compute_engine.py     # Compute Engine 인스턴스 생성 및 자동 배포 스크립트
    ├── compute_engine_example.ipynb    # GCP 전 세계 리전 실시간 최저가 분석 및 VM 프로비저닝 노트북
    ├── login_gcp.bat                   # GCP 계정 로그인 및 프로젝트 설정 스크립트
    ├── run.bat                         # compute_engine 폴더 내 로컬 실행 배치 스크립트
    ├── run.ps1                         # compute_engine 폴더 내 로컬 실행 PowerShell 스크립트
    ├── deployment_process.log          # Compute Engine 배포 및 작업 로그
    ├── static/                         # 챗봇 웹 프론트엔드 (Gemini 공식 UI 재현)
    │   ├── index.html                  # 메인 웹 페이지
    │   ├── style.css                   # 반응형 스타일시트 (글로우 효과, 다크 테마)
    │   └── app.js                      # SSE 스트리밍 처리, 모델 전환, 음성 인식(STT)
    └── scripts/                        # Compute Engine VM 인스턴스 보안 및 웹서버 설정 스크립트
        ├── README.md                   # VM 스크립트 사용 가이드
        ├── only_https.sh               # Pure HTTPS(443) 단독 서비스 설정 (HTTP 완전 차단)
        ├── redirect_to_https.sh        # HTTP(80) ➡️ HTTPS(443) 301 자동 리다이렉트 설정
        ├── apply_letsencrypt.sh        # Let's Encrypt 공인 SSL 인증서 Nginx 바인딩
        ├── setup_nginx.sh              # Nginx 리버스 프록시 초기 설치 스크립트
        └── setup_ssl.sh                # 자체 서명 SSL 인증서 테스트 스크립트
```

---

## 🚀 로컬 실행 방법

### 방법 1. 루트 디렉터리에서 바로 실행
루트 경로에서 편의 스크립트를 실행하면 자동으로 `compute_engine/` 디렉터리로 이동하여 챗봇을 실행합니다.

```powershell
# PowerShell
.\run.ps1
```
```cmd
:: CMD
run.bat
```

### 방법 2. `compute_engine/` 디렉터리에서 직접 실행
```bash
cd compute_engine
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

서버 기동 후 웹 브라우저에서 `http://localhost:8000`으로 접속합니다.

---

## ☁️ Google Cloud Platform (GCP) Compute Engine 배포

Compute Engine 배포 스크립트는 `compute_engine/` 폴더 내의 백엔드, 프론트엔드, 설정 및 스크립트를 자동으로 패키징하여 VM 인스턴스(`/opt/gemini-chatbot`)에 배포합니다.

### 배포 스크립트 실행
```powershell
# 루트 디렉터리에서 실행 시
python compute_engine/deploy_to_compute_engine.py

# 또는 compute_engine 디렉터리로 이동 후 실행 시
cd compute_engine
python deploy_to_compute_engine.py
```

자세한 VM 사양, Secret Manager 연동, Nginx 리버스 프록시, Let's Encrypt 공인 SSL 적용 절차는 **[compute_engine/README.md](compute_engine/README.md)**를 참고하세요.
