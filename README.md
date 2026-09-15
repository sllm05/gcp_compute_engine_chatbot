# GCP Compute Engine 기반 Gemini 3.8 / 3.7 Flash 챗봇

Google Gemini 공식 웹 인터페이스 스타일을 완벽하게 반영한 **Gemini 3.8 Flash**(기본) 및 **Gemini 3.7 Flash** 기반 실시간 대화형 AI 웹 챗봇입니다.

---

## ✨ 주요 기능

1. **Gemini 3.8 Flash & 3.7 Flash 듀얼 모델 지원**
   - 최신 고속 지능형 모델인 `Gemini 3.8 Flash`가 기본 설정되어 있습니다.
   - 입력창 우측의 `Flash ⌵` 드롭다운 메뉴를 통해 언제든지 `Gemini 3.7 Flash`로 전환하여 대화할 수 있습니다.
2. **실시간 Google 웹 검색 (Google Search Grounding)**
   - 실시간 웹 검색 도구가 기본 활성화되어 있어 최신 뉴스, 날씨, 환율, 주가 및 실시간 이슈에 대해 정확하고 신뢰성 높은 최신 정보를 제공합니다.
   - 검색에 참조된 실시간 검색 키워드와 웹 출처(링크)가 답변 하단에 자동으로 표시됩니다.
   - 입력창 우측의 지구본(🌐) 아이콘 버튼을 통해 실시간 검색 기능을 켜거나 끌 수 있습니다.
3. **Gemini 웹 공식 UI 스타일 재현**
   - 부드러운 블루-바이올렛 확산 래디얼 글로우 배경
   - 중앙 `"무엇을 도와드릴까요?"` 히어로 타이틀
   - 알약(Pill)형 플로팅 입력 바, 추천 메뉴(`+`), 마이크 음성 입력(Web Speech API)
4. **실시간 타이핑 스트리밍 (Server-Sent Events)**
   - 글자/단어 단위로 실시간 스트리밍되어 빠르고 자연스러운 응답 경험을 제공합니다.
5. **마크다운 & 코드 구문 강조 (Syntax Highlighting)**
   - 코드 블록 언어 태그 표시 및 원클릭 복사 버튼 제공
   - 수식, 리스트, 테이블 지원
6. **대화 기록 관리 & 멀티턴 맥락 유지**
   - 이전 질의응답을 기억하여 이어지는 대화 흐름 지원
   - 로컬 스토리지를 통한 최근 대화 목록 저장/불러오기/삭제 기능
7. **다크 모드 & 반응형 지원**
   - 우측 상단 테마 토글 버튼을 통해 라이트/다크 모드 자유 전환

---

## 🛠️ 사전 준비 (Prerequisites)

- Python 3.10 이상
- Gemini API Key (환경변수 `GEMINI_API_KEY`)

```bash
# Windows PowerShell 환경변수 설정 예시
$env:GEMINI_API_KEY="your-gemini-api-key-here"

# Linux / macOS 환경변수 설정 예시
export GEMINI_API_KEY="your-gemini-api-key-here"
```

---

## 🚀 로컬 실행 방법

### 방법 1. 원클릭 실행 (Windows)
- `run.bat` 또는 `run.ps1` 파일을 더블클릭하거나 PowerShell에서 실행합니다:
```powershell
.\run.ps1
```

### 방법 2. 일반 실행
```bash
pip install -r requirements.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

브라우저에서 `http://localhost:8000`으로 접속합니다.

---

## ☁️ Google Cloud Platform (GCP) Compute Engine 배포 가이드

### 1. Compute Engine 인스턴스 생성
- OS: Ubuntu 22.04 LTS / Debian 12 (권장)
- 머신 유형: `e2-micro` 또는 `e2-small` (초경량 구동 가능)
- 방화벽: **HTTP 트래픽 허용**, **HTTPS 트래픽 허용** 체크

### 2. 인스턴스 SSH 접속 후 환경 설정
```bash
# 패키지 업데이트 및 필수 패키지 설치
sudo apt update && sudo apt install -y python3-pip git

# 프로젝트 클론 및 디렉터리 이동
git clone <repository-url> chatbot
cd chatbot

# 의존성 설치
pip3 install -r requirements.txt
```

### 3. 환경변수 등록 및 백그라운드 서비스(systemd) 구성
```bash
# systemd 서비스 파일 생성
sudo nano /etc/systemd/system/gemini-chatbot.service
```

아래 내용을 입력합니다 (`GEMINI_API_KEY`와 작업 경로를 수정):
```ini
[Unit]
Description=Gemini 3.8/3.7 Flash Chatbot Web Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/chatbot
Environment="GEMINI_API_KEY=your-gemini-api-key-here"
ExecStart=/usr/local/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

서비스 활성화 및 시작:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gemini-chatbot
sudo systemctl start gemini-chatbot
sudo systemctl status gemini-chatbot
```

### 4. GCP 방화벽 규칙 추가 (8000번 포트 또는 Nginx 80번 프록시)
- GCP 콘솔 > **VPC 네트워크** > **방화벽** > **방화벽 규칙 만들기**
  - 대상 태그: `http-server`
  - 소스 IPv4 범위: `0.0.0.0/0`
  - 프로토콜 및 포트: `tcp:8000` (또는 Nginx 리버스 프록시 적용 시 80 포트 그대로 이용)
