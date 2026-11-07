#!/usr/bin/env bash
# One-time setup for the Claim 3 macrobenchmarks inside the Ubuntu 16.04.6 guest.
#
# Installs Redis 4.0.8 (the paper's version) from source when reachable, plus
# Apache, Nginx and `ab`. Nginx is moved to port 8080 so it can coexist with
# Apache on port 80.
set -euo pipefail

SUDO="sudo"
if [[ $EUID -eq 0 ]]; then SUDO=""; fi

export DEBIAN_FRONTEND=noninteractive
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq build-essential curl ca-certificates \
    apache2 apache2-utils nginx redis-tools

REDIS_VERSION="4.0.8"
REDIS_PREFIX="/opt/redis-${REDIS_VERSION}"
if [[ ! -x "${REDIS_PREFIX}/src/redis-server" ]]; then
  if curl -fsSL "https://download.redis.io/releases/redis-${REDIS_VERSION}.tar.gz" -o /tmp/redis.tgz; then
    tar -xzf /tmp/redis.tgz -C /tmp
    make -C "/tmp/redis-${REDIS_VERSION}" -j"$(nproc)" >/tmp/redis-build.log 2>&1
    $SUDO mkdir -p /opt
    $SUDO rm -rf "$REDIS_PREFIX"
    $SUDO cp -r "/tmp/redis-${REDIS_VERSION}" "$REDIS_PREFIX"
    echo "built redis ${REDIS_VERSION} in ${REDIS_PREFIX}"
  else
    echo "warning: redis ${REDIS_VERSION} download failed; using the distro package" >&2
    $SUDO apt-get install -y -qq redis-server
  fi
fi

# Nginx on 8080; Apache keeps 80.
$SUDO tee /etc/nginx/sites-available/macrobench >/dev/null <<'EOF'
server {
    listen 8080 default_server;
    listen [::]:8080 default_server;
    root /var/www/html;
    index index.html index.htm;
    server_name _;
    location / { try_files $uri $uri/ =404; }
}
EOF
$SUDO rm -f /etc/nginx/sites-enabled/default
$SUDO ln -sf /etc/nginx/sites-available/macrobench /etc/nginx/sites-enabled/macrobench

$SUDO systemctl restart apache2 nginx
$SUDO systemctl enable apache2 nginx >/dev/null 2>&1 || true

echo "--- installed ---"
apache2 -v | head -1
nginx -v 2>&1 | head -1
if [[ -x "${REDIS_PREFIX}/src/redis-server" ]]; then
  "${REDIS_PREFIX}/src/redis-server" --version
else
  redis-server --version
fi
ab -V 2>&1 | head -1
