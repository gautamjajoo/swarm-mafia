#!/usr/bin/env bash
set -euo pipefail
# Run on the target VM as the SSH user; only dedicated service paths are changed.
src="$(cd "$(dirname "$0")" && pwd)"
sudo install -d -m 700 /etc/swarm-observatory
sudo python3 - <<'PY'
import os, secrets
p='/etc/swarm-observatory/backend.env'
if not os.path.exists(p):
    fd=os.open(p, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write('SWARM_API_TOKEN='+secrets.token_urlsafe(48)+'\n')
        f.write('GOOGLE_CLOUD_PROJECT=third-technique-504821-m4\n')
        f.write('GOOGLE_CLOUD_LOCATION=global\n')
        f.write('VERTEX_MODEL=gemini-3.5-flash\n')
PY
if ! id swarm-caddy >/dev/null 2>&1; then
  sudo useradd --system --home-dir /var/lib/swarm-caddy --shell /usr/sbin/nologin swarm-caddy
fi
if ! test -x /usr/local/bin/swarm-caddy; then
  download="$(mktemp /tmp/swarm-caddy.XXXXXX)"
  trap 'rm -f "$download"' EXIT
  curl --fail --silent --show-error --location 'https://caddyserver.com/api/download?os=linux&arch=amd64' -o "$download"
  sudo install -m 755 "$download" /usr/local/bin/swarm-caddy
  rm "$download"
  trap - EXIT
fi
sudo install -m 600 "$src/Caddyfile" /etc/swarm-observatory/Caddyfile
# Caddyfile contains only an environment reference; no credential in its contents.
sudo chown root:swarm-caddy /etc/swarm-observatory
sudo chmod 750 /etc/swarm-observatory
sudo chown root:swarm-caddy /etc/swarm-observatory/Caddyfile
sudo chmod 640 /etc/swarm-observatory/Caddyfile
sudo install -m 644 "$src/swarm-caddy.service" /etc/systemd/system/swarm-caddy.service
sudo systemctl daemon-reload
sudo systemctl enable --now swarm-caddy.service
sudo systemctl is-active swarm-caddy.service
