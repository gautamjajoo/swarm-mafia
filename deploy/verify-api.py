"""HTTPS/auth smoke tests; credential stays in memory and data is not printed."""
import json
from pathlib import Path
import urllib.error
import urllib.request

origin = 'https://swarm-observatory.34.93.205.17.sslip.io'
token = (Path.home() / '.codex/secrets/swarm-observatory/api-token').read_text().strip()

def check(path, expected, bearer=None):
    headers = {'Authorization': 'Bearer ' + bearer} if bearer else {}
    request = urllib.request.Request(origin + path, headers=headers)
    try:
        response = urllib.request.urlopen(request, timeout=60)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        status = response.status
        body = response.read()
    assert status == expected, f'{path}: expected {expected}, got {status}'
    print(f'{path} auth={"valid" if bearer == token else "invalid" if bearer else "none"} HTTP {status}')
    return body

health = json.loads(check('/health', 200))
assert health == {'status': 'ok'}, 'Health endpoint must not disclose source data'
check('/v1/stats', 401)
check('/v1/stats', 401, 'invalid-credential')
stats = json.loads(check('/v1/stats', 200, token))
assert isinstance(stats, dict), 'Stats response must be an object'
check('/v1/search?limit=101', 422, token)
check('/v1/stats?source=invalid', 400, token)
check('/docs', 401)
print('HTTPS, minimal health, bearer gates, data API, and input validation passed.')
