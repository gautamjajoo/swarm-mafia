import os
import secrets
import sqlite3
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from store import Store, TABLES
from swarmtraces_adapter import SwarmTracesStore, SwarmTracesError
from fastapi.responses import JSONResponse

app = FastAPI(title="Historical Agent Evidence", docs_url=None, redoc_url=None, openapi_url=None)
store = Store()
swarmtraces = SwarmTracesStore()

def source_store(source):
    if source == "ai-village":
        return store
    if source == "swarmtraces":
        return swarmtraces
    raise HTTPException(400, "source must be ai-village or swarmtraces")

@app.exception_handler(ValueError)
async def value_error(request, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)[:300]})

@app.exception_handler(SwarmTracesError)
async def upstream_error(request, exc):
    return JSONResponse(status_code=502, content={"detail": "Swarm Traces source is temporarily unavailable"})

@app.exception_handler(sqlite3.OperationalError)
async def query_error(request, exc):
    return JSONResponse(status_code=503, content={"detail": "Query exceeded the evidence-service budget or the index is temporarily busy; narrow the scope"})

def authenticate(authorization: str = Header(default="")):
    token = os.environ.get("OBSERVATORY_API_TOKEN", "")
    token_file = os.environ.get("OBSERVATORY_API_TOKEN_FILE", "")
    if token_file:
        with open(token_file) as f:
            token = f.read().strip()
    if not token or not secrets.compare_digest(authorization, "Bearer " + token):
        raise HTTPException(401, "Authentication required")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/v1/stats", dependencies=[Depends(authenticate)])
def stats(source: str = "ai-village"):
    return source_store(source).stats()

@app.get("/v1/agents", dependencies=[Depends(authenticate)])
def agents(source: str = "ai-village"):
    return source_store(source).agents()

@app.get("/v1/overview", dependencies=[Depends(authenticate)])
def overview(source: str = "ai-village"):
    return source_store(source).overview()

@app.get("/v1/patterns", dependencies=[Depends(authenticate)])
def patterns(kind: str = "exact_repetition",limit: int = Query(10,ge=1,le=30),source: str = "ai-village"):
    if source!="ai-village":
        raise HTTPException(400,"Lexical repetition candidates currently cover AI Village chat messages only")
    try:
        return store.patterns(kind,limit)
    except RuntimeError as exc:
        raise HTTPException(409,str(exc))

@app.get("/v1/search", dependencies=[Depends(authenticate)])
def search(q: str = "", agent_id: str = None, table: str = None, from_time: str = Query(None, alias="from"),
           to_time: str = Query(None, alias="to"), limit: int = Query(30, ge=1, le=100), cursor: int = Query(0, ge=0, le=100000), source: str = "ai-village"):
    selected = source_store(source)
    if source == "ai-village" and table and table not in TABLES:
        raise HTTPException(400, "Unknown table")
    return selected.search(q, agent_id, table, from_time, to_time, limit, cursor)

@app.get("/v1/timeline", dependencies=[Depends(authenticate)])
def timeline(agent_id: str = None, from_time: str = Query(None, alias="from"), to_time: str = Query(None, alias="to"),
             limit: int = Query(100, ge=1, le=200), cursor: int = Query(0, ge=0, le=100000), table: str = None, source: str = "ai-village"):
    selected = source_store(source)
    if source != "ai-village":
        raise HTTPException(400, "Swarm Traces has no reliable event timestamps for a timeline")
    if table and table not in TABLES:
        raise HTTPException(400, "Unknown table")
    return selected.search("", agent_id, table, from_time, to_time, limit, cursor, timeline=True)

@app.get("/v1/records/{table}/{source_id}", dependencies=[Depends(authenticate)])
def record(table: str, source_id: str, source: str = "ai-village"):
    selected = source_store(source)
    if source == "ai-village" and table not in TABLES:
        raise HTTPException(400, "Unknown table")
    result = selected.record(table, source_id)
    if not result:
        raise HTTPException(404, "Record has not been indexed")
    return result

@app.get("/v1/graph", dependencies=[Depends(authenticate)])
def graph(seed: str, hops: int = Query(1, ge=0, le=2), limit: int = Query(100, ge=1, le=200), source: str = "ai-village"):
    selected = source_store(source)
    if ":" not in seed or (source == "ai-village" and seed.split(":", 1)[0] not in TABLES):
        raise HTTPException(400, "seed must be a known table:source_id")
    return selected.graph(seed, hops, limit)

@app.get("/v1/records/{table}/{source_id}/raw", dependencies=[Depends(authenticate)])
def raw_record(table: str, source_id: str, source: str = "ai-village"):
    if source != "ai-village" or table not in TABLES:
        raise HTTPException(400, "Exact raw view is supported for AI Village tables")
    try:
        result = store.raw_record(table,source_id)
    except RuntimeError as exc:
        raise HTTPException(409, str(exc))
    if not result:
        raise HTTPException(404, "Record has not been indexed")
    return result

@app.get("/v1/context", dependencies=[Depends(authenticate)])
def context(seed: str, before: int = Query(8,ge=0,le=25), after: int = Query(8,ge=0,le=25), source: str = "ai-village", mode: str = "source"):
    if source != "ai-village":
        raise HTTPException(400,"Chronological context is unavailable for Swarm Traces")
    if ":" not in seed or seed.split(":",1)[0] not in TABLES:
        raise HTTPException(400,"seed must be a known table:source_id")
    return store.context(seed,before,after,mode)

try:
    from assistant import router as assistant_router
except ImportError:
    assistant_router = None
if assistant_router is not None:
    app.include_router(assistant_router, prefix="/v1", dependencies=[Depends(authenticate)])
