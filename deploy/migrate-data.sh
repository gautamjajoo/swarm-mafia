#!/usr/bin/env bash
set -euo pipefail
# Run only after the ingestion owner confirms all product writers have stopped.
src=/home/jajoo_kairosity_ai/swarm-observatory/data
dst=/srv/swarm-observatory/data
mountpoint -q /srv/swarm-observatory
test -d "$src"
test ! -L "$src"
test -f "$src/evidence.sqlite"
sudo systemctl stop swarm-observatory.service
python3 - <<'PY'
import sqlite3
p='/home/jajoo_kairosity_ai/swarm-observatory/data/evidence.sqlite'
with sqlite3.connect(p, timeout=30) as db:
    status=db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
    if status[0] != 0:
        raise SystemExit('Active database writer remains; cutover aborted.')
    if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
        raise SystemExit('Source database failed consistency check.')
PY
rsync -a --delete "$src/" "$dst/"
test -z "$(rsync -anic --delete "$src/" "$dst/")"
python3 - <<'PY'
import sqlite3
p='/srv/swarm-observatory/data/evidence.sqlite'
with sqlite3.connect('file:'+p+'?mode=ro', uri=True) as db:
    if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
        raise SystemExit('Destination database failed consistency check.')
print('Source and destination verified; snapshot bytes match.')
PY
backup="${src}.boot-copy-$(date -u +%Y%m%dT%H%M%SZ)"
mv "$src" "$backup"
ln -s "$dst" "$src"
chmod 700 "$dst"
sudo install -m 644 ~/swarm-deploy/swarm-observatory.service ~/swarm-deploy/swarm-observatory-backup.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start swarm-observatory.service
sudo systemctl is-active swarm-observatory.service
printf 'Original data preserved at %s\n' "$backup"
df -h / /srv/swarm-observatory
