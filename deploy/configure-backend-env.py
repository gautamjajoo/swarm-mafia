"""Run with sudo remotely; preserve secret and configure service environment."""
import os
from pathlib import Path
p = Path('/etc/swarm-observatory/backend.env')
values = dict(line.split('=', 1) for line in p.read_text().splitlines() if '=' in line)
values.update({
    'OBSERVATORY_API_TOKEN': values['SWARM_API_TOKEN'],
    'OBSERVATORY_DB': '/home/jajoo_kairosity_ai/swarm-observatory/data/evidence.sqlite',
    'VERTEX_MODEL': 'gemini-3.5-flash',
})
fd = os.open(p, os.O_WRONLY | os.O_TRUNC, 0o600)
with os.fdopen(fd, 'w') as f:
    for key, value in values.items():
        f.write(f'{key}={value}\n')
os.chmod(p, 0o600)
print('Backend environment configured; secrets not displayed.')
