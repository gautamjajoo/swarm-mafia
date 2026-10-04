"""Bounded structural candidate selection over a VM-built metadata-only cache.
No live corpus scan, source command execution, or source text storage.
"""
from __future__ import annotations
import hashlib,json,os,threading
from datetime import datetime,timezone
from pathlib import Path
_CACHE_LOCK=threading.Lock();_CACHE={}

def _utc(value):
    if value is None:return None
    dt=datetime.fromisoformat(value.replace('Z','+00:00'))
    if dt.tzinfo is None:raise ValueError('Timestamp requires a timezone')
    return dt.astimezone(timezone.utc)

def discover_candidates(*,feature='mixed',agent_id=None,from_time=None,to_time=None,limit=8,source='ai-village',table='computer_use_turns',cache_path=None):
    if source!='ai-village':raise ValueError('Structural candidates support source=ai-village only')
    if table not in (None,'computer_use_turns'):raise ValueError('Structural candidates use table=computer_use_turns only')
    if feature not in ('mixed','long_session','repeated_action','message_dominant_session'):raise ValueError('Unknown structural feature')
    limit=int(limit)
    if not 1<=limit<=20:raise ValueError('Candidate limit must be 1..20')
    lo,hi=_utc(from_time),_utc(to_time)
    if lo and hi and lo>hi:raise ValueError('from_time must precede to_time')
    path=Path(cache_path or os.environ.get('OBSERVATORY_CENSUS_CACHE',''))
    if not path.is_file():raise RuntimeError('Structural candidate cache is unavailable; no whole-corpus discovery result can be claimed')
    stat=path.stat()
    if stat.st_size>128*1024*1024:raise RuntimeError('Structural candidate cache exceeds bounded metadata size')
    key=(str(path.resolve()),stat.st_mtime_ns,stat.st_size)
    with _CACHE_LOCK:
        if _CACHE.get('key')!=key:
            value=json.loads(path.read_text());_CACHE.clear();_CACHE.update(key=key,value=value)
        d=_CACHE['value']
    full=isinstance(d.get('sessions'),list)
    if full:rows=d['sessions']
    else:
        rows=list({r['session_id']:r for k in ('top_sessions_by_turns','top_nonmessage_scalar_runs','top_message_dominant_sessions') for r in d.get(k,[])}.values())
    scoped=[];boundary_excluded=0
    for s in rows:
        if agent_id and s.get('agent_id')!=agent_id:continue
        first,last=_utc(s.get('first')),_utc(s.get('last'))
        # Whole-session aggregates must stay wholly inside requested temporal scope.
        if (lo and (not first or first<lo)) or (hi and (not last or last>hi)):
            boundary_excluded+=1;continue
        scoped.append(s)
    candidates=[]
    for s in scoped:
        features=[]
        if s['count']>=50:features.append(('long_session',s['count'],None))
        r=s.get('longest_nontrivial_action_with_error_run') or s.get('longest_nonmessage_scalar_run')
        if not r:r=s.get('longest_exact_action_run')
        if r and not s.get('time_regressions') and not s.get('timestamp_ties') and r['count']>=3 and r['action_type'] not in ('wait','pause','screenshot','send_message_back_to_chat','unknown','unknown_or_long_action_label'):
            features.append(('repeated_action',r['count'],r))
        if s['count']>=100 and s.get('message_share',0)>=.8:features.append(('message_dominant_session',s['count']*s['message_share'],None))
        for kind,score,run in features:
            if feature not in ('mixed',kind):continue
            first=s.get('first');quarter=first[:4]+'-Q'+str((int(first[5:7])-1)//3+1) if first else 'unknown'
            source_ids=list(dict.fromkeys(([run['first_id'],run['last_id']] if run else [s['first_id'],s['last_id']])))
            candidates.append(dict(id=hashlib.sha256((d['snapshot']+s['session_id']+kind).encode()).hexdigest()[:20],feature=kind,session_id='computer_use_sessions:'+s['session_id'],agent_id=s.get('agent_id'),actor=s.get('actor'),timestamp_from=s.get('first'),timestamp_to=s.get('last'),quarter=quarter,evidence_status='structural_candidate',causal_status='not_established',features=dict(turns=s['count'],elapsed_seconds=s.get('elapsed_seconds'),message_share=s.get('message_share'),action_counts=s.get('actions',{}),repeated_run=run,error_field_nonempty=s.get('error_field_nonempty'),timestamp_ties=s.get('timestamp_ties',0),fingerprint_basis='complete original agent_action' if full else 'stored scalar metadata; arrays omitted, strings clipped'),source_ids=source_ids,next_retrievals=[dict(tool='context',seed=x,before=3,after=4) for x in source_ids],_score=score))
    # Per-feature ranks, then round-robin UTC quarter and actor diversity.
    ranked=[]
    for kind in ('repeated_action','long_session','message_dominant_session'):
        group=sorted([c for c in candidates if c['feature']==kind],key=lambda c:(-c['_score'],c['session_id']))
        for rank,c in enumerate(group,1):c['rank_in_feature']=rank;ranked.append(c)
    ranked.sort(key=lambda c:(c['rank_in_feature'],('repeated_action','long_session','message_dominant_session').index(c['feature']),c['quarter']))
    selected=[];seen_sessions=set();seen_quarters=set();seen_pairs=set()
    for policy in ('quarter','actor_quarter','remaining'):
        for c in ranked:
            if len(selected)>=limit:break
            if c['session_id'] in seen_sessions:continue
            pair=(c['quarter'],c['agent_id'])
            if policy=='quarter' and c['quarter'] in seen_quarters:continue
            if policy=='actor_quarter' and pair in seen_pairs:continue
            selected.append({k:v for k,v in c.items() if k!='_score'});seen_sessions.add(c['session_id']);seen_quarters.add(c['quarter']);seen_pairs.add(pair)
    coverage=dict(complete=bool(d.get('complete')),scanned_turns=d.get('scanned_turns'),expected_turns=d.get('expected_turns'),session_features='all sessions' if full else 'global top feature pools only',eligible_cached_sessions=len(scoped),candidate_sessions=len({c['session_id'] for c in candidates}),sessions_excluded_by_time_scope=boundary_excluded,scope=dict(source=source,table='computer_use_turns',agent_id=agent_id,from_time=from_time,to_time=to_time,temporal_rule='entire first-to-last session span must be inside bounds; crossing sessions excluded'),cache_version=d.get('version','scalar-metadata-v1'))
    limits=list(d.get('limitations',[]))+['Coverage is the canonical computer_use_turns table; SDK-message tool calls are not separately normalized in this cache.','Structural candidates are not citation evidence or outcome judgments. Hydrate canonical source IDs before making claims.','Nonempty error fields can be successful-command stderr; no field-presence count is a failure count.','Candidate selection is feature-ranked and diversified, not random or a population incidence sample.']
    if not full:limits.append('Filters operate on global top feature pools; no match cannot establish corpus absence for a date or actor.')
    return dict(snapshot=d['snapshot'],data=dict(records=selected,feature=feature,selection='per-feature ranks, quarter diversity, actor-quarter diversity, remaining ranks',limitations=limits),coverage=coverage,truncated=len({c['session_id'] for c in candidates})>len(selected),next_cursor=None)
