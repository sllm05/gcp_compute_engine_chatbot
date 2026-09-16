# GCP Compute Engine 기반 Gemini 3.8 / 3.7 Flash 챗봇

Google Gemini 공식 웹 인터페이스 스타일을 완벽하게 반영한 **Gemini 3.8 Flash**(기본) 및 **Gemini 3.7 Flash** 기반 실시간 대화형 AI 웹 챗봇입니다.  
GCP Compute Engine 가상머신에 배포되어 있으며, **GCP Secret Manager**와 **Let's Encrypt 공인 SSL/TLS 인증서**를 적용하여 안전한 **Pure HTTPS** 환경에서 서비스됩니다.

---

## 🌐 서비스 접속 URL

- **공인 HTTPS 서비스 주소**: [https://104.197.81.128.sslip.io](https://104.197.81.128.sslip.io) *(Let's Encrypt 공인 인증, 보안 경고 없음)*
- **운영 상태**: 비암호화 HTTP(80, 8000) 완전 차단, **HTTPS(443) 단독 보안 운영**

---

## ✨ 주요 기능

1. **Gemini 3.8 Flash & 3.7 Flash 듀얼 모델 지원**
   - 최신 고속 지능형 모델인 `Gemini 3.8 Flash`가 기본 설정되어 있습니다.
   - 입력창 우측 드롭다운 메뉴를 통해 언제든지 `Gemini 3.7 Flash`로 전환하여 대화할 수 있습니다.
2. **실시간 Google 웹 검색 (Google Search Grounding)**
   - 최신 뉴스, 날씨, 환율, 주가 등 실시간 정보 질의 시 Google Search Grounding을 통해 실시간 웹 출처와 링크를 자동 제공합니다.
3. **Gemini 웹 공식 UI 스타일 재현**
   - 부드러운 블루-바이올렛 글로우 배경, 중앙 히어로 타이틀, 플로팅 입력 바, 추천 프롬프트, 마이크 음성 인식(Web Speech API) 지원
4. **실시간 타이핑 스트리밍 (Server-Sent Events)**
   - 글자/단어 단위로 실시간 스트리밍되어 빠르고 자연스러운 응답 경험을 제공합니다.
5. **GCP Secret Manager 안전 연동**
   - API 키를 소스코드나 로컬 파일에 하드코딩하지 않고 GCP Secret Manager(`projects/108335720396/secrets/GEMINI_API_KEY`)에서 직접 로드하여 보안을 극대화했습니다.

---

## 🔒 HTTP vs HTTPS 프로토콜 차이와 전환 기술 아키텍처

본 프로젝트는 초기 개발 및 테스트 단계에서는 **HTTP (포트 8000 / 80)**로 구현되었으나, 보안 강화 및 브라우저 호환성을 위해 **공인 HTTPS (포트 443)** 단독 운영 환경으로 전환되었습니다.

### 1. HTTP와 HTTPS의 핵심 차이점

| 비교 항목 | HTTP (HyperText Transfer Protocol) | HTTPS (HTTP Secure / TLS) |
| :--- | :--- | :--- |
| **통신 암호화** | **평문(Plaintext) 전송** (암호화 없음) | **대칭키/비대칭키 혼합 암호화 (TLS 1.2/1.3)** |
| **보안성** | 네트워크 도청, 패킷 변조, 중간자 공격(MitM)에 취약 | 전송 구간 전체 암호화로 도청 및 데이터 변조 불가 |
| **서버 인증** | 접속한 서버가 실제 정당한 서버인지 검증 불가 | 공인 인증기관(CA)의 전자서명을 통해 서버 진위 보증 |
| **기본 포트** | `TCP 80` (또는 개발용 8000, 8080) | `TCP 443` |
| **브라우저 표시** | "주의 요함" / "보안되지 않음" 경고 표시 | **안전한 자물쇠 아이콘(Secure Connection)** 표시 |
| **브라우저 최신 API** | 마이크(Web Speech API), 위치 정보 등 핵심 API 차단 | **마이크 음성 입력, 최신 웹 보안 API 정상 작동** |

### 2. AI 챗봇 서비스에서 HTTPS가 필수적인 이유

1. **사용자 프라이버시 및 대화 데이터 보호**:
   - 사용자가 챗봇에 입력하는 질문(개인정보, 업무 질의, 민감한 텍스트)이 평문 HTTP로 전송되면 공용 Wi-Fi나 네트워크 경로상에서 쉽게 도청될 수 있습니다. HTTPS는 이를 강력하게 암호화합니다.
2. **마이크 음성 입력(Web Speech API) 구동 조건**:
   - Chrome, Edge, Safari 등 최신 모던 브라우저는 보안 정책상 `HTTPS`(또는 localhost) 환경이 아닐 경우 마이크 장치 접근 권한을 원천 차단합니다. 챗봇의 마이크 음성 대화 기능을 사용하려면 HTTPS가 필수적입니다.
3. **API 토큰 및 인증 탈취 방지**:
   - 서버와 클라이언트 간 통신 헤더 및 데이터 변조를 차단하여 세션 및 자격 증명을 안전하게 유지합니다.

---

### 3. HTTP에서 HTTPS로 전환하기 위해 사용된 기술 스택

HTTP에서 브라우저 경고 없는 공인 HTTPS로 완벽히 전환하기 위해 다음 5가지 핵심 엔지니어링 기술이 적용되었습니다:

```
[사용자 브라우저]
       │ (HTTPS / TLSv1.3 암호화 통신 - 포트 443)
       ▼
[GCP VPC Firewall]  ───▶ (tcp:80, tcp:8000 완전 차단 / tcp:443만 허용)
       │
       ▼
[Nginx Reverse Proxy]
  ├─ Let's Encrypt 공인 SSL 인증서 바인딩 (104.197.81.128.sslip.io)
  ├─ HSTS 보안 헤더 (Strict-Transport-Security)
  ├─ SSE 실시간 스트리밍 버퍼링 해제 (proxy_buffering off)
       │ (내부 루프백 127.0.0.1:8000 프록시 전달)
       ▼
[Uvicorn / FastAPI Backend] 
  ├─ GCP Secret Manager에서 GEMINI_API_KEY 주입
  └─ Gemini 3.8 / 3.7 Flash 모델 서빙
```

#### ① Dynamic Wildcard DNS (`sslip.io`)
- **문제점**: Let's Encrypt 등 글로벌 공인 CA(인증기관)는 정책상 단순 공인 IP(`104.197.81.128`)에 대해 무료 도메인 인증서를 발급하지 않습니다.
- **해결 기술**: IP 주소 자체를 서브도메인으로 해석하는 매직 DNS 기술인 `sslip.io`를 활용하여 `104.197.81.128.sslip.io`라는 유효한 FQDN 도메인을 생성하고 IP에 자동 매핑했습니다.

#### ② Let's Encrypt 공인 CA & Certbot 자동화
- 자체 서명(Self-signed) 인증서 사용 시 발생하는 브라우저의 `NET::ERR_CERT_AUTHORITY_INVALID` 경고를 제거하기 위해, 전 세계 모든 브라우저가 신뢰하는 루트 CA인 **Let's Encrypt**를 도입했습니다.
- `certbot` 및 `python3-certbot-nginx` 플러그인을 사용하여 도메인 소유권 검증(HTTP-01 Challenge)을 거쳐 정식 공인 SSL 인증서를 발급받고, systemd 타이머를 통한 90일 주기 자동 갱신 체계를 구축했습니다.

#### ③ Nginx SSL/TLS 듀얼 프록시 및 최적화
- Nginx에 `listen 443 ssl` 리스너를 설정하고 발급받은 `fullchain.pem` 및 `privkey.pem`을 바인딩했습니다.
- **TLS 1.2 / TLS 1.3** 및 안전한 암호화 알고리즘(`ciphers HIGH:!aNULL:!MD5`)을 적용했습니다.
- **SSE 스트리밍 최적화**: Nginx의 기본 응답 버퍼링이 켜져 있으면 실시간 타이핑 스트리밍이 뭉쳐서 한 번에 출력되는 문제가 발생하므로, `proxy_buffering off;` 설정을 통해 Gemini AI 답변이 글자 단위로 실시간 전송되도록 최적화했습니다.

#### ④ HSTS (HTTP Strict Transport Security) 보안 강제
- `Strict-Transport-Security "max-age=31536000; includeSubDomains"` 헤더를 적용하여 브라우저가 첫 방문 이후에는 사용자가 `http://`로 입력하더라도 클라이언트 단에서 자동으로 `https://` 연결을 강제하도록 설정했습니다.

#### ⑤ GCP 클라우드 방화벽(VPC Firewall) 포트 통제
- 기존의 평문 HTTP 포트(`tcp:80`) 및 백엔드 직접 노출 포트(`tcp:8000`) 규칙을 클라우드 콘솔/CLI에서 **완전히 삭제 및 차단**했습니다.
- 외부 인터넷에서는 오직 `tcp:443 (HTTPS)` 포트 하나만을 통해서만 인스턴스에 접근할 수 있도록 네트워크 경계를 단일화(Pure HTTPS)했습니다.

---

## 🛠️ 사전 준비 (Prerequisites)

- Python 3.10 이상
- GCP Secret Manager 권한이 있는 GCP 서비스 계정 또는 로컬 환경변수 `GEMINI_API_KEY`

```bash
# 로컬 개발 시 환경변수 설정 예시
$env:GEMINI_API_KEY="your-gemini-api-key-here"  # Windows PowerShell
export GEMINI_API_KEY="your-gemini-api-key-here" # Linux/macOS
```

---

## 🚀 로컬 실행 방법

### 방법 1. 원클릭 실행 (Windows)
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

## ☁️ Google Cloud Platform (GCP) Compute Engine 배포 아키텍처

주피터 노트북([compute_engine_example.ipynb](compute_engine_example.ipynb))에 정의된 최저가 단가 분석 결과를 바탕으로 `us-central1-a` 리전에 인스턴스가 프로비저닝되었습니다.

- **인스턴스명**: `gemini-chatbot-vm`
- **머신 유형**: `e2-medium` (2 vCPU, 4GB Memory)
- **운영체제**: Debian 13 (Trixie)
- **디스크**: 10GB `pd-balanced` + 스케줄 스냅샷 정책(`default-schedule-1`)
- **모니터링**: Google Cloud Ops Agent 정책 자동 배포 (`config.yaml`)
- **서비스 매니저**: Linux `systemd` (`gemini-chatbot.service` 자동 재시작 구성)
- **로그 파일**: 전체 배포 및 인프라 전환 이력은 [deployment_process.log](deployment_process.log)에 실시간으로 보존됩니다.
