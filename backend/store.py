"""Compact, provenance-first SQLite access. No SQL or source credentials reach clients."""
import contextlib
import json
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from collections import deque

REVISION = "838b4150303ca8228e8edb432d8b8ccae353d258"
BUCKET = "kairosity-ai-village-504821"
TABLES = ["villages", "agents", "chat_rooms", "village_goals", "agent_goals",
          "computer_use_sessions", "claude_code_sessions", "chat_messages", "events",
          "summaries", "claude_code_messages", "agent_memories", "computer_use_turns"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources(table_name TEXT PRIMARY KEY, object_uri TEXT NOT NULL,
 generation TEXT NOT NULL, expected INTEGER NOT NULL, indexed INTEGER NOT NULL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'pending', bytes INTEGER NOT NULL, error TEXT);
CREATE TABLE IF NOT EXISTS records(pk INTEGER PRIMARY KEY, table_name TEXT NOT NULL,
 source_id TEXT NOT NULL, timestamp TEXT, agent_id TEXT, session_id TEXT, room_id TEXT,
 village_id TEXT, message_id TEXT, sdk_session_id TEXT, action_type TEXT,
 excerpt TEXT NOT NULL, excerpt_truncated INTEGER NOT NULL, metadata TEXT NOT NULL,
 source_line INTEGER NOT NULL, byte_offset INTEGER NOT NULL, byte_length INTEGER NOT NULL,
 row_sha256 TEXT NOT NULL, UNIQUE(table_name,source_id));
CREATE INDEX IF NOT EXISTS record_time ON records(timestamp,pk);
CREATE INDEX IF NOT EXISTS record_agent_time ON records(agent_id,timestamp,pk);
CREATE INDEX IF NOT EXISTS record_session ON records(session_id);
CREATE INDEX IF NOT EXISTS record_room ON records(room_id,timestamp);
CREATE INDEX IF NOT EXISTS record_message ON records(message_id);
CREATE INDEX IF NOT EXISTS record_sdk ON records(agent_id,sdk_session_id);
CREATE VIRTUAL TABLE IF NOT EXISTS record_fts USING fts5(excerpt, content='records', content_rowid='pk', tokenize='unicode61');
CREATE TABLE IF NOT EXISTS activity(day TEXT, agent_id TEXT, table_name TEXT, action_type TEXT,
 count INTEGER NOT NULL, PRIMARY KEY(day,agent_id,table_name,action_type));
CREATE TABLE IF NOT EXISTS mentions(day TEXT, source_agent_id TEXT, target_agent_id TEXT,
 count INTEGER NOT NULL, PRIMARY KEY(day,source_agent_id,target_agent_id));
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
"""

def initialize(path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.executescript("PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA cache_size=-65536;")
    db.executescript(SCHEMA)
    db.commit()
    return db

def normalize_time(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    except (ValueError, TypeError) as exc:
        raise ValueError("Timestamp must be an ISO date or datetime") from exc

class Store:
    def __init__(self, path=None):
        self.path = path or os.environ.get("OBSERVATORY_DB", "data/evidence.sqlite")

    @contextlib.contextmanager
    def connect(self):
        db = sqlite3.connect("file:" + os.path.abspath(self.path) + "?mode=ro", uri=True, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        deadline = time.monotonic() + 5
        db.set_progress_handler(lambda: int(time.monotonic() > deadline), 10000)
        try:
            yield db
        finally:
            db.close()

    def coverage(self, db):
        rows = [dict(r) for r in db.execute("SELECT table_name,expected,indexed,status FROM sources ORDER BY table_name")]
        return {"tables": rows, "complete": bool(rows) and all(r["status"] == "complete" for r in rows),
                "indexed_records": sum(r["indexed"] for r in rows), "expected_records": sum(r["expected"] for r in rows),
                "search_scope": "First 2000 characters of selected source text per record; not all raw content",
                "counting_unit": "Source records; an event and its referenced chat message may describe the same action. Counts are not unique actions.",
                "snapshot": REVISION}

    def envelope(self, db, data, truncated=False, next_cursor=None):
        return {"snapshot": REVISION, "data": data, "coverage": self.coverage(db),
                "truncated": bool(truncated), "next_cursor": next_cursor}

    def render(self, row, sources):
        r = dict(row)
        s = sources[r["table_name"]]
        result = {"id": r["table_name"] + ":" + r["source_id"], "source_id": r["source_id"],
                "table": r["table_name"], "agent_id": r["agent_id"], "timestamp": r["timestamp"],
                "action_type": r["action_type"], "excerpt": r["excerpt"],
                "excerpt_truncated": bool(r["excerpt_truncated"]), "metadata": json.loads(r["metadata"]),
                "evidence_status": "secondary_generated" if r["table_name"] == "summaries" else "recorded",
                "provenance": {"snapshot": REVISION, "object_uri": s["object_uri"], "generation": s["generation"],
                               "line": r["source_line"], "sha256": r["row_sha256"],
                               "byte_offset": r["byte_offset"], "byte_length": r["byte_length"]}}
        if r["table_name"] == "computer_use_turns" and r["session_id"]:
            result["actor_provenance"] = {"source_record_id":"computer_use_sessions:"+r["session_id"],"field":"agent_id","join":"computer_use_turns.session_id = computer_use_sessions.id"}
        actor_id=r["source_id"] if r["table_name"]=="agents" else r["agent_id"]
        actor_name=sources.get("__agent_names",{}).get(actor_id)
        if actor_name:
            result["actor_name"]=actor_name
            result["actor_name_provenance"]={"source_record_id":"agents:"+actor_id,"field":"name",
                "join":"computer_use_turns.session_id = computer_use_sessions.id; computer_use_sessions.agent_id = agents.id" if r["table_name"]=="computer_use_turns" else "associated agent ID = agents.id",
                "meaning":"Exported display name of the associated agent; this is not an authorship claim for SDK user/tool/system messages"}
        return result

    def sources(self, db):
        result={r["table_name"]: dict(r) for r in db.execute("SELECT * FROM sources")}
        result["__agent_names"]={r["source_id"]:json.loads(r["metadata"]).get("name") for r in db.execute("SELECT source_id,metadata FROM records WHERE table_name='agents'")}
        return result

    def source_field(self, row, column):
        fallback = column
        if row["table_name"] == "events":
            fallback = {"agent_id":"data.speakerId" if row["action_type"] == "AGENT_TALK" else "data.agentId",
                        "session_id":"data.computerUseSessionId", "room_id":"data.roomId", "message_id":"data.messageId"}.get(column,column)
        elif row["table_name"] == "chat_messages" and column == "agent_id":
            fallback = "agent_speaker_id"
        return json.loads(row["metadata"]).get("source_fields", {}).get(column,fallback)

    @staticmethod
    def agent_relation(table):
        return {"chat_messages":"AUTHORED_BY","agent_memories":"AUTHORED_BY",
                "computer_use_sessions":"RAN_BY","claude_code_sessions":"RAN_BY",
                "agent_goals":"ASSIGNED_TO"}.get(table,"ASSOCIATED_WITH_AGENT")

    def stats(self):
        with self.connect() as db:
            return self.envelope(db, {"storage": "private GCS originals + VM SQLite evidence index",
                                      "relations": "recorded source fields; no inferred causal edges"})

    def agents(self):
        with self.connect() as db:
            sources = self.sources(db)
            rows = db.execute("SELECT * FROM records WHERE table_name='agents' ORDER BY source_id")
            return self.envelope(db, [self.render(r, sources) for r in rows])

    def search(self, q="", agent_id=None, table=None, from_time=None, to_time=None, limit=30, cursor=0, timeline=False):
        limit = max(1, min(200 if timeline else 100, int(limit)))
        cursor = max(0, min(100000, int(cursor)))
        from_time, to_time = normalize_time(from_time), normalize_time(to_time)
        if from_time and to_time and from_time > to_time:
            raise ValueError("from must be at or before to")
        conditions, params = [], []
        index_hint = ""
        if q.strip():
            # Literal tokens only: never expose FTS operators or arbitrary SQL.
            tokens = re.findall(r"[\w-]+", q[:500], flags=re.UNICODE)[:12]
            if not tokens:
                tokens = ["__no_match__"]
            match = " AND ".join('"' + t.replace('"', '""') + '"' for t in tokens)
            # Materialize only matching integer row IDs, then traverse the time
            # index in requested order. Joining first fetched/sorted all matching
            # large payloads before LIMIT, causing common-term timeouts as the
            # corpus grew. Membership preserves complete matching semantics.
            index_hint = " INDEXED BY " + ("record_agent_time" if agent_id else "record_time")
            conditions.append("r.pk IN (SELECT rowid FROM record_fts WHERE record_fts MATCH ?)")
            params.append(match)
        for col, val, op in [("agent_id", agent_id, "="), ("table_name", table, "="),
                              ("timestamp", from_time, ">="), ("timestamp", to_time, "<=")]:
            if val:
                conditions.append("r." + col + op + "?")
                params.append(val)
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        order = "r.timestamp ASC,r.pk ASC" if timeline else "r.timestamp DESC,r.pk DESC"
        with self.connect() as db:
            sources = self.sources(db)
            rows = db.execute("SELECT r.* FROM records r" + index_hint + where + " ORDER BY " + order + " LIMIT ? OFFSET ?",
                              params + [limit + 1, cursor]).fetchall()
            more = len(rows) > limit
            return self.envelope(db, [self.render(r, sources) for r in rows[:limit]], more, cursor + limit if more else None)

    def record(self, table, source_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM records WHERE table_name=? AND source_id=?", (table, source_id)).fetchone()
            if row is None:
                return None
            return self.envelope(db, self.render(row, self.sources(db)))

    def overview(self):
        with self.connect() as db:
            daily = [dict(r) for r in db.execute("SELECT day,SUM(count) count FROM activity GROUP BY day ORDER BY day")]
            actions = [dict(r) for r in db.execute("SELECT action_type,SUM(count) count FROM activity GROUP BY action_type ORDER BY count DESC LIMIT 81")]
            agents = [dict(r) for r in db.execute("SELECT agent_id,SUM(count) count FROM activity WHERE agent_id!='' GROUP BY agent_id ORDER BY count DESC")]
            mentions = [dict(r) for r in db.execute("SELECT source_agent_id,target_agent_id,SUM(count) count FROM mentions GROUP BY source_agent_id,target_agent_id ORDER BY count DESC LIMIT 301")]
            return self.envelope(db, {"daily_activity": daily, "action_types": actions[:80], "agent_activity": agents,
                                     "agent_mentions": mentions[:300], "aggregate_limits": {"action_types":80,"agent_mentions":300},
                                     "mentions_definition": "Exact exported agent display-name matches in indexed chat-message excerpts, one count per message/target; mentions do not establish readership or influence."}, len(actions)>80 or len(mentions)>300)

    def patterns(self,kind="exact_repetition",limit=10):
        if kind not in ("exact_repetition","participation_concentration"):
            raise ValueError("Supported kinds are exact_repetition and participation_concentration")
        limit=max(1,min(30,int(limit)))
        with self.connect() as db:
            setting=db.execute("SELECT value FROM settings WHERE key=?",("pattern_"+kind,)).fetchone()
            if not setting:
                raise RuntimeError("Pattern candidates are not built yet")
            metadata=json.loads(setting[0])
            rows=db.execute("SELECT payload FROM deterministic_patterns WHERE kind=? ORDER BY rank DESC,id LIMIT ?",(kind,limit+1)).fetchall()
            patterns=[json.loads(row[0]) for row in rows[:limit]]
            def name(table,ident):
                row=db.execute("SELECT metadata FROM records WHERE table_name=? AND source_id=?",(table,ident)).fetchone()
                return json.loads(row[0]).get("name") if row else None
            for pattern in patterns:
                if kind=="participation_concentration":
                    pattern["agent_name"]=name("agents",pattern["agent_id"])
                    pattern["room_name"]=name("chat_rooms",pattern["room_id"])
                else:
                    ids=pattern.pop("known_agent_ids",[])
                    pattern["actor_names"]=[value for ident in ids[:10] if (value:=name("agents",ident))]
                    pattern["actor_names_truncated"]=len(ids)>10
                    pattern["actor_names_scope"]="Up to ten exported agent display names; human display names are unavailable"
            return self.envelope(db,{"kind":kind,**metadata,"patterns":patterns},len(rows)>limit)

    def raw_record(self, table, source_id, max_bytes=65536):
        """Read at most max_bytes from the exact private source JSONL record."""
        from pathlib import Path
        import hashlib
        import indexed_gzip
        with self.connect() as db:
            row = db.execute("SELECT * FROM records WHERE table_name=? AND source_id=?", (table,source_id)).fetchone()
            if row is None:
                return None
            source = db.execute("SELECT * FROM sources WHERE table_name=?",(table,)).fetchone()
            path = Path(self.path).resolve().parent / "sources" / (table + ".jsonl.gz")
            index = Path(str(path)+".gzidx")
            # Never construct an entire index in an interactive API request.
            if not index.is_file():
                raise RuntimeError("Exact source view will be ready when this table's ingestion and seek index finish")
            with indexed_gzip.IndexedGzipFile(str(path), index_file=str(index)) as stream:
                stream.seek(row["byte_offset"])
                raw = stream.read(min(max_bytes,row["byte_length"]))
            truncated = row["byte_length"] > len(raw)
            verified = not truncated and hashlib.sha256(raw).hexdigest() == row["row_sha256"]
            if not truncated and not verified:
                raise RuntimeError("Source record integrity check failed")
            # UTF-8 may end inside a code point at the display boundary.
            text = raw.decode("utf-8", errors="replace")
            return self.envelope(db, {"id": table+":"+source_id, "raw_json": text,
                "record": self.render(row,self.sources(db)),
                "bytes_returned":len(raw), "record_bytes":row["byte_length"], "hash_verified": verified,
                "format": "jsonl" if not truncated else "jsonl_prefix",
                "provenance":self.render(row,self.sources(db))["provenance"]}, truncated)

    def candidates(self, **kwargs):
        try:
            from .candidates import discover_candidates
        except ImportError:
            from candidates import discover_candidates
        return discover_candidates(**kwargs)

    def context(self, seed, before=8, after=8, mode="source"):
        before, after = max(0,min(25,int(before))), max(0,min(25,int(after)))
        if ":" not in seed:
            raise ValueError("seed must be table:source_id")
        table, ident = seed.split(":",1)
        if mode not in ("source","actor"):
            raise ValueError("Context mode must be source or actor")
        with self.connect() as db:
            anchor=db.execute("SELECT * FROM records WHERE table_name=? AND source_id=?",(table,ident)).fetchone()
            if anchor is None:
                return self.envelope(db,{"seed":seed,"records":[],"scope":None,"before_truncated":False,"after_truncated":False})
            filters, params = [], []
            scope={"kind":"table","id":table,"order":"timestamp_utc_then_source_id_then_table","mode":mode}
            if mode=="actor":
                actor=anchor["source_id"] if table=="agents" else anchor["agent_id"]
                if not actor:
                    raise ValueError("This record has no recorded or session-joined agent identity")
                filters=["agent_id=?"]
                params=[actor]
                scope.update(kind="actor_across_tables",id=actor)
            elif table=="computer_use_turns" and anchor["session_id"]:
                filters=["table_name='computer_use_turns'","session_id=?"]
                params=[anchor["session_id"]]
                scope.update(kind="session",id=anchor["session_id"])
            elif table=="claude_code_messages" and anchor["sdk_session_id"]:
                filters=["table_name='claude_code_messages'","agent_id=?","sdk_session_id=?"]
                params=[anchor["agent_id"],anchor["sdk_session_id"]]
                scope.update(kind="sdk_session",id=anchor["sdk_session_id"],agent_id=anchor["agent_id"])
            elif table=="chat_messages" and anchor["room_id"]:
                filters=["table_name='chat_messages'","room_id=?"]
                params=[anchor["room_id"]]
                scope.update(kind="room",id=anchor["room_id"])
            elif anchor["agent_id"]:
                filters=["table_name=?","agent_id=?"]
                params=[table,anchor["agent_id"]]
                scope.update(kind="agent",id=anchor["agent_id"])
            else:
                filters=["table_name=?"]
                params=[table]
            order="timestamp"
            value=anchor["timestamp"]
            if table=="events" and mode=="source":
                order="CAST(json_extract(metadata,'$.event_index') AS INTEGER)"
                value=json.loads(anchor["metadata"]).get("event_index")
                scope["order"]="event_index_then_source_id"
            if value is None:
                return self.envelope(db,{"seed":seed,"records":[self.render(anchor,self.sources(db))],"scope":{**scope,"order_unavailable":True},"before_truncated":False,"after_truncated":False})
            where=" AND ".join(filters)
            prior=db.execute("SELECT * FROM records WHERE "+where+" AND ("+order+",source_id,table_name)<(?,?,?) ORDER BY "+order+" DESC,source_id DESC,table_name DESC LIMIT ?",params+[value,ident,table,before+1]).fetchall()
            following=db.execute("SELECT * FROM records WHERE "+where+" AND ("+order+",source_id,table_name)>(?,?,?) ORDER BY "+order+" ASC,source_id ASC,table_name ASC LIMIT ?",params+[value,ident,table,after+1]).fetchall()
            clipped_before,clipped_after=len(prior)>before,len(following)>after
            rows=list(reversed(prior[:before]))+[anchor]+following[:after]
            sources=self.sources(db)
            return self.envelope(db,{"seed":seed,"records":[self.render(row,sources) for row in rows],"scope":scope,
                "before_truncated":clipped_before,"after_truncated":clipped_after,
                "interpretation":"Recorded neighboring rows in the stated scope; temporal sequence does not prove causality. Missing/unindexed records may limit context."},clipped_before or clipped_after)

    def graph(self, seed, hops=1, limit=100):
        limit = max(1, min(200, int(limit)))
        hops = max(0, min(2, int(hops)))
        if ":" not in seed:
            raise ValueError("seed must be table:source_id")
        with self.connect() as db:
            sources = self.sources(db)
            nodes, edges, queue, seen_edges = {}, [], deque([(seed, 0)]), set()
            truncated = False
            unresolved = 0
            ambiguous = 0
            def get(key):
                table, ident = key.split(":", 1)
                return db.execute("SELECT * FROM records WHERE table_name=? AND source_id=?", (table, ident)).fetchone()
            seed_row = get(seed)
            if seed_row is None:
                return self.envelope(db, {"nodes": [], "edges": [], "unresolved_references": 0})
            nodes[seed] = self.render(seed_row, sources)
            while queue:
                key, depth = queue.popleft()
                if depth >= hops:
                    continue
                row = get(key)
                relations = []
                mapping = [("agent_id", "agents", "AUTHORED_BY"), ("session_id", "computer_use_sessions", "IN_SESSION"),
                           ("room_id", "chat_rooms", "IN_ROOM"), ("village_id", "villages", "IN_VILLAGE"),
                           ("message_id", "chat_messages", "HAS_MESSAGE")]
                for col, table, kind in mapping:
                    if col == "agent_id" and row["table_name"] == "computer_use_turns":
                        continue  # actor is joined through session, not a direct turn field
                    if row[col] and table + ":" + row[col] != key:
                        if col == "agent_id":
                            kind = self.agent_relation(row["table_name"])
                        source_field = self.source_field(row,col)
                        relations.append((key, table + ":" + row[col], kind, source_field))
                if row["sdk_session_id"] and row["table_name"] == "claude_code_messages":
                    parents = db.execute("SELECT source_id FROM records WHERE table_name='claude_code_sessions' AND agent_id=? AND sdk_session_id=? ORDER BY source_id LIMIT ?",(row["agent_id"],row["sdk_session_id"],limit+1)).fetchall()
                    if len(parents)>1:
                        ambiguous+=1
                    if len(parents)>limit:
                        truncated=True
                    for parent in parents[:limit]:
                        relations.append((key,"claude_code_sessions:"+parent[0],"SHARES_SDK_SESSION_KEY" if len(parents)>1 else "IN_SDK_SESSION","sdk_session_id+agent_id"))
                elif row["sdk_session_id"] and row["table_name"] == "claude_code_sessions":
                    parent_count=db.execute("SELECT COUNT(*) FROM records WHERE table_name='claude_code_sessions' AND agent_id=? AND sdk_session_id=?",(row["agent_id"],row["sdk_session_id"])).fetchone()[0]
                    if parent_count>1:
                        ambiguous+=1
                    sdk_children=db.execute("SELECT source_id FROM records WHERE table_name='claude_code_messages' AND agent_id=? AND sdk_session_id=? ORDER BY timestamp DESC LIMIT ?",(row["agent_id"],row["sdk_session_id"],limit+1)).fetchall()
                    if len(sdk_children)>limit:
                        truncated=True
                    for child in sdk_children[:limit]:
                        relations.append(("claude_code_messages:"+child[0],key,"SHARES_SDK_SESSION_KEY" if parent_count>1 else "IN_SDK_SESSION","sdk_session_id+agent_id"))
                reverse = {"agents": "agent_id", "computer_use_sessions": "session_id", "chat_rooms": "room_id", "chat_messages": "message_id"}
                col = reverse.get(row["table_name"])
                if col:
                    exclusion = " AND table_name!='computer_use_turns'" if col == "agent_id" else ""
                    children = db.execute("SELECT table_name,source_id,metadata,action_type FROM records WHERE " + col + "=?" + exclusion + " ORDER BY timestamp DESC LIMIT ?", (row["source_id"], limit + 1)).fetchall()
                    if len(children) > limit:
                        truncated = True
                    kind = next(kind for column, _, kind in mapping if column == col)
                    for child in children[:limit]:
                        child_key = child["table_name"] + ":" + child["source_id"]
                        if child_key != key:
                            child_kind = self.agent_relation(child["table_name"]) if col == "agent_id" else kind
                            source_field = self.source_field(child,col)
                            relations.append((child_key,key,child_kind,source_field))
                for source, target, kind, field in relations:
                    other = target if source == key else source
                    if other not in nodes:
                        if len(nodes) >= limit:
                            truncated = True
                            continue
                        target_row = get(other)
                        if target_row is None:
                            unresolved += 1
                            continue
                        nodes[other] = self.render(target_row, sources)
                        queue.append((other, depth + 1))
                    edge_id = source + "|" + kind + "|" + target
                    if edge_id not in seen_edges:
                        if len(edges)>=600:
                            truncated=True
                            continue
                        seen_edges.add(edge_id)
                        edges.append({"id": edge_id, "source": source, "target": target, "type": kind,
                                      "evidence_status": "recorded", "provenance": {"source_record_id": source, "field": field}})
            return self.envelope(db, {"nodes": list(nodes.values()), "edges": edges, "unresolved_references": unresolved,
                                     "ambiguous_references":ambiguous,"limits":{"nodes":limit,"edges":600,"hops":hops}}, truncated)
