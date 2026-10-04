"""Tiny paid smoke test using VM identity; never writes tokens or source data."""
import json
import urllib.request

req = urllib.request.Request(
    'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',
    headers={'Metadata-Flavor': 'Google'})
with urllib.request.urlopen(req, timeout=10) as r:
    token = json.load(r)['access_token']
model = 'gemini-3.5-flash'
url = ('https://aiplatform.googleapis.com/v1/projects/third-technique-504821-m4/'
       f'locations/global/publishers/google/models/{model}:generateContent')
body = {'contents': [{'role':'user','parts':[{'text':'Reply with exactly OK.'}]}],
        'generationConfig': {'maxOutputTokens': 64, 'temperature': 0}}
req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
    'Authorization': 'Bearer '+token, 'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=60) as r:
    result = json.load(r)
print(json.dumps({'model': model, 'status': 'ok',
                  'response': [p.get('text') for p in result.get('candidates', [{}])[0].get('content', {}).get('parts', []) if p.get('text')],
                  'usage': result.get('usageMetadata')}))
