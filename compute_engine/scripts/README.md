# GCP Compute Engine VM 설정 스크립트 모음

GCP Compute Engine 인스턴스 환경 구성 및 웹 서버(Nginx) 설정 관리를 위한 쉘 스크립트 모음입니다.

---

## 📁 스크립트 구성 및 역할

| 스크립트 파일명 | 상태 | 설명 |
| :--- | :---: | :--- |
| **`only_https.sh`** | **⭐ 현재 적용 중** | **Pure HTTPS(443) 단독 서비스 설정**<br>- HTTP(80) 포트를 완전히 닫고 Let's Encrypt 공인 SSL이 적용된 HTTPS(443)로만 트래픽 수신<br>- HSTS 보안 헤더 및 SSE 스트리밍 버퍼링 해제 적용 |
| **`redirect_to_https.sh`** | 보관 | **HTTP ➡️ HTTPS 301 자동 리다이렉트 설정**<br>- 80번 포트로 들어온 요청을 `https://104.197.81.128.sslip.io`로 자동 전환 |
| **`apply_letsencrypt.sh`** | 보관 | **Let's Encrypt 공인 인증서 Nginx 바인딩**<br>- `104.197.81.128.sslip.io` 도메인 전용 SSL 인증서(/etc/letsencrypt/) 적용 |
| **`setup_nginx.sh`** | 보관 | **초기 Nginx 리버스 프록시 설치 스크립트**<br>- Nginx 설치 및 80 ➡️ 8000 기본 프록시 설정 |
| **`setup_ssl.sh`** | 보관 | **초기 자체 서명(Self-signed) SSL 테스트 스크립트**<br>- OpenSSL 기반 자체 서명 인증서 생성 테스트용 |

---

## 🚀 사용 방법 (Compute Engine VM 내부 실행)

```bash
# 실행 권한 부여 후 실행
chmod +x scripts/only_https.sh
./scripts/only_https.sh
```
