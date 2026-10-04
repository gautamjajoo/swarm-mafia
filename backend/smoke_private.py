"""Run with sudo on VM. Credentials and source contents are never printed."""
import json
import time
from urllib.error import HTTPError,URLError
from urllib.parse import urlencode
from urllib.request import Request,build_opener,HTTPRedirectHandler

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

config={}
for line in open("/etc/swarm-observatory/backend.env"):
    if "=" in line and not line.startswith("#"):
        key,value=line.strip().split("=",1)
        config[key]=value.strip("\"'")
token=config["OBSERVATORY_API_TOKEN"]
base="https://swarm-observatory.34.93.205.17.sslip.io"
opener=build_opener(NoRedirect())

def request(path,auth=True):
    req=Request(base+path,headers={"Authorization":"Bearer "+token} if auth else {})
    try:
        response=opener.open(req,timeout=35)
    except HTTPError as error:
        response=error
    with response:
        body=response.read(4_000_000)
        try:
            data=json.loads(body)
        except (ValueError,UnicodeError):
            data={"detail":"Non-JSON response"}
        return response.code,data

for _ in range(20):
    try:
        if request("/health",False)[0]==200:
            break
    except URLError:
        pass
    time.sleep(.5)

report={}
for path in ("/v1/patterns","/v1/context?seed=agents:missing","/v1/search?q=correction"):
    status,_=request(path,False)
    assert status==401,("Anonymous route was not denied",path,status)
    report["anonymous "+path]=status

seed=None
for kind in ("exact_repetition","participation_concentration"):
    status,result=request("/v1/patterns?"+urlencode({"kind":kind,"limit":3}))
    assert status==200,("Pattern route failed",status)
    patterns=result["data"]["patterns"]
    assert all(p["causal_claim"] is False for p in patterns)
    report[kind]={"status":status,"returned":len(patterns),"pattern_count":result["data"]["pattern_count"],"truncated":result["truncated"],"names_present":bool(patterns[0].get("agent_name") or patterns[0].get("actor_names"))}
    seed=seed or patterns[0]["source_ids"][0]

table,ident=seed.split(":",1)
status,result=request("/v1/context?"+urlencode({"seed":seed,"before":3,"after":4}))
assert status==200,("Context route failed",status)
report["context"]={"status":status,"returned":len(result["data"]["records"]),"scope":result["data"]["scope"]}
status,result=request("/v1/records/"+table+"/"+ident+"/raw")
assert status==200 and result["data"]["hash_verified"] is True,("Raw source hash check failed",status)
report["raw"]={"status":status,"hash_verified":result["data"]["hash_verified"],"bytes_returned":result["data"]["bytes_returned"]}
for q in ("correction","the","__no_such_rare_probe_9f772c__"):
    start=time.monotonic()
    status,result=request("/v1/search?"+urlencode({"q":q,"limit":30}))
    assert status==200,("Search route failed",q,status)
    report["search "+q]={"status":status,"seconds":round(time.monotonic()-start,3),"returned":len(result["data"])}
report["over_limit"]=request("/v1/patterns?limit=31")[0]
report["unsupported_source"]=request("/v1/patterns?source=swarmtraces")[0]
assert report["over_limit"]==422 and report["unsupported_source"]==400
print(json.dumps(report,indent=2))
