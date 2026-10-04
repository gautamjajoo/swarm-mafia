"""Explicit local-preview persistence acceptance test; creates a labeled QA case."""
import concurrent.futures,json,urllib.request,urllib.error
BASE='http://127.0.0.1:3000'
def call(method,path,payload=None):
    body=json.dumps(payload).encode() if payload is not None else None
    req=urllib.request.Request(BASE+path,data=body,method=method,headers={'Cookie':'__sites_local_auth=1','Origin':BASE,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=15) as r:return r.status,json.load(r)
    except urllib.error.HTTPError as e:return e.code,json.load(e)
state={'query':'fixture','filters':{},'pins':[],'notes':[{'id':'qa-note','text':'A textual acknowledgment is not an outcome.','target_claim':'Compliance improved.','source_ids':['chat_messages:fixture'],'record_id':'chat_messages:fixture','evidence_status':'counterevidence','review_status':'disputed','created_at':'2026-10-04T00:00:00Z'}],'studies':[],'messages':[],'tab':'context','context_mode':'actor','selected_id':'chat_messages:fixture'}
payload={'title':'QA — synthetic persistence and conflict test','source':'ai-village','snapshot':'synthetic-test-only','state':state}
status,new=call('POST','/api/investigations',payload);assert status==201,(status,new)
path='/api/investigations/'+new['id'];payload['revision']=1
with concurrent.futures.ThreadPoolExecutor(2) as pool:
    results=list(pool.map(lambda _:call('PUT',path,payload),range(2)))
assert sorted(s for s,_ in results)==[200,409],results
status,read=call('GET',path);assert status==200 and read['revision']==2
assert read['state']==state,read['state']
invalid={**payload,'state':{**state,'studies':[{'id':'invalid','title':'invalid','status':'executed'}]}}
status,_=call('PUT',path,invalid);assert status==400
large={**payload,'title':'x'*1000001};status,_=call('POST','/api/investigations',large);assert status==400
print(json.dumps({'checks':5,'passed':True,'created_local_qa_case':new['id'],'revision_conflict':[200,409],'large_body':status}))
