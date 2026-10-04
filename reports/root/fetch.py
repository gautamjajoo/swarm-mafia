import json,urllib.request,urllib.parse
from pathlib import Path
BASE='https://swarm-observatory.34.93.205.17.sslip.io/v1/'
def fetch(path,params=None,name=None):
    token=Path('/Users/gautamjajoo/.codex/secrets/swarm-observatory/api-token').read_text().strip()
    req=urllib.request.Request(BASE+path+('?' + urllib.parse.urlencode(params) if params else ''),headers={'Authorization':'Bearer '+token})
    with urllib.request.urlopen(req,timeout=180) as f:r=json.load(f)
    if name:Path('reports/root/'+name+'.json').write_text(json.dumps(r,indent=2))
    return r
if __name__=='__main__':
    jobs=[('search',{'q':'AI Republic','table':'chat_messages','from':'2026-08-01T00:00:00Z','to':'2026-09-05T00:00:00Z','limit':100},'identity_search'),('context',{'seed':'chat_messages:c2ead9f2-4c0a-4a05-b56d-e7b0334e50fe','before':15,'after':15},'identity_context'),('search',{'q':'contaminated','table':'chat_messages','from':'2026-08-01T00:00:00Z','to':'2026-09-05T00:00:00Z','limit':50},'identity_contamination')]
    for path,p,name in jobs:
        r=fetch(path,p,name); rows=r['data']['records'] if path=='context' else r['data']
        print(json.dumps({'name':name,'truncated':r.get('truncated'),'next_cursor':r.get('next_cursor'),'rows':[{'id':x['id'],'actor':x.get('actor_name'),'timestamp':x.get('timestamp'),'text':x['excerpt'][:1800]} for x in rows]}))
