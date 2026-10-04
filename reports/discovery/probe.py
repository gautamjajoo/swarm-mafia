"""Bounded read-only Observatory discovery; never prints the credential."""
import json,os,sys,re,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'clients'))
from observatory_client.api import ObservatoryAPI,ClientError
os.environ['OBSERVATORY_API_URL']='https://swarm-observatory.34.93.205.17.sslip.io'
os.environ['OBSERVATORY_API_TOKEN_FILE']=str(Path.home()/'.codex/secrets/swarm-observatory/api-token')
api=ObservatoryAPI.from_env(); root=Path(__file__).parent

def clean(v):
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
 if isinstance(v,list):return [clean(x) for x in v]
 if isinstance(v,str):
  v=re.sub(r'\b(?:sk-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{25,}|ya29\.[A-Za-z0-9_.-]+)\b','[REDACTED_CREDENTIAL]',v)
  v=re.sub(r'(?i)(\b(?:password|api[_ -]?key|access[_ -]?token|bearer)\b\s*[:=]\s*)[^\s,;"\']+',r'\1[REDACTED_CREDENTIAL]',v)
 return v
for spec in json.loads(sys.argv[1]):
 label=spec.pop('label'); method=spec.pop('method','search'); start=time.monotonic()
 try:
  r=clean(getattr(api,method)(**spec)) if method!='request' else clean(api.request(**spec))
  (root/'packets'/f'{label}.json').write_text(json.dumps(r,indent=2))
  rows=r.get('data',[]); rows=rows.get('records',rows) if isinstance(rows,dict) else rows
  print('\nQUERY',label,json.dumps(spec),'truncated',r.get('truncated'),'next',r.get('next_cursor'))
  if isinstance(rows,list):
   for row in rows:
    print(json.dumps({k:row.get(k) for k in ('id','timestamp','actor_name','action_type')},ensure_ascii=False),str(row.get('excerpt',''))[:1100].replace('\n',' '))
  else: print(json.dumps(rows,ensure_ascii=False)[:4000])
  log={'label':label,'method':method,'params':spec,'seconds':round(time.monotonic()-start,3),'returned':len(rows) if isinstance(rows,list) else None,'truncated':r.get('truncated'),'next_cursor':r.get('next_cursor'),'coverage_complete':r.get('coverage',{}).get('complete'),'snapshot':r.get('snapshot')}
 except ClientError as e:
  log={'label':label,'method':method,'params':spec,'error':e.as_dict(),'seconds':round(time.monotonic()-start,3)};print(json.dumps(log))
 with (root/'query-log.jsonl').open('a') as f:f.write(json.dumps(log)+'\n')
