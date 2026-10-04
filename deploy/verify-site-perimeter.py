"""Read-only perimeter checks; no cookies, credentials, data, or response bodies logged."""
import concurrent.futures
import datetime
import json
import urllib.error
import urllib.parse
import urllib.request

ORIGIN = 'https://kairosity-observatory.gautamjajoo.chatgpt.site'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

CASES = [
    ('GET', '/api/evidence/stats', None, 'none'),
    ('GET', '/api/investigations', None, 'none'),
    ('GET', '/api/investigations/nonexistent', None, 'none'),
    ('POST', '/api/investigations', b'', 'empty'),
    ('POST', '/api/investigations', b'{', 'invalid-json'),
    ('PUT', '/api/investigations/nonexistent', b'{', 'invalid-json'),
]

def check(case, spoofed, with_origin):
    method, path, body, body_kind = case
    headers = {'User-Agent': 'Swarm-Observatory-Perimeter-Verification/1.0'}
    if body is not None:
        headers['Content-Type'] = 'application/json'
    if spoofed:
        headers['oai-authenticated-user-id'] = 'perimeter-probe-not-a-real-user'
    if with_origin:
        headers['Origin'] = ORIGIN
    request = urllib.request.Request(ORIGIN + path, method=method, data=body, headers=headers)
    opener = urllib.request.build_opener(NoRedirect())
    try:
        response = opener.open(request, timeout=30)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        status = response.status
        content_type = response.headers.get('Content-Type', '').split(';')[0]
        location = urllib.parse.urlsplit(response.headers.get('Location', ''))
        # Do not follow redirects or print response content, cookies, or queries.
        body_size = len(response.read(262144))
    login_redirect = status in (301, 302, 303, 307, 308) and (
        location.hostname in ('chatgpt.com', 'auth.openai.com', 'auth0.openai.com')
        or any(part in location.path.lower() for part in ('login', 'signin', 'oauth', 'authorize')))
    return {'method': method, 'path': path, 'body_kind': body_kind,
            'spoofed_identity': spoofed, 'origin_present': with_origin,
            'status': status, 'content_type': content_type,
            'body_bytes_observed': body_size, 'login_redirect': bool(login_redirect),
            'denied': status in (401, 403) or login_redirect}

if __name__ == '__main__':
    combinations = [(case, spoofed, origin) for case in CASES
                    for spoofed in (False, True) for origin in (False, True)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(check, *args) for args in combinations]
        results = [future.result() for future in futures]
    report = {'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'origin': ORIGIN, 'requests': len(results),
              'all_denied': all(row['denied'] for row in results), 'results': results}
    print(json.dumps(report, indent=2))
    if not report['all_denied']:
        raise SystemExit('Perimeter verification failed; response bodies withheld.')
