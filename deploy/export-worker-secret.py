"""Copy gateway credential over IAP into a private local file; print path only.

Use the resulting file as a secret manager / Worker CLI stdin source. Never
commit it, put it in browser environment variables, or paste its contents.
"""
import os
import subprocess
from pathlib import Path

result = subprocess.run([
    '/opt/homebrew/bin/gcloud', 'compute', 'ssh', 'unsc-v12-runner',
    '--zone', 'asia-south1-c', '--project', 'third-technique-504821-m4',
    '--tunnel-through-iap', '--command',
    'sudo cat /etc/swarm-observatory/backend.env',
], check=True, capture_output=True, text=True)
values = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
dest = Path.home() / '.codex/secrets/swarm-observatory'
dest.mkdir(mode=0o700, parents=True, exist_ok=True)
os.chmod(dest, 0o700)
path = dest / 'api-token'
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, 'w') as f:
    f.write(values['SWARM_API_TOKEN'])
os.chmod(path, 0o600)
print(path)
