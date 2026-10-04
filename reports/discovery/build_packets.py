import json,os,sys,datetime
from pathlib import Path
root=Path(__file__).parent
sys.path.insert(0,str(root.parents[1]/'clients'))
from observatory_client.api import ObservatoryAPI
os.environ['OBSERVATORY_API_URL']='https://swarm-observatory.34.93.205.17.sslip.io'
os.environ['OBSERVATORY_API_TOKEN_FILE']=str(Path.home()/'.codex/secrets/swarm-observatory/api-token')
a=ObservatoryAPI.from_env(); records={}
for path in (root/'packets').glob('*.json'):
 r=json.loads(path.read_text());data=r.get('data')
 if isinstance(data,dict):data=data.get('records',[])
 if isinstance(data,list):
  for row in data:
   if isinstance(row,dict) and 'id' in row:records[row['id']]=row

def item(ident,title,quote,field,annotation,kind):return dict(id=ident,title=title,quote=quote,quote_field=field,annotation=annotation,evidence_kind=kind)
M=[
item('computer_use_turns:bbaecd27-4bae-4e38-9987-74920005b5aa','Workflow dispatch returns account restriction','Actions has been disabled for this user.','error','Recorded error establishes the local trigger problem; it does not establish why GitHub restricted this account. The shell fallback printed dispatch timed out for any nonzero status, so that label alone would be misleading.','recorded_tool_error'),
item('chat_messages:ee68d5b9-a8cb-4e7b-a209-b11bd981065d','Requester supplies a concrete cross-account workaround','cherry-pick commit 4ca4990 onto a new branch + open PR','content','GPT-5.2 asks another agent to re-publish the same fix so CI can run. A specific transferable commit is supplied.','recorded_request'),
item('chat_messages:fc669e9a-8a0e-458c-b7e0-1ffafc0330b1','Peer accepts the handoff','I can help trigger CI for PR #81.','content','Opus initially promises an empty commit. Subsequent actions instead use the requester’s alternative new-branch/cherry-pick path.','recorded_commitment'),
item('computer_use_turns:da346c3d-e74a-4cab-beca-6dca7fb3a13b','The original PR branch presents a second obstacle','A pull request already exists','error','The recorded create operation rejects a duplicate PR although Opus reported not finding an open PR. This supports a visibility/state inconsistency; not proof that PR81 never existed.','recorded_tool_error'),
item('computer_use_turns:a660e93d-ce72-4ce0-9581-1d312ba055ff','Opus actually cherry-picks and pushes the shared fix','705202b','output','Recorded command/output shows cherry-pick4ca4990 and a new commit with GPT-5.2 retained as author, followed by push output.','recorded_tool_action_and_output'),
item('computer_use_turns:74b74ad2-401e-4760-9c69-7b28a260ad78','The new pull request is created','https://github.com/ai-village-agents/rpg-game-rest/pull/82','output','The gh command returns PR82; this is an artifact receipt rather than only a chat completion claim.','recorded_tool_output'),
item('computer_use_turns:73c801bc-f958-4de8-8c3a-d29058d3d225','A third agent checks the new CI run','"conclusion":"success","status":"completed"','output','DeepSeek independently issues a run-status command for23814851757. The recorded output is completed/success; this is not an independent present-day GitHub audit.','recorded_tool_output'),
item('chat_messages:4c9d93b1-8ae2-4560-972b-846118790799','GPT-5.2 separates a remaining deployment failure','No url found for submodule path','content','The team does not treat CI success as complete deployment success. This chat diagnosis is subsequently corroborated by a recorded removal commit and deployment check.','recorded_diagnosis'),
item('computer_use_turns:eb249794-253d-4372-989a-c95c94c3c651','Opus removes the stray gitlink and commits the repair','1df3466','output','Recorded git action removes original-rpg-game; output identifies the fix commit. The corpus also records PR83 creation separately.','recorded_tool_action_and_output'),
item('computer_use_turns:f857a024-d911-48d7-aa50-e984789948d9','The repair PR is confirmed merged','"state":"MERGED"','output','Recorded gh result reports PR83 mergedAt19:21:20Z. This is stronger than the preceding should-be-fixed chat wording.','recorded_tool_output'),
item('computer_use_turns:ce6f6519-17be-4699-b36c-e209945fa1fe','The post-merge Pages run is checked successfully','"conclusion":"success"','output','Recorded run23815272789 is completed/success. Supports the bounded outcome: this workflow succeeded after the repair, not general game correctness or measured cooperation improvement.','recorded_tool_output'),
item('computer_use_turns:d6ea8ea8-d279-486e-8d33-f5920c6e83da','Requester verifies the gitlink is absent from main','Tree entry (should be empty):\nStage entry (should be empty):','output','The recorded check produces no intervening gitlink entries. This corroborates removal; absent .gitmodules is expected once the unused gitlink is gone.','recorded_tool_output')]
S=[
item('chat_messages:b35f8ed2-bd9c-4df0-9f49-89ffc06ddf06','o3 announces an appendix edit','Adding the cleaned six-line Hindrance/Nudge/Strength','content','One announced editor of the shared Playbook. Concurrent intent does not by itself prove destructive collision.','recorded_commitment'),
item('chat_messages:1a3d6700-6be6-4407-a8e7-2e8ff58e1e65','Sonnet announces another edit in the same period','rather than waiting for consensus','content','The message says it will directly fix formatting; interpreted with the actual capitalization retained in the source. This is an announced plan, not verified mutation.','recorded_commitment'),
item('computer_use_turns:ec5783c9-5299-4784-b9ea-8168d835614a','An appendix heading is actually typed','Appendix A — H/N/S Quick Reference (29-Sep-25)','agent_action.text','The input action is recorded. It does not establish its final location, what was selected, or that this edit deleted other content.','recorded_input_action'),
item('chat_messages:e9e5808f-91ee-4e97-a1b2-36349d77fd4a','Opus reports missing structure','the document structure seems to have changed significantly','content','This is a contemporaneous observation claim, not a source-level document diff. Opus attributes the problem to simultaneous editing.','recorded_observation_claim'),
item('chat_messages:6d2e8395-1357-4222-8aff-48c77a6e90aa','A designated repair editor volunteers','I’ll volunteer to be the document editor.','content','Sonnet proposes serialized editing and preserving valid additions.','recorded_coordination_proposal'),
item('chat_messages:c0460b52-2bd2-49f2-9c02-82a77c3c8ef0','Another editor agrees to pause','will refrain from further edits','content','o3 explicitly accepts the coordination constraint. This message alone does not prove all agents complied indefinitely.','recorded_commitment'),
item('chat_messages:0f4fc1c2-2c21-485a-bf8c-e66832795e35','First restoration attempt reports partial progress','couldn’t complete the full restoration','content','Sonnet still describes missing content and technical obstacles. Curly apostrophe in this working quote is normalized below to the exact source quote if necessary.','recorded_outcome_claim'),
item('computer_use_turns:492e2f7f-fe48-4701-b0e0-9b4a68f2b2ee','A different document access path is attempted','left_click','agent_action.action','Recorded click occurs while the agent says it is opening the PDF with Google Docs. The target is its screen interpretation; raw coordinates alone do not identify the artifact. A different rendering/version is an alternative explanation.','recorded_input_with_actor_interpretation'),
item('chat_messages:734cbc0d-b3fe-4532-bc03-df5e4e347760','The editor now reports substantial existing content','it appears most of the content from the PDF has already been transferred','content','Observation changes within minutes; this does not reveal who transferred content or whether the same underlying document was displayed.','recorded_observation_claim'),
item('chat_messages:9fc29bac-ce29-4c6f-90de-300ca935d278','Explicit correction: mostly intact, not empty','actually mostly intact, not empty as we initially feared','content','Key counterevidence against treating the original near-wipeout diagnosis as established. The editor says it preserved the appendix and changed its style.','recorded_correction'),
item('computer_use_turns:2de3323c-fb2c-436e-80e6-b1c8f4570919','Next-day restore-confirmation click is recorded','left_click','agent_action.action','Opus describes a Restore this version dialog and issues a click. No screenshot or document diff was independently inspected; actual restored content is not established by the click alone.','recorded_input_with_actor_interpretation'),
item('chat_messages:73ca014e-3095-4a4f-9208-31ecbef05152','Next-day restoration is reported again','restored the Mutual-Aid Playbook from yesterday’s version history','content','The later claim prevents interpreting the day-one all-clear as demonstrated durable recovery. It is an outcome report, not independent artifact verification.','recorded_outcome_claim')]
# Exact quotes must match source, including capitalization and punctuation.
S[1]['quote']='Rather than waiting for consensus'
S[4]['quote']="I'll volunteer to be the document editor."
S[6]['quote']="couldn't complete the full restoration"
S[11]['quote']="restored the Mutual-Aid Playbook from yesterday's version history"

def field(row,path):
 for part in path.split('.'):row=row[part]
 return row
for name,items in [('march31-repair',M),('sept29-playbook',S)]:
 timeline=[]
 for x in items:
  record=records[x['id']];table,ident=x['id'].split(':',1); raw=a.record(table,ident,raw=True)
  assert raw['data']['hash_verified'] and not raw['truncated'],x['id']
  decoded=json.loads(raw['data']['raw_json']);target=field(decoded,x['quote_field'])
  assert x['quote'] in target,(x['id'],x['quote'],target[:1000])
  result={**x,'timestamp':record['timestamp'],'actor':record.get('actor_name'),'actor_id':record.get('agent_id'),'provenance':record['provenance'],'raw_hash_verified':True,'quote_exact_match':True,'excerpt_truncated':record['excerpt_truncated']}
  timeline.append(result);print(name,result['timestamp'],result['id'],'verified',flush=True)
 report={'episode_id':name,'snapshot':timeline[0]['provenance']['snapshot'],'timeline':timeline,'source_scope':'Bounded AI Village API record/context/search responses; original JSONL rows individually hash-verified. No bulk corpus download.','verification_note':'A row hash verifies source-byte identity; an exact quote match does not independently validate an agent claim or interpretation.'}
 (root/(name+'.json')).write_text(json.dumps(report,indent=2)+'\n')
