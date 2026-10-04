"""Bounded read-only Observatory research helper; never evaluates trace content."""
import json, pathlib, sys, urllib.request, urllib.parse
TOKEN=pathlib.Path.home().joinpath('.codex/secrets/swarm-observatory/api-token').read_text().strip()
BASE='https://swarm-observatory.34.93.205.17.sslip.io'
def get(path, **params):
    params={('from' if k=='from_time' else 'to' if k=='to_time' else k):v for k,v in params.items()}
    req=urllib.request.Request(BASE+'/v1/'+path+'?'+urllib.parse.urlencode(params),headers={'Authorization':'Bearer '+TOKEN})
    with urllib.request.urlopen(req, timeout=90) as r: return json.load(r)
if __name__=='__main__':
    path=sys.argv[1]; params=dict(x.split('=',1) for x in sys.argv[2:]); result=get(path,**params)
    print(json.dumps(result,ensure_ascii=False))
