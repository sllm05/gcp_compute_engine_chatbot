#!/usr/bin/env bash
set -e

sudo tee /etc/nginx/sites-available/default > /dev/null <<'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;
    server_name 104.197.81.128.sslip.io 104.197.81.128 _;

    ssl_certificate /etc/letsencrypt/live/104.197.81.128.sslip.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/104.197.81.128.sslip.io/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
EOF

sudo nginx -t
sudo systemctl restart nginx
echo "LETSENCRYPT_NGINX_CONFIGURED"
