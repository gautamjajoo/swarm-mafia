import json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'clients'))
from observatory_client.api import ObservatoryAPI
os.environ['OBSERVATORY_API_URL']='https://swarm-observatory.34.93.205.17.sslip.io'
os.environ['OBSERVATORY_API_TOKEN_FILE']=str(Path.home()/'.codex/secrets/swarm-observatory/api-token')
a=ObservatoryAPI.from_env(); out=[]
for canonical in sys.argv[1:]:
 table,ident=canonical.split(':',1); r=a.record(table,ident,raw=True);d=r['data']
 x={'id':canonical,'hash_verified':d['hash_verified'],'raw_truncated':r['truncated'],'provenance':d['provenance']}
 if not r['truncated']:
  row=json.loads(d['raw_json']); x['source_keys']=list(row)
  fields=('agent_action','output','error','session_id') if table=='computer_use_turns' else tuple(k for k in row if k not in ('session_goal','agent_id','id'))
  x['inspected_fields']={k:row.get(k) for k in fields}
  for k,v in list(x['inspected_fields'].items()):
   if isinstance(v,str) and len(v)>3500:x['inspected_fields'][k]=v[:3500];x.setdefault('field_clipped',[]).append(k)
 out.append(x);print(json.dumps(x,ensure_ascii=False))
p=Path(__file__).parent/'raw-field-inspections.json'; prior=json.loads(p.read_text()) if p.exists() else [];p.write_text(json.dumps(prior+out,indent=2))
