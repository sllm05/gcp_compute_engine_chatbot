# Python 3.11 Slim 베이스 이미지
FROM python:3.11-slim

# 표준 출력 즉시 출력 및 파이썬 캐시 비활성화
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# 시스템 패키지 최적화 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스코드 및 정적 웹 리소스 복사
COPY app.py .
COPY static ./static

# Cloud Run 서비스 포트 노출
EXPOSE 8080

# Uvicorn 서버 실행 (Cloud Run 환경에서 ADC 자격 증명 자동 수신)
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}
