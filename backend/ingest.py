"""Run ONLY on the VM. Original compressed source files remain private.

Streaming records are committed in batches with exact JSONL byte/line pointers.
The compact index can be searched without expanding source gzips. Optional
indexed_gzip indexes provide bounded random access to full private source rows.
"""
import argparse
import collections
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import time

from google.cloud import storage
from store import BUCKET, REVISION, TABLES, initialize, normalize_time

TEXT_FIELDS = ("content", "session_goal", "goal", "description", "name", "query", "summary", "answerToQuery", "nextSessionGoal")
SELECTED_META = {"name", "model_string", "speaker_type", "message_type", "message_subtype", "type", "generated_by", "summary_date",
                 "summary_target", "start_time", "end_time", "is_participating", "screenshot_is_redacted", "has_redaction_been_overruled",
                 "has_been_asked_to_stop", "has_been_approved", "event_index", "short_name", "slug", "deleted_at", "user_speaker_id"}

def timestamp(value):
    return normalize_time(value)

def text_fragments(value, budget=2400, depth=0):
    """Traverse provider-shaped content without serializing arbitrary large blobs."""
    if budget <= 0 or depth > 8:
        return ""
    if isinstance(value, str):
        return value[:budget]
    parts = []
    if isinstance(value, dict):
        keys = [k for k in ("text", "content", "thinking", "reasoning_content", "command", "description", "action", "message", "parts", "candidates", "output", "tool_calls", "function", "arguments") if k in value]
        for key in keys:
            piece = text_fragments(value[key], budget, depth + 1)
            if piece:
                parts.append(piece)
                budget -= len(piece) + 1
    elif isinstance(value, list):
        for item in value[:100]:
            piece = text_fragments(item, budget, depth + 1)
            if piece:
                parts.append(piece)
                budget -= len(piece) + 1
            if budget <= 0:
                break
    return "\n".join(parts)

def normalize(table, row, sessions):
    data = row.get("data") if isinstance(row.get("data"), dict) else {}
    agent = row.get("agent_id") or row.get("agent_speaker_id") or data.get("agentId") or data.get("speakerId")
    session = row.get("session_id") or data.get("computerUseSessionId")
    if table == "computer_use_turns" and session:
        agent = sessions.get(session)
    meta = {k: v for k, v in row.items() if k in SELECTED_META and isinstance(v, (str, int, float, bool, type(None)))}
    meta["source_fields"] = {
        "agent_id": "agent_id" if row.get("agent_id") else "agent_speaker_id" if row.get("agent_speaker_id") else "data.agentId" if data.get("agentId") else "data.speakerId",
        "session_id": "session_id" if row.get("session_id") else "data.computerUseSessionId",
        "room_id": "room_id" if row.get("room_id") else "data.roomId",
        "village_id": "village_id", "message_id": "data.messageId"}
    for k in ("speakerName", "speakerType", "seconds", "startDay", "endDay", "inputTokens", "outputTokens", "cost"):
        if k in data and isinstance(data[k], (str, int, float, bool, type(None))):
            meta[k] = data[k]
    action = row.get("agent_action")
    action_type = data.get("actionType") or row.get("message_type") or row.get("type") or table
    if isinstance(action, dict):
        action_type = action.get("action") or ("command" if action.get("command") else "computer_action")
        meta["agent_action"] = {k: (v[:1000] if isinstance(v, str) else v) for k, v in action.items() if isinstance(v, (str, int, float, bool, type(None)))}
    if table == "chat_messages":
        action_type = "AGENT_TALK" if row.get("speaker_type") == "agent" else "USER_TALK"
    pieces = []
    if table == "computer_use_turns":
        pieces = [text_fragments(action), text_fragments(row.get("agent_messages")), text_fragments(row.get("output")), text_fragments(row.get("error"))]
    else:
        for field in TEXT_FIELDS:
            if row.get(field) is not None:
                pieces.append(text_fragments(row[field]))
            if data.get(field) is not None:
                pieces.append(text_fragments(data[field]))
        if table == "events" and not any(pieces):
            pieces.append(text_fragments(data.get("output")))
    full = "\n".join(p for p in pieces if p)
    encoded_meta = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
    if len(encoded_meta.encode()) > 8000:
        meta = {k: (v[:300] if isinstance(v, str) else v) for k, v in meta.items() if k != "agent_action"}
        meta["metadata_truncated"] = True
        encoded_meta = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
        while len(encoded_meta.encode()) > 8000:
            candidates = [k for k,v in meta.items() if isinstance(v,str)]
            if not candidates:
                meta = {"metadata_truncated":True}
                break
            del meta[max(candidates,key=lambda k:len(meta[k].encode()))]
            encoded_meta = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
        encoded_meta = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
    return (timestamp(row.get("created_at")), agent, session, row.get("room_id") or data.get("roomId"),
            row.get("village_id"), data.get("messageId"), row.get("sdk_session_id"), str(action_type),
            full[:2000], int(len(full) > 2000), encoded_meta)

def log(**fields):
    print(json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **fields}), flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="../data")
    parser.add_argument("--tables", default=",".join(TABLES))
    parser.add_argument("--seek-indexes", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Explicit pilot only; marks table partial")
    parser.add_argument("--cache-mb",type=int,default=512,help="SQLite importer page cache budget")
    parser.add_argument("--batch-size",type=int,default=5000,help="Committed rows per ingestion batch")
    parser.add_argument("--max-db-gb",type=int,default=12,help="Combined SQLite main/WAL safety cap; use 24 only on the dedicated data volume")
    args = parser.parse_args()
    root = Path(args.data_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    rawdir = root / "sources"
    rawdir.mkdir(exist_ok=True)
    db = initialize(str(root / "evidence.sqlite"))
    db.execute("PRAGMA cache_size=-"+str(max(64,min(1024,args.cache_mb))*1024))
    batch_size=max(100,min(10000,args.batch_size))
    bucket = storage.Client().bucket(BUCKET)
    export = json.loads(bucket.blob("ai-village/manifest.json").download_as_text())
    (root / "export-manifest.json").write_text(json.dumps(export, indent=2))
    for table in TABLES:
        blob = bucket.blob("ai-village/" + table + ".jsonl.gz")
        blob.reload()
        if (blob.metadata or {}).get("hf-revision") != REVISION:
            raise RuntimeError("Source snapshot metadata mismatch: " + table)
        db.execute("INSERT OR IGNORE INTO sources(table_name,object_uri,generation,expected,bytes) VALUES(?,?,?,?,?)",
                   (table, "gs://" + BUCKET + "/" + blob.name, str(blob.generation), export["rowCounts"][table], blob.size))
    db.commit()
    sessions = {r[0]: r[1] for r in db.execute("SELECT source_id,agent_id FROM records WHERE table_name='computer_use_sessions'")}
    for table in args.tables.split(","):
        if table not in TABLES:
            raise ValueError("Unknown table " + table)
        source = db.execute("SELECT generation,indexed,status,bytes,expected FROM sources WHERE table_name=?", (table,)).fetchone()
        generation, checkpoint, status, source_size, expected = source
        if status == "complete":
            continue
        if shutil.disk_usage(root).free < max(source_size + 3 * 1024**3, 4 * 1024**3):
            raise RuntimeError("Insufficient disk headroom before " + table)
        path = rawdir / (table + ".jsonl.gz")
        blob = bucket.blob("ai-village/" + table + ".jsonl.gz", generation=int(generation))
        if not path.exists() or path.stat().st_size != source_size:
            temp = path.with_suffix(".partial")
            log(table=table, state="downloading", compressed_bytes=source_size)
            blob.download_to_filename(str(temp), if_generation_match=int(generation), checksum="auto", timeout=600)
            os.replace(temp, path)
        db.execute("UPDATE sources SET status='ingesting',error=NULL WHERE table_name=?", (table,))
        db.commit()
        names = []
        for agent_id, metadata in db.execute("SELECT source_id,metadata FROM records WHERE table_name='agents'"):
            name = json.loads(metadata).get("name")
            if name:
                names.append((agent_id, re.compile(r"(?<![\w.-])" + re.escape(name) + r"(?![\w.-])", re.I)))
        log(table=table, state="ingesting", resume_line=checkpoint)
        start = time.monotonic()
        daily = collections.Counter()
        mentions = collections.Counter()
        offset = 0
        processed = checkpoint
        file = gzip.open(path, "rb")
        index_reader = None
        if args.seek_indexes:
            import indexed_gzip
            index_reader = indexed_gzip.IndexedGzipFile(str(path), spacing=4 * 1024 * 1024)
            file = io.BufferedReader(index_reader, buffer_size=1024 * 1024)
        try:
            for number, line in enumerate(file, 1):
                line_offset = offset
                offset += len(line)
                if number <= checkpoint:
                    continue
                row = json.loads(line)
                values = normalize(table, row, sessions)
                cursor = db.execute("INSERT INTO records(table_name,source_id,timestamp,agent_id,session_id,room_id,village_id,message_id,sdk_session_id,action_type,excerpt,excerpt_truncated,metadata,source_line,byte_offset,byte_length,row_sha256) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                    (table, row["id"], *values, number, line_offset, len(line), hashlib.sha256(line).hexdigest()))
                pk = cursor.lastrowid
                db.execute("INSERT INTO record_fts(rowid,excerpt) VALUES(?,?)", (pk, values[8]))
                if table == "computer_use_sessions":
                    sessions[row["id"]] = row["agent_id"]
                day, agent = (values[0] or "unknown")[:10], values[1] or ""
                daily[(day, agent, table, values[7])] += 1
                if table == "chat_messages" and agent:
                    for target, regex in names:
                        if target != agent and regex.search(values[8]):
                            mentions[(day, agent, target)] += 1
                processed = number
                if number % batch_size == 0 or (args.limit and number >= args.limit):
                    flush(db, table, number, daily, mentions)
                    if number % 20000 == 0:
                        log(table=table, indexed=number, expected=expected, rows_per_second=round((number-checkpoint)/max(1,time.monotonic()-start)), sqlite_mb=round((root / "evidence.sqlite").stat().st_size/1e6))
                    check_capacity(root,args.max_db_gb)
                if args.limit and number >= args.limit:
                    break
            flush(db, table, processed, daily, mentions)
            complete = processed == expected
            db.execute("UPDATE sources SET status=? WHERE table_name=?", ("complete" if complete else "partial", table))
            db.commit()
            if index_reader is not None:
                index_reader.export_index(str(path) + ".gzidx")
            log(table=table, state="complete" if complete else "partial", indexed=processed, expected=expected, elapsed_seconds=round(time.monotonic()-start))
            db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except Exception as exc:
            db.rollback()
            db.execute("UPDATE sources SET status='error',error=? WHERE table_name=?", (str(exc)[:500], table))
            db.commit()
            raise
        finally:
            file.close()
    log(state="finished", indexed=db.execute("SELECT SUM(indexed) FROM sources").fetchone()[0])

def flush(db, table, number, daily, mentions):
    db.executemany("INSERT INTO activity(day,agent_id,table_name,action_type,count) VALUES(?,?,?,?,?) ON CONFLICT(day,agent_id,table_name,action_type) DO UPDATE SET count=count+excluded.count", [(*key,value) for key,value in daily.items()])
    db.executemany("INSERT INTO mentions(day,source_agent_id,target_agent_id,count) VALUES(?,?,?,?) ON CONFLICT(day,source_agent_id,target_agent_id) DO UPDATE SET count=count+excluded.count", [(*key,value) for key,value in mentions.items()])
    db.execute("UPDATE sources SET indexed=? WHERE table_name=?", (number, table))
    db.commit()
    daily.clear()
    mentions.clear()

def check_capacity(root,max_db_gb=12):
    db_path = root / "evidence.sqlite"
    size = sum(p.stat().st_size for p in [db_path, Path(str(db_path)+"-wal")] if p.exists())
    if size > max_db_gb * 1024**3:
        raise RuntimeError("SQLite main/WAL size reached configured safety cap; checkpoint, compact, or provision storage before continuing")
    if shutil.disk_usage(root).free < 3 * 1024**3:
        raise RuntimeError("VM free disk fell below 3 GiB; ingestion paused before exhaustion")

if __name__ == "__main__":
    main()
