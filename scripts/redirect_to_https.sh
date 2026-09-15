#!/usr/bin/env bash
set -e

echo '[1/2] Nginx HTTP -> HTTPS 301 영구 리다이렉트 및 SSL HSTS 설정 적용...'
sudo tee /etc/nginx/sites-available/default > /dev/null <<'EOF'
# 1. HTTP(80) 모든 요청을 HTTPS로 301 영구 리다이렉트
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    return 301 https://104.197.81.128.sslip.io$request_uri;
}

# 2. HTTPS(443) 보안 서비스 및 IP 접속 시 도메인 리다이렉트
server {
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;
    server_name 104.197.81.128.sslip.io 104.197.81.128 _;

    ssl_certificate /etc/letsencrypt/live/104.197.81.128.sslip.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/104.197.81.128.sslip.io/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS 보안 헤더 추가 (브라우저에 항상 HTTPS 접속 강제)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 숫자 IP로 HTTPS 접속 시 공인 SSL 도메인으로 리다이렉트
    if ($host = "104.197.81.128") {
        return 301 https://104.197.81.128.sslip.io$request_uri;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;

        # 실시간 SSE 스트리밍 버퍼링 해제
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
EOF

echo '[2/2] Nginx 설정 테스트 및 재시작...'
sudo nginx -t
sudo systemctl restart nginx
echo "HTTP_TO_HTTPS_REDIRECT_SUCCESSFUL"
