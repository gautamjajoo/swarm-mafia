"""Run on VM: report counts, exact foreign-key gaps, and source hash checks only."""
import argparse
import json
from pathlib import Path
import sqlite3
import time
from collections import Counter

from store import Store

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--db",default="../data/evidence.sqlite")
    parser.add_argument("--references",action="store_true",help="Perform full indexed relationship audit")
    args=parser.parse_args()
    store=Store(args.db)
    report={"created_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"coverage":store.stats()["coverage"],"source_samples":[],"queries":{}}
    with sqlite3.connect("file:"+str(Path(args.db).resolve())+"?mode=ro",uri=True) as db:
        def table_rows(table,columns):
            # Table rows were appended in ingestion batches. Restrict the rowid
            # range, then check table_name, to avoid UUID-index random heap reads.
            low,high=db.execute("SELECT MIN(pk),MAX(pk) FROM records WHERE table_name=?",(table,)).fetchone()
            if low is None:
                return iter(())
            return db.execute("SELECT "+columns+" FROM records NOT INDEXED WHERE pk BETWEEN ? AND ? AND table_name=?",(low,high,table))
        for table,status in db.execute("SELECT table_name,status FROM sources"):
            if status!="complete":
                continue
            low,high=db.execute("SELECT MIN(pk),MAX(pk) FROM records WHERE table_name=?",(table,)).fetchone()
            seen=set()
            for position,target in (("first",low),("middle",(low+high)//2),("last",high)):
                pk,ident=db.execute("SELECT pk,source_id FROM records NOT INDEXED WHERE pk>=? AND pk<=? AND table_name=? ORDER BY pk LIMIT 1",(target,high,table)).fetchone()
                if pk in seen:
                    continue
                seen.add(pk)
                raw=store.raw_record(table,ident)
                report["source_samples"].append({"table":table,"position":position,"id":table+":"+ident,"hash_verified":raw["data"]["hash_verified"],"truncated":raw["truncated"],"bytes_returned":raw["data"]["bytes_returned"]})
        if args.references:
            report["actual_table_counts"]=dict(db.execute("SELECT table_name,COUNT(*) FROM records GROUP BY table_name"))
            report["fts_document_count"]=db.execute("SELECT COUNT(*) FROM record_fts_docsize").fetchone()[0]
            quality=list(db.execute("SELECT table_name,COUNT(*),SUM(excerpt_truncated),SUM(timestamp IS NULL),MAX(length(excerpt)),MAX(length(CAST(metadata AS BLOB))),SUM(byte_length>65536) FROM records NOT INDEXED GROUP BY table_name"))
            report["excerpt_clipping_by_table"]={row[0]:dict(total=row[1],clipped=row[2]) for row in quality}
            report["unknown_timestamps_by_table"]={row[0]:row[3] for row in quality}
            report["indexed_field_bounds_by_table"]={row[0]:dict(max_excerpt_characters=row[4],max_metadata_bytes=row[5],raw_rows_over_64KiB=row[6]) for row in quality}
            report["counts_match_manifest"]=all(report["actual_table_counts"].get(row["table_name"])==row["expected"]==row["indexed"] for row in report["coverage"]["tables"])
            report["fts_count_matches_records"]=report["fts_document_count"]==sum(report["actual_table_counts"].values())
            report["activity_record_count"]=db.execute("SELECT SUM(count) FROM activity").fetchone()[0]
            report["activity_count_matches_records"]=report["activity_record_count"]==sum(report["actual_table_counts"].values())
            joins=[("computer_use_turns","session_id","computer_use_sessions"),("computer_use_sessions","agent_id","agents"),
                   ("chat_messages","agent_id","agents"),("chat_messages","room_id","chat_rooms"),
                   ("events","message_id","chat_messages"),("events","session_id","computer_use_sessions"),
                   ("agent_memories","agent_id","agents"),("agent_goals","agent_id","agents")]
            report["unresolved_references"]={}
            parent_ids={parent:{row[0] for row in table_rows(parent,"source_id")} for parent in {parent for _,_,parent in joins}}
            for child,field,parent in joins:
                n=sum(1 for (value,) in table_rows(child,field) if value is not None and value not in parent_ids[parent])
                report["unresolved_references"][child+"."+field+"->"+parent]=n
            report["noncanonical_timestamps"]=db.execute("SELECT COUNT(*) FROM records WHERE timestamp IS NOT NULL AND length(timestamp)!=27").fetchone()[0]
            sdk_keys=Counter(pair for pair in table_rows("claude_code_sessions","agent_id,sdk_session_id") if None not in pair)
            report["ambiguous_sdk_session_keys"]=sum(count>1 for count in sdk_keys.values())
            report["unresolved_sdk_messages"]=sum(pair not in sdk_keys for pair in table_rows("claude_code_messages","agent_id,sdk_session_id"))
            event_indexes=[json.loads(metadata).get("event_index") for (metadata,) in table_rows("events","metadata")]
            report["missing_or_duplicate_event_indexes"]=len(event_indexes)-len({value for value in event_indexes if value is not None})
        for query in ("coordination", "failed", "plan"):
            start=time.monotonic()
            try:
                result=store.search(query,limit=10)
                report["queries"][query]={"seconds":round(time.monotonic()-start,3),"returned":len(result["data"]),"truncated":result["truncated"]}
            except sqlite3.OperationalError:
                report["queries"][query]={"seconds":round(time.monotonic()-start,3),"status":"budget_exceeded"}
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
