#!/usr/bin/env python3
"""VM-only exact-action census; reads immutable gzip, never executes source actions.
Read after SQLite scan, not concurrently. No raw source text appears in output.
"""
import argparse,collections,datetime,gzip,hashlib,json,os,sqlite3,time,sys
p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--source',required=True);p.add_argument('--output',required=True);p.add_argument('--seconds',type=int,default=1200);a=p.parse_args();os.nice(10);start=time.monotonic()
db=sqlite3.connect('file:'+a.db+'?mode=ro',uri=True);db.execute('PRAGMA query_only=ON');db.execute('PRAGMA cache_size=-8192')
names={i:json.loads(m).get('name') for i,m in db.execute("SELECT source_id,metadata FROM records WHERE table_name='agents'")}
actor_map={i:agent for i,agent in db.execute("SELECT source_id,agent_id FROM records WHERE table_name='computer_use_sessions'")}
expected=db.execute("SELECT expected FROM sources WHERE table_name='computer_use_turns'").fetchone()[0];db.close()
sessions={};total=0;quarters=collections.Counter();field_types=collections.Counter();missing=collections.Counter();error_tags=collections.Counter()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def utc(t):
 if not t:return None
 d=datetime.datetime.fromisoformat(t.replace('Z','+00:00'))
 if d.tzinfo is None:d=d.replace(tzinfo=datetime.timezone.utc)
 return d.astimezone(datetime.timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')
def qtr(t):return t[:4]+'-Q'+str((int(t[5:7])-1)//3+1) if t else 'unknown'
def finish(s):
 r=s.get('_run')
 if not r:return
 if r['count']>s.get('longest_exact_action_run',{}).get('count',0):s['longest_exact_action_run']=dict(r)
 if r['error_present_count'] and r['count']>s.get('longest_exact_action_with_error_run',{}).get('count',0):s['longest_exact_action_with_error_run']=dict(r)
 # Exclude actions whose repetition is normally observational, messaging or waiting.
 if r['action_type'] not in {'wait','pause','screenshot','send_message_back_to_chat','unknown','unknown_or_long_action_label'} and r['error_present_count'] and r['count']>s.get('longest_nontrivial_action_with_error_run',{}).get('count',0):s['longest_nontrivial_action_with_error_run']=dict(r)
with gzip.open(a.source,'rb') as f:
 for line in f:
  if time.monotonic()-start>a.seconds:break
  r=json.loads(line);total+=1;sid=r.get('session_id');t=utc(r.get('created_at'));ident='computer_use_turns:'+str(r.get('id'));action=r.get('agent_action');err=r.get('error');out=r.get('output');act=action.get('action') or ('command' if action.get('command') else 'computer_action') if isinstance(action,dict) else 'unknown';act=act if isinstance(act,str) and len(act)<80 else 'unknown_or_long_action_label'
  quarters[(qtr(t),act)]+=1;field_types[('error',type(err).__name__)]+=1;field_types[('output',type(out).__name__)]+=1
  if not sid:missing['session_id']+=1;continue
  agent=actor_map.get(sid);s=sessions.setdefault(sid,dict(session_id=sid,agent_id=agent,actor=names.get(agent),count=0,error_field_nonempty=0,output_field_nonempty=0,first=t,last=t,first_id=ident,last_id=ident,actions=collections.Counter(),time_regressions=0,_turns=[]))
  s['count']+=1;s['actions'][act]+=1;s['error_field_nonempty']+=bool(err);s['output_field_nonempty']+=bool(out)
  if t and s['last'] and t<s['last']:s['time_regressions']+=1
  if t and (not s['first'] or t<s['first']):s['first']=t;s['first_id']=ident
  if t and (not s['last'] or t>=s['last']):s['last']=t;s['last_id']=ident
  # Literal indicators only: they nominate bounded raw review and never prove failure.
  tags=[]
  if isinstance(err,str):
   for term,label in [('Traceback (most recent call last)','python_traceback'),('Permission denied','permission_denied'),('429','literal_429'),('rate limit','rate_limit_phrase'),('timed out','timed_out_phrase'),('not found','not_found_phrase'),('not allowed','not_allowed_phrase'),('disabled for this user','account_disabled_phrase')]:
    if term.lower() in err.lower():tags.append(label);error_tags[(qtr(t),label)]+=1
  stamp=datetime.datetime.fromisoformat(t.replace('Z','+00:00')).timestamp() if t else float('-inf')
  s['_turns'].append((stamp,t,ident,sys.intern(act),digest(action),bool(err),bool(out),tuple(tags)))
  if total%250000==0:print(json.dumps(dict(stage='raw_scan',turns=total,expected=expected,elapsed_seconds=round(time.monotonic()-start,1))),flush=True)
for s in sessions.values():
 # Original rows are not ordered within session: derive temporal runs after sorting.
 turns=s.pop('_turns');turns.sort(key=lambda x:(x[0],x[2]))
 s['source_order_backward_comparisons']=s['time_regressions'];s['time_regressions']=0
 s['timestamp_ties']=sum(turns[i][0]==turns[i-1][0] for i in range(1,len(turns)))
 for stamp,t,ident,act,sig,haserr,hasout,tags in turns:
  run=s.get('_run')
  if run and run['fingerprint']==sig:
   run['count']+=1;run['last_id']=ident;run['last']=t;run['error_present_count']+=haserr;run['output_present_count']+=hasout;run['literal_error_indicators']=sorted(set(run['literal_error_indicators']+list(tags)))
  else:
   finish(s);s['_run']=dict(action_type=act,count=1,first_id=ident,last_id=ident,first=t,last=t,fingerprint=sig,error_present_count=int(haserr),output_present_count=int(hasout),literal_error_indicators=list(tags))
 finish(s);s.pop('_run',None);s['actions']=dict(s['actions']);s['quarter']=qtr(s['first'])
 s['message_share']=s['actions'].get('send_message_back_to_chat',0)/s['count']
 s['elapsed_seconds']=(datetime.datetime.fromisoformat(s['last'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(s['first'].replace('Z','+00:00'))).total_seconds() if s['first'] and s['last'] else None
result=dict(version='exact-action-session-features-v1',snapshot='838b4150303ca8228e8edb432d8b8ccae353d258',complete=total==expected,expected_turns=expected,scanned_turns=total,session_count=len(sessions),sessions=list(sessions.values()),quarter_action_counts=[dict(quarter=q,action_type=act,count=n) for (q,act),n in sorted(quarters.items())],literal_error_indicators=[dict(quarter=q,indicator=tag,count=n) for (q,tag),n in sorted(error_tags.items())],field_types=[dict(field=field,type=typ,count=n) for (field,typ),n in field_types.items()],missing=dict(missing),elapsed_seconds=round(time.monotonic()-start,1),limitations=['Exact action fingerprints include all original agent_action fields, including arrays; no source command is executed.','Nonempty error fields may be harmless stderr; literal indicators are screening signals, not outcome labels.','Runs are sorted by parsed UTC timestamp within session, with canonical ID tie-break. Tied timestamps cannot establish strict order and are flagged.','Repeated actions and long sessions are structural candidates, not demonstrated failures.','Session elapsed time is first-to-last recorded turn, not active compute time or session lifecycle duration.'])
temp=a.output+'.tmp'
with open(temp,'w') as f:json.dump(result,f,separators=(',',':'))
os.replace(temp,a.output)
print(json.dumps(dict(stage='complete',complete=result['complete'],scanned_turns=total,sessions=len(sessions),elapsed_seconds=result['elapsed_seconds'],output=a.output)),flush=True)
