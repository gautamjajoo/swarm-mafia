"""Deterministic lexical candidates, never failure or causal classifications."""
import argparse
import hashlib
import json
import sqlite3
import time
from collections import Counter

DEFINITION = "Exact repetitions among complete indexed chat-message texts of at least 80 characters, after Unicode casefold and whitespace collapse; at least three occurrences."
QUALIFICATION = {"table":"chat_messages","min_chars":80,"min_occurrences":3,"exclude_truncated":True,
                 "normalization":"Unicode casefold + collapsed whitespace","actor_count":"Distinct known agent or human speaker IDs; unknown speakers excluded"}
PATTERN_SCHEMA = """
CREATE TABLE IF NOT EXISTS deterministic_patterns(id TEXT PRIMARY KEY,kind TEXT NOT NULL,rank REAL NOT NULL,payload TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS deterministic_pattern_rank ON deterministic_patterns(kind,rank DESC,id);
"""

def add_temporal_sample(sample,row):
    sample.append((row.get("timestamp") or "","chat_messages:"+row["source_id"]))
    sample.sort()
    if len(sample)>10:
        sample[:]=sample[:5]+sample[-5:]

def count_participation(row,tracker):
    room,timestamp=row.get("room_id"),row.get("timestamp")
    if not room or not timestamp:
        tracker["excluded_missing_room_or_time"]+=1
        return
    key=(room,timestamp[:10])
    group=tracker["buckets"].setdefault(key,{"counts":Counter(),"samples":{},"human_messages":0,"unknown_agent_messages":0,"unknown_speaker_messages":0})
    metadata=row.get("metadata",{})
    if isinstance(metadata,str):
        metadata=json.loads(metadata)
    if metadata.get("speaker_type")=="agent":
        actor=row.get("agent_id")
        if not actor:
            group["unknown_agent_messages"]+=1
        else:
            group["counts"][actor]+=1
            sample=group["samples"].setdefault(actor,[])
            add_temporal_sample(sample,row)
    elif metadata.get("speaker_type")=="user":
        group["human_messages"]+=1
    else:
        group["unknown_speaker_messages"]+=1

def participation_candidates(tracker):
    result=[]
    for (room,day),group in tracker["buckets"].items():
        total=sum(group["counts"].values())
        if total<20:
            continue
        actor,count=sorted(group["counts"].items(),key=lambda item:(-item[1],item[0]))[0]
        result.append({"id":"participation_concentration:"+room+":"+day,"room_id":room,"day":day,
            "agent_id":actor,"message_count":count,"eligible_agent_messages":total,"share":count/total,
            "human_messages":group["human_messages"],"unknown_agent_messages":group["unknown_agent_messages"],
            "unknown_speaker_messages":group["unknown_speaker_messages"],"source_ids":[source_id for _,source_id in group["samples"][actor]],
            "sample_selection":"Up to five earliest and five latest matching records by UTC timestamp and source ID",
            "evidence_status":"volume_candidate","causal_claim":False,
            "interpretation":"Share of recorded agent-authored message volume; this does not measure influence, cooperation, or quality."})
    result.sort(key=lambda p:(-p["share"],-p["eligible_agent_messages"],p["id"]))
    return result

def discover_exact_repetitions(rows,participation=None):
    groups={}
    inspected=eligible=0
    for row in rows:
        inspected+=1
        if participation is not None:
            count_participation(row,participation)
        if row["excerpt_truncated"]:
            continue
        text=row["excerpt"]
        normalized=" ".join(text.casefold().split())
        if len(normalized)<80:
            continue
        eligible+=1
        group=groups.setdefault(normalized,{"text":text,"count":0,"actors":set(),"first":None,"last":None,"samples":[],"unknown_actor_occurrences":0})
        group["count"]+=1
        actor="agent:"+row["agent_id"] if row.get("agent_id") else None
        if not actor:
            metadata=row.get("metadata",{})
            if isinstance(metadata,str):
                metadata=json.loads(metadata)
            if metadata.get("user_speaker_id"):
                actor="user:"+metadata["user_speaker_id"]
        if actor:
            group["actors"].add(actor)
        else:
            group["unknown_actor_occurrences"]+=1
        timestamp=row.get("timestamp")
        if timestamp:
            group["first"]=min(group["first"],timestamp) if group["first"] else timestamp
            group["last"]=max(group["last"],timestamp) if group["last"] else timestamp
        add_temporal_sample(group["samples"],row)
    patterns=[]
    for normalized,g in groups.items():
        if g["count"]<3:
            continue
        patterns.append({"id":"exact_repetition:"+hashlib.sha256(normalized.encode()).hexdigest(),
                         "text":g["text"],"count":g["count"],"actor_count":len(g["actors"]),
                         "first":g["first"],"last":g["last"],"source_ids":[source_id for _,source_id in g["samples"]],
                         "known_agent_ids":sorted(actor.removeprefix("agent:") for actor in g["actors"] if actor.startswith("agent:")),
                         "sample_selection":"Up to five earliest and five latest matching records by UTC timestamp and source ID",
                         "unknown_actor_occurrences":g["unknown_actor_occurrences"],
                         "evidence_status":"lexical_candidate","causal_claim":False,
                         "interpretation":"Lexical repetition candidate; repetition alone does not establish failure, agreement, or causality."})
    patterns.sort(key=lambda p:(-p["count"],p["id"]))
    return patterns,{"inspected_chat_records":inspected,"eligible_chat_records":eligible,"pattern_count":len(patterns)}

def build(path):
    db=sqlite3.connect(path,timeout=60)
    db.row_factory=sqlite3.Row
    state=db.execute("SELECT status,indexed,expected FROM sources WHERE table_name='chat_messages'").fetchone()
    if not state or state["status"]!="complete" or state["indexed"]!=state["expected"]:
        raise RuntimeError("Exact repetition summary requires complete chat-message ingestion")
    rows=(dict(row) for row in db.execute("SELECT source_id,agent_id,room_id,timestamp,excerpt,excerpt_truncated,metadata FROM records WHERE table_name='chat_messages' ORDER BY source_line"))
    tracker={"buckets":{},"excluded_missing_room_or_time":0}
    patterns,coverage=discover_exact_repetitions(rows,tracker)
    participation=participation_candidates(tracker)
    db.executescript(PATTERN_SCHEMA)
    db.execute("DELETE FROM deterministic_patterns WHERE kind IN ('exact_repetition','participation_concentration')")
    db.executemany("INSERT INTO deterministic_patterns VALUES(?,'exact_repetition',?,?)",[(p["id"],p["count"],json.dumps(p)) for p in patterns])
    db.executemany("INSERT INTO deterministic_patterns VALUES(?,'participation_concentration',?,?)",[(p["id"],p["share"],json.dumps(p)) for p in participation])
    metadata={"built_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"definition":DEFINITION,"qualification":QUALIFICATION,**coverage}
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('pattern_exact_repetition',?)",(json.dumps(metadata),))
    participation_metadata={"built_at":metadata["built_at"],"definition":"Highest agent share of known agent-authored chat-message counts for each room and UTC day, with at least 20 eligible messages.",
        "qualification":{"table":"chat_messages","min_eligible_agent_messages":20,"time_bucket":"UTC calendar day","denominator":"Messages with speaker_type=agent and known agent_id; humans and unknown actors excluded and counted separately","includes_truncated_text":True},
        "inspected_chat_records":coverage["inspected_chat_records"],"eligible_room_days":len(participation),"pattern_count":len(participation),"excluded_missing_room_or_time":tracker["excluded_missing_room_or_time"]}
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('pattern_participation_concentration',?)",(json.dumps(participation_metadata),))
    db.commit()
    db.close()
    return {"exact_repetition":metadata,"participation_concentration":participation_metadata}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--db",default="../data/evidence.sqlite")
    print(json.dumps(build(parser.parse_args().db)))
