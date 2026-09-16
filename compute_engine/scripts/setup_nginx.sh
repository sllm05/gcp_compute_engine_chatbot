#!/usr/bin/env bash
set -e

echo '[1/3] Nginx 설치...'
sudo apt-get update -y
sudo apt-get install -y nginx

echo '[2/3] Nginx 리버스 프록시 설정 (포트 80 -> 포트 8000)...'
sudo tee /etc/nginx/sites-available/default > /dev/null <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 및 실시간 스트리밍 버퍼링 해제
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
EOF

echo '[3/3] Nginx 설정 검증 및 재시작...'
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
echo "NGINX_SETUP_SUCCESSFUL"
