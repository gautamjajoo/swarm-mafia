"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  Upload,
  Download,
  ArrowRight,
  FlaskConical,
  MessageSquare,
  Network,
  List,
  Loader2,
  CheckCircle2,
  AlertCircle,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  api,
  download as downloadText,
  type InvestigationResult,
  type Study,
} from "@/lib/evidence";
import {
  audience,
  eventLabel,
  prefixState,
  societyPath,
  type TraceRun,
  type TraceSummary,
  type TraceGraph,
  type TraceCheck,
  type WorldAction,
  type WorldResult,
} from "@/lib/society";
import { EvidenceGraph } from "@/components/observatory/evidence-graph";
import "./society.css";

const asText = (value: unknown) =>
  typeof value === "string" ? value : JSON.stringify(value, null, 2);
const errorText = (e: unknown) =>
  e instanceof Error ? e.message : "The request could not be completed.";
const download = (name: string, data: unknown) =>
  downloadText(name, JSON.stringify(data, null, 2));
function Json({ value }: { value: unknown }) {
  return <pre className="sl-json">{asText(value)}</pre>;
}

export function SocietyLab({
  study,
  evidence,
  active = true,
  onDraftStudy,
}: {
  study?: Study | null;
  evidence?: unknown;
  active?: boolean;
  onDraftStudy: (
    title: string,
    hypothesis: string,
    sourceRef: NonNullable<Study["source_ref"]>,
  ) => void;
}) {
  const [tab, setTab] = useState<"traces" | "world">(
    study ? "world" : "traces",
  );
  const [listTruncated, setListTruncated] = useState(false);
  const [runs, setRuns] = useState<TraceSummary[]>([]),
    [run, setRun] = useState<TraceRun | null>(null);
  const [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  const [playhead, setPlayhead] = useState(0),
    [playing, setPlaying] = useState(false),
    [actor, setActor] = useState(""),
    [kind, setKind] = useState("");
  const [mode, setMode] = useState<"replay" | "graph">("replay"),
    [graph, setGraph] = useState<TraceGraph | null>(null),
    [graphBusy, setGraphBusy] = useState(false);
  const [question, setQuestion] = useState(
    "Where do completion claims diverge from recorded tool outcomes? Check recovery as well.",
  );
  const [review, setReview] = useState<InvestigationResult | null>(null),
    [reviewBusy, setReviewBusy] = useState(false);
  const [checks, setChecks] = useState<TraceCheck[]>([]),
    [notes, setNotes] = useState<
      { text: string; event_id: string; kind: string }[]
    >([]),
    [note, setNote] = useState("");
  const input = useRef<HTMLInputElement>(null),
    generation = useRef(0),
    reviewAbort = useRef<AbortController | null>(null),
    graphGeneration = useRef(0);
  const events = run?.payload.events ?? [],
    event = playhead > 0 ? events[playhead - 1] : undefined;
  const state = useMemo(
    () => prefixState(events, playhead),
    [events, playhead],
  );
  const actors = useMemo(
    () =>
      [...new Set(events.map((e) => e.actor_id).filter(Boolean))] as string[],
    [events],
  );
  const kinds = useMemo(
    () => [...new Set(events.map((e) => e.kind))],
    [events],
  );
  const visible = events
    .map((e, i) => ({ e, i }))
    .filter(
      ({ e }) => (!actor || e.actor_id === actor) && (!kind || e.kind === kind),
    );
  const refresh = async () => {
    const r = await api<{ runs: TraceSummary[]; truncated: boolean }>(
      societyPath("runs"),
    );
    setRuns(r.runs);
    setListTruncated(r.truncated);
  };
  useEffect(() => {
    void refresh().catch((e) => setError(errorText(e)));
    return () => {
      generation.current++;
      reviewAbort.current?.abort();
    };
  }, []);
  useEffect(() => {
    if (!active) setPlaying(false);
  }, [active]);
  useEffect(() => {
    if (study) setTab("world");
  }, [study]);
  useEffect(() => {
    if (!playing || !events.length) return;
    const id = setInterval(
      () =>
        setPlayhead((p) => {
          if (p >= events.length) {
            setPlaying(false);
            return p;
          }
          return p + 1;
        }),
      1200,
    );
    return () => clearInterval(id);
  }, [playing, events.length]);
  async function openRun(id: string, version: number) {
    const g = ++generation.current;
    reviewAbort.current?.abort();
    setReviewBusy(false);
    setBusy(true);
    setError("");
    setPlaying(false);
    setChecks([]);
    setGraphBusy(false);
    graphGeneration.current++;
    try {
      const r = await api<{
        run: TraceRun;
        review?: { observations?: TraceCheck[] };
      }>(societyPath(`runs/${encodeURIComponent(id)}?version=${version}`));
      if (g !== generation.current) return;
      setRun(r.run);
      setPlayhead(1);
      setReview(null);
      setNotes([]);
      setNote("");
      setActor("");
      setKind("");
      setGraph(null);
      setMode("replay");
      setChecks(r.review?.observations ?? []);
    } catch (e) {
      if (g === generation.current) setError(errorText(e));
    } finally {
      if (g === generation.current) setBusy(false);
    }
  }
  async function importText(raw: string) {
    setError("");
    setBusy(true);
    try {
      if (new TextEncoder().encode(raw).length > 1048576)
        throw new Error(
          "Import one JSON batch of up to 1 MiB and 2,000 events.",
        );
      const response = await fetch(societyPath("runs"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: raw,
      });
      const r = (await response.json()) as {
        run: TraceRun;
        idempotent: boolean;
        added_events: number;
        detail?: string;
      };
      if (!response.ok)
        throw new Error(
          typeof r.detail === "string" ? r.detail : "Trace import failed.",
        );
      await refresh();
      await openRun(r.run.id, r.run.version);
      setNotice(
        r.idempotent
          ? "This exact batch was already saved. No duplicate events were added."
          : `${r.added_events} events saved as version ${r.run.version}.`,
      );
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  async function loadExample() {
    try {
      const r = await fetch("/society-example.json");
      if (!r.ok) throw new Error("Example unavailable");
      await importText(await r.text());
    } catch (e) {
      setError(errorText(e));
    }
  }
  async function loadGraph(seed = event?.id) {
    if (!run || !seed) return;
    const g = generation.current,
      requestId = ++graphGeneration.current;
    setGraphBusy(true);
    setMode("graph");
    setError("");
    try {
      const r = await api<TraceGraph>(
        societyPath(
          `runs/${encodeURIComponent(run.id)}/graph?version=${run.version}&seed=${encodeURIComponent(seed)}&hops=1`,
        ),
      );
      if (g === generation.current && requestId === graphGeneration.current)
        setGraph(r);
    } catch (e) {
      if (g === generation.current) setError(errorText(e));
    } finally {
      if (g === generation.current && requestId === graphGeneration.current)
        setGraphBusy(false);
    }
  }
  async function investigate() {
    if (!run || !question.trim()) return;
    const g = generation.current;
    setReviewBusy(true);
    setError("");
    const controller = new AbortController();
    reviewAbort.current = controller;
    try {
      const r = await api<InvestigationResult>(
        societyPath(`runs/${encodeURIComponent(run.id)}/investigate`),
        { version: run.version, question },
        undefined,
        controller.signal,
      );
      if (g === generation.current) setReview(r);
    } catch (e) {
      if (g === generation.current && !controller.signal.aborted)
        setError(errorText(e));
    } finally {
      if (g === generation.current) setReviewBusy(false);
    }
  }
  function jump(id: string) {
    const resolved = review?.sources.find((s) => s.id === id)?.source_id ?? id;
    const index = events.findIndex((e) => e.id === resolved);
    if (index >= 0) {
      setPlayhead(index + 1);
      setMode("replay");
      setPlaying(false);
      setActor("");
      setKind("");
      requestAnimationFrame(() =>
        document
          .getElementById("society-evidence")
          ?.scrollIntoView({ behavior: "smooth", block: "start" }),
      );
    }
  }
  return (
    <section className="society-lab">
      <div className="sl-heading">
        <div>
          <div className="eyebrow">TRACE & TEST LAB</div>
          <h1>Follow behavior. Test an explanation.</h1>
          <p>
            Bring your own traces into the same evidence workflow, then explore
            a controlled world.
          </p>
        </div>
        <div className="sl-tabs" aria-label="Lab views">
          <button
            className={tab === "traces" ? "active" : ""}
            onClick={() => setTab("traces")}
          >
            <List size={16} />
            Trace replay
          </button>
          <button
            className={tab === "world" ? "active" : ""}
            onClick={() => setTab("world")}
          >
            <FlaskConical size={16} />
            Test environment
          </button>
        </div>
      </div>
      <div hidden={tab !== "world"}>
        <WorldSandbox
          study={study}
          evidence={
            study?.source_ref ??
            (run
              ? {
                  id: run.id,
                  version: run.version,
                  hash: run.hash,
                  question,
                  notes,
                }
              : evidence)
          }
        />
      </div>
      <div hidden={tab !== "traces"}>
        <div className="sl-import-bar">
          <div>
            <strong>Connected runs</strong>
            <span>
              Versioned telemetry · source remains declared by its producer
            </span>
          </div>
          <div className="sl-actions">
            <Button variant="outline" disabled={busy} onClick={loadExample}>
              Open authored example
            </Button>
            <Button disabled={busy} onClick={() => input.current?.click()}>
              <Upload size={15} />
              Import traces
            </Button>
            <input
              ref={input}
              type="file"
              accept=".json,application/json"
              hidden
              aria-label="Import telemetry JSON"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                e.target.value = "";
                if (!file) return;
                if (file.size > 1048576) {
                  setError(
                    "File exceeds 1 MiB. Split it into batches with stable event IDs.",
                  );
                  return;
                }
                await importText(await file.text());
              }}
            />
          </div>
        </div>
        {error && (
          <div className="sl-error" role="alert">
            <AlertCircle size={17} />
            {error}
          </div>
        )}
        {notice && (
          <div className="sl-notice" role="status">
            {notice}
            <button aria-label="Dismiss notice" onClick={() => setNotice("")}>
              <X size={14} />
            </button>
          </div>
        )}
        <div className="sl-run-list">
          {runs.map((r) => (
            <button
              key={r.id}
              disabled={busy}
              className={run?.id === r.id ? "selected" : ""}
              onClick={() => void openRun(r.id, r.version)}
            >
              <strong>{r.run.name ?? r.run.id}</strong>
              <span>
                {r.event_count} events · v{r.version} ·{" "}
                {r.source.kind === "authored_example"
                  ? "Authored example"
                  : "Imported telemetry"}
              </span>
            </button>
          ))}
        </div>
        {listTruncated && (
          <p className="sl-muted">
            Showing the most recent 50 runs. Use the API or CLI to inspect a
            saved run by its ID.
          </p>
        )}
        {busy && (
          <p className="sl-loading">
            <Loader2 className="animate-spin" size={18} />
            Opening the exact saved version…
          </p>
        )}
        {!run && !busy && (
          <div className="sl-start">
            <div className="sl-start-icon">
              <Network size={32} />
            </div>
            <h2>What happened after “done”?</h2>
            <p>
              Import messages, tool calls and receipts, task changes, and
              artifact revisions. Replay their recorded order without revealing
              outcomes early.
            </p>
            <div className="sl-start-flow">
              <span>Import a run</span>
              <ArrowRight />
              <span>Inspect the sequence</span>
              <ArrowRight />
              <span>Question the evidence</span>
            </div>
            <details>
              <summary>Supported format and access</summary>
              <p>
                societylab.events.v1 · JSON batches up to 1 MiB / 2,000 events.
                Reimporting unchanged event IDs is idempotent; changing a saved
                event is rejected. Imported runs are shared inside this admitted
                private workspace.
              </p>
              <Button
                variant="outline"
                onClick={async () => {
                  try {
                    download(
                      "society-protocol.json",
                      await api(societyPath("protocol")),
                    );
                  } catch (e) {
                    setError(errorText(e));
                  }
                }}
              >
                Download schema guide
              </Button>
            </details>
          </div>
        )}
        {run && (
          <>
            <div className="sl-run-heading">
              <div>
                <span className="sl-badge">
                  {run.payload.source.kind === "authored_example"
                    ? "Authored example · not observed agent behavior"
                    : "Producer-declared telemetry"}
                </span>
                <h2>{run.payload.run.name ?? run.payload.run.id}</h2>
                <details>
                  <summary>
                    Exact version {run.version} · {run.hash.slice(0, 12)}
                  </summary>
                  <code>
                    {run.id}
                    <br />
                    {run.hash}
                  </code>
                  <p>{run.payload.source.name}</p>
                  <label>
                    Open saved version{" "}
                    <input
                      aria-label="Saved run version"
                      type="number"
                      min="1"
                      max={
                        runs.find((r) => r.id === run.id)?.version ??
                        run.version
                      }
                      defaultValue={run.version}
                      key={run.id + run.version}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          const v = Number(e.currentTarget.value);
                          if (Number.isSafeInteger(v) && v > 0)
                            void openRun(run.id, v);
                        }
                      }}
                    />
                  </label>
                  <small>Press Enter to inspect an earlier version.</small>
                </details>
              </div>
              <Button
                variant="outline"
                onClick={() =>
                  download(`swarm-review-v${run.version}.json`, {
                    schema_version: "swarm-mafia.review.v1",
                    run,
                    question,
                    ai_review: review,
                    human_notes: notes,
                    human_notes_status: "unverified_observations",
                    scope: "exact_saved_run",
                  })
                }
              >
                <Download size={15} />
                Export review
              </Button>
            </div>
            <div className="sl-workbench" id="society-evidence">
              <div className="sl-replay">
                <div className="sl-replay-toolbar">
                  <div className="sl-tabs">
                    <button
                      className={mode === "replay" ? "active" : ""}
                      onClick={() => setMode("replay")}
                    >
                      <Play size={14} />
                      Replay
                    </button>
                    <button
                      className={mode === "graph" ? "active" : ""}
                      onClick={() => void loadGraph()}
                    >
                      <Network size={14} />
                      Event links
                    </button>
                  </div>
                  <span>{events.length} captured events</span>
                </div>
                {mode === "replay" ? (
                  <>
                    <div className="sl-player">
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label="Restart replay"
                        onClick={() => {
                          setPlaying(false);
                          setPlayhead(0);
                        }}
                      >
                        <RotateCcw size={16} />
                      </Button>
                      <Button
                        size="icon"
                        aria-label={playing ? "Pause replay" : "Play replay"}
                        onClick={() => {
                          if (playhead === events.length) setPlayhead(0);
                          setPlaying(!playing);
                        }}
                      >
                        {playing ? <Pause size={16} /> : <Play size={16} />}
                      </Button>
                      <input
                        type="range"
                        min="0"
                        max={events.length}
                        value={playhead}
                        aria-label="Replay position"
                        onChange={(e) => {
                          setPlaying(false);
                          setPlayhead(Number(e.target.value));
                        }}
                      />
                      <span>
                        {playhead} / {events.length}
                      </span>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label="Next event"
                        disabled={playhead === events.length}
                        onClick={() => {
                          setPlaying(false);
                          setPlayhead((p) => p + 1);
                        }}
                      >
                        <SkipForward size={16} />
                      </Button>
                    </div>
                    <div className="sl-filters">
                      <select
                        aria-label="Filter replay actor"
                        value={actor}
                        onChange={(e) => setActor(e.target.value)}
                      >
                        <option value="">All actors</option>
                        {actors.map((a) => (
                          <option key={a}>{a}</option>
                        ))}
                      </select>
                      <select
                        aria-label="Filter event type"
                        value={kind}
                        onChange={(e) => setKind(e.target.value)}
                      >
                        <option value="">All event types</option>
                        {kinds.map((k) => (
                          <option key={k}>{k}</option>
                        ))}
                      </select>
                      <small>Capture order; timestamps may be skewed.</small>
                    </div>
                    <div
                      className="sl-events"
                      aria-label="Recorded event sequence"
                    >
                      {visible
                        .filter(({ i }) => i < playhead)
                        .map(({ e, i }) => (
                          <button
                            className={`sl-event ${event?.id === e.id ? "current" : ""}`}
                            key={e.id}
                            onClick={() => {
                              setPlayhead(i + 1);
                              setPlaying(false);
                            }}
                          >
                            <span className="sl-event-position">
                              {String(i + 1).padStart(2, "0")}
                            </span>
                            <div>
                              <div className="sl-event-meta">
                                <strong>
                                  {e.actor_id ?? "Actor not declared"}
                                </strong>
                                <span>{e.kind}</span>
                                <time>{e.occurred_at.slice(11, 19)}</time>
                              </div>
                              <p>{eventLabel(e)}</p>
                              <small>{audience(e)}</small>
                            </div>
                            {e.kind === "tool.returned" &&
                              (e.data.success ? (
                                <CheckCircle2 size={16} />
                              ) : (
                                <AlertCircle size={16} />
                              ))}
                          </button>
                        ))}
                      {!playhead && (
                        <p className="sl-muted">
                          Press play or advance to reveal the first event.
                        </p>
                      )}
                      {playhead < events.length && (
                        <div className="sl-future">
                          {events.length - playhead} later events hidden until
                          you advance
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="sl-links">
                    {graphBusy ? (
                      <p>Reading declared links…</p>
                    ) : (
                      graph && (
                        <>
                          <p>
                            One-hop neighborhood of{" "}
                            <strong>{graph.seed_event_id ?? event?.id}</strong>.
                            Entire saved version; this view may include later
                            events.
                          </p>
                          <EvidenceGraph
                            data={{
                              nodes: graph.nodes.map((n) => ({
                                id: n.id,
                                source_id: n.id,
                                table: n.kind,
                                agent_id: n.actor_id,
                                excerpt: eventLabel(
                                  events.find((e) => e.id === n.id)!,
                                ),
                                metadata: {},
                                provenance: { source_ref: graph.source_ref },
                                evidence_status: "producer_declared",
                              })),
                              edges: graph.edges.map((e, i) => ({
                                id: `edge-${i}`,
                                source: e.source,
                                target: e.target,
                                type: e.relation,
                                evidence_status: "declared_reference",
                                provenance: {
                                  field: e.field,
                                  source_ref: graph.source_ref,
                                },
                              })),
                            }}
                            selected={event?.id}
                            onSelect={(r) => jump(r.id)}
                            truncated={graph.truncated}
                          />
                          <div className="sl-link-nodes">
                            {graph.nodes.map((n) => (
                              <button key={n.id} onClick={() => jump(n.id)}>
                                <span>{n.capture_position}</span>
                                <strong>{n.actor_id ?? "Unknown actor"}</strong>
                                <small>{n.kind}</small>
                              </button>
                            ))}
                          </div>
                          <h3>Field-backed links</h3>
                          {graph.edges.map((edge, i) => (
                            <button
                              className="sl-edge"
                              key={i}
                              onClick={() => jump(edge.source)}
                            >
                              <code>{edge.source}</code>
                              <span>
                                {edge.relation.replaceAll("_", " ")}
                                <small>{edge.field}</small>
                              </span>
                              <ArrowRight size={14} />
                              <code>{edge.target}</code>
                            </button>
                          ))}
                          {!graph.edges.length && (
                            <p>
                              No uniquely resolved declared references in this
                              neighborhood.
                            </p>
                          )}
                          {graph.diagnostics.length > 0 && (
                            <details open>
                              <summary>
                                {graph.diagnostics.length} unresolved or
                                conflicting references
                              </summary>
                              <Json value={graph.diagnostics} />
                            </details>
                          )}
                          {graph.truncated && (
                            <p>Display capped; more links may exist.</p>
                          )}
                          <small>
                            Links identify references, not reading, influence or
                            causation.
                          </small>
                        </>
                      )
                    )}
                  </div>
                )}
                <div className="sl-state">
                  <h3>State at event {playhead}</h3>
                  <div>
                    {(["tasks", "calls", "artifacts"] as const).map((key) => (
                      <section key={key}>
                        <h4>{key === "calls" ? "Tool receipts" : key}</h4>
                        {state[key].length ? (
                          state[key].map((item) => (
                            <button
                              key={item.id}
                              onClick={() => jump(item.event)}
                            >
                              <strong>{item.title}</strong>
                              <span>{item.status}</span>
                            </button>
                          ))
                        ) : (
                          <small>None recorded yet</small>
                        )}
                      </section>
                    ))}
                  </div>
                </div>
              </div>
              <aside className="sl-inspector">
                <div className="sl-inspector-head">
                  <span className="eyebrow">SOURCE INSPECTOR</span>
                  <strong>{event?.id ?? "No event selected"}</strong>
                </div>
                {event && (
                  <>
                    <div className="sl-field-list">
                      <span>{event.kind}</span>
                      <time>{event.occurred_at}</time>
                      <p>{audience(event)}</p>
                    </div>
                    <Json value={event.data} />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => void loadGraph(event.id)}
                    >
                      <Network size={14} />
                      Follow this event’s links
                    </Button>
                  </>
                )}
                <div className="sl-note">
                  <label htmlFor="trace-note">
                    Your interpretation or counterevidence
                  </label>
                  <textarea
                    id="trace-note"
                    value={note}
                    maxLength={2000}
                    placeholder="What would change your interpretation?"
                    onChange={(e) => setNote(e.target.value)}
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!note.trim() || !event || notes.length >= 50}
                    onClick={() => {
                      if (!event) return;
                      setNotes((n) => [
                        ...n,
                        {
                          text: note.trim(),
                          event_id: event.id,
                          kind: "human_note",
                        },
                      ]);
                      setNote("");
                    }}
                  >
                    Add to review
                  </Button>
                  <small>Notes stay in this view until exported.</small>
                  {notes.map((n, i) => (
                    <blockquote key={i}>
                      {n.text}
                      <button onClick={() => jump(n.event_id)}>
                        {n.event_id}
                      </button>
                    </blockquote>
                  ))}
                </div>
              </aside>
            </div>
            <div className="sl-review">
              <div>
                <div className="eyebrow">ASK ABOUT THIS EXACT RUN</div>
                <h2>Follow a question through the evidence</h2>
                <p>
                  The investigator receives a bounded selection and must cite
                  recorded fields. Review its sources and missing evidence.
                </p>
                <div className="sl-question">
                  <textarea
                    aria-label="Question about imported trace"
                    value={question}
                    maxLength={2000}
                    onChange={(e) => setQuestion(e.target.value)}
                  />
                  <Button
                    disabled={reviewBusy || !question.trim()}
                    onClick={() => void investigate()}
                  >
                    {reviewBusy ? (
                      <Loader2 className="animate-spin" size={16} />
                    ) : (
                      <ArrowRight size={16} />
                    )}
                    Review behavior
                  </Button>
                </div>
                {reviewBusy && (
                  <p role="status">
                    Inspecting this saved version. The result will retain its
                    exact source identity.
                  </p>
                )}
                {checks.length > 0 && (
                  <details>
                    <summary>
                      {checks.length} deterministic review leads
                    </summary>
                    {checks.map((c, i) => (
                      <div className="sl-check" key={i}>
                        <strong>
                          {String(c.title ?? c.kind ?? "Review lead")}
                        </strong>
                        <p>
                          {String(
                            c.text ??
                              c.summary ??
                              c.detail ??
                              "Inspect the referenced events before interpreting this lead.",
                          )}
                        </p>
                        {c.event_ids?.map((id) => (
                          <button key={id} onClick={() => jump(id)}>
                            {id}
                          </button>
                        ))}
                      </div>
                    ))}
                  </details>
                )}
              </div>
              <div className="sl-review-result">
                {review ? (
                  <>
                    <span className="sl-badge">
                      AI draft · human review required
                    </span>
                    <p>
                      {review.findings.length
                        ? `${review.findings.length} observations to review against their sources`
                        : review.answer}
                    </p>
                    {review.findings.map((f, i) => (
                      <article key={i}>
                        <p>{f.text}</p>
                        {f.quotes?.map((q, j) => (
                          <blockquote key={j}>
                            {q.quote}
                            <button onClick={() => jump(q.source_id)}>
                              Inspect source
                            </button>
                          </blockquote>
                        ))}
                      </article>
                    ))}
                    {review.unknowns.length > 0 && (
                      <>
                        <h3>Still unknown</h3>
                        <ul>
                          {review.unknowns.map((u, i) => (
                            <li key={i}>{u}</li>
                          ))}
                        </ul>
                      </>
                    )}
                    {(Array.isArray(review.coverage.warnings)
                      ? (review.coverage.warnings as string[])
                      : review.warnings
                    )?.map((w, i) => (
                      <p className="sl-muted" key={i}>
                        {w}
                      </p>
                    ))}
                    <details>
                      <summary>Retrieval and source coverage</summary>
                      <Json
                        value={{
                          query_plan: review.query_plan,
                          coverage: review.coverage,
                        }}
                      />
                    </details>
                    <Button
                      variant="outline"
                      onClick={() =>
                        onDraftStudy(
                          question,
                          review.findings[0]?.text ?? question,
                          {
                            id: run.id,
                            version: run.version,
                            hash: run.hash,
                            event_ids: review.sources
                              .map((s) => s.source_id)
                              .slice(0, 24),
                          },
                        )
                      }
                    >
                      <FlaskConical size={15} />
                      Draft the next study
                    </Button>
                  </>
                ) : (
                  <div className="sl-review-empty">
                    <MessageSquare size={25} />
                    <strong>From sequence to explanation</strong>
                    <p>
                      Ask about handoffs, conflicting receipts, recovery or
                      changes in behavior. A candidate is a starting point for
                      review.
                    </p>
                  </div>
                )}
              </div>
            </div>
            <div className="sl-next">
              <div>
                <strong>Turn an explanation into something testable.</strong>
                <p>
                  Explore Society Lab’s controlled document-recovery world. It
                  has new roles and declared proxy rules.
                </p>
              </div>
              <Button
                variant="outline"
                onClick={() => {
                  setPlaying(false);
                  setTab("world");
                }}
              >
                Explore test environment
                <ArrowRight size={15} />
              </Button>
            </div>
          </>
        )}
      </div>
      <footer className="sl-credit">
        Combines Swarm Mafia evidence review with{" "}
        <a
          href="https://github.com/Atharvap14/society-lab"
          target="_blank"
          rel="noreferrer"
        >
          Atharva Pandey’s Society Lab
        </a>
        : typed event intake, versioned links, replay and controlled-world
        mechanics.
      </footer>
    </section>
  );
}

function WorldSandbox({
  study,
  evidence,
}: {
  study?: Study | null;
  evidence?: unknown;
}) {
  const [world, setWorld] = useState<WorldResult | null>(null),
    [actions, setActions] = useState<WorldAction[]>([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [action, setAction] = useState(""),
    [fields, setFields] = useState<Record<string, string>>({}),
    [seed, setSeed] = useState(173);
  const generation = useRef(0);
  async function replay(next: WorldAction[], selectedSeed = seed) {
    const g = ++generation.current;
    setBusy(true);
    setError("");
    try {
      const r = await api<WorldResult>(societyPath("worlds/replay"), {
        seed: selectedSeed,
        max_rounds: 8,
        actions: next,
      });
      if (g !== generation.current) return;
      setWorld(r);
      setActions(next);
      setAction("");
      setFields({});
    } catch (e) {
      if (g === generation.current) setError(errorText(e));
    } finally {
      if (g === generation.current) setBusy(false);
    }
  }
  useEffect(() => {
    return () => {
      generation.current++;
    };
  }, []);
  const options =
    world?.action_schema?.properties?.action?.enum ??
    Object.keys(world?.action_fields ?? {});
  const fieldNames = (world?.action_fields?.[action] ?? []).filter(
    (f) => f !== "action",
  );
  return (
    <div className="sl-world">
      <div className="sl-world-intro">
        <div>
          <span className="sl-badge">Human-steered proxy · no model calls</span>
          <h2>Can the checker open the correct original?</h2>
          <p>
            One owner has a valid document reference. The checker starts with a
            broken one. Use the actual local tool mechanics to distinguish
            sending a fix, drafting a URL and verified access.
          </p>
        </div>
        <div>
          <label>
            World seed
            <input
              aria-label="World seed"
              type="number"
              min="0"
              max="9007199254740991"
              value={seed}
              disabled={busy || actions.length > 0}
              onChange={(e) => setSeed(Number(e.target.value))}
            />
          </label>
          <Button
            disabled={busy || !Number.isSafeInteger(seed) || seed < 0}
            onClick={() => void replay([])}
          >
            {world ? "Reset world" : "Start controlled world"}
          </Button>
        </div>
      </div>
      {study && (
        <div className="sl-attached">
          <strong>Study draft: {study.title}</strong>
          <p>{study.intervention}</p>
          <small>
            This world is a mechanism probe. The proposed study remains unrun;
            its fit and design need review.
          </small>
        </div>
      )}
      {error && (
        <div className="sl-error" role="alert">
          {error}
        </div>
      )}
      {world && (
        <>
          <div className="sl-world-metrics">
            <div>
              <span>Verified checker access</span>
              <strong>
                {world.outcome.verified_repaired_reference
                  ? "Recorded"
                  : "Not yet"}
              </strong>
            </div>
            <div>
              <span>Action budget</span>
              <strong>
                {world.steps_used} / {world.max_steps}
              </strong>
            </div>
            <div>
              <span>Next experimental role</span>
              <strong>{world.next_role ?? "Complete"}</strong>
            </div>
            <div>
              <span>World identity</span>
              <strong>{world.spec_hash.slice(0, 12)}</strong>
            </div>
          </div>
          <div className="sl-world-grid">
            <section>
              <h3>
                {world.next_role
                  ? `What ${world.next_role} can observe`
                  : "Final observation"}
              </h3>
              <p>
                This panel shows the role’s supplied observation. You can also
                inspect experimenter receipts below.
              </p>
              <WorldObservation observation={world.observation} />
            </section>
            <section className="sl-action-panel">
              <h3>Choose the next action</h3>
              <p>
                You control a new experimental role; these are not the
                historical agents.
              </p>
              <label>
                Tool
                <select
                  aria-label="World tool"
                  value={action}
                  disabled={busy || world.terminal}
                  onChange={(e) => {
                    setAction(e.target.value);
                    setFields({});
                  }}
                >
                  <option value="">Select a tool</option>
                  {options.map((x) => (
                    <option key={x}>{x}</option>
                  ))}
                </select>
              </label>
              {fieldNames.map((field) => (
                <label key={field}>
                  {field.replaceAll("_", " ")}
                  {world.action_schema.properties?.[field]?.enum ? (
                    <select
                      aria-label={`Action ${field}`}
                      value={fields[field] ?? ""}
                      onChange={(e) =>
                        setFields((s) => ({ ...s, [field]: e.target.value }))
                      }
                    >
                      <option value="">Choose…</option>
                      {world.action_schema.properties[field].enum!.map((x) => (
                        <option key={x}>{x}</option>
                      ))}
                    </select>
                  ) : (
                    <textarea
                      aria-label={`Action ${field}`}
                      maxLength={4000}
                      value={fields[field] ?? ""}
                      onChange={(e) =>
                        setFields((s) => ({ ...s, [field]: e.target.value }))
                      }
                    />
                  )}
                </label>
              ))}
              <Button
                disabled={
                  busy ||
                  world.terminal ||
                  !world.next_role ||
                  !action ||
                  fieldNames.some((f) => !fields[f]?.trim())
                }
                onClick={() =>
                  void replay([
                    ...actions,
                    { role: world.next_role!, action: { action, ...fields } },
                  ])
                }
              >
                {busy ? (
                  <Loader2 className="animate-spin" size={15} />
                ) : (
                  <ArrowRight size={15} />
                )}
                Execute local action
              </Button>
              <p className="sl-muted">
                Every action, including a failed action, consumes a turn.
                Messages and status reports alone do not satisfy the
                checker-access goal.
              </p>
              <Button
                variant="outline"
                disabled={busy || !actions.length}
                onClick={() => void replay(actions.slice(0, -1))}
              >
                Replay without last action
              </Button>
            </section>
          </div>
          <div className="sl-world-receipts">
            <h3>Executed receipts</h3>
            {world.events.map((e, i) => (
              <details key={i} open={i === world.events.length - 1}>
                <summary>
                  {String(e.type)} · {String(e.agent_id ?? "scenario")} ·{" "}
                  {String(
                    (e.action as Record<string, unknown>)?.action ??
                      "Initial condition",
                  )}
                </summary>
                <Json value={e} />
              </details>
            ))}
          </div>
          <div className="sl-next">
            <div>
              <strong>Keep the experiment’s boundaries with its result.</strong>
              <p>
                This run checks proxy mechanics. It does not measure how an LLM
                or the original agents respond.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() =>
                download("society-world-run.json", {
                  schema_version: "swarm-mafia.world-review.v1",
                  evidence_ref: evidence,
                  study_draft: study,
                  actions,
                  result: world,
                  status: "human_steered_proxy_not_causal_experiment",
                })
              }
            >
              <Download size={15} />
              Export world run
            </Button>
          </div>
          <details className="sl-world-limits">
            <summary>World rules, provenance and limitations</summary>
            <ul>
              {world.limitations.map((l, i) => (
                <li key={i}>{l}</li>
              ))}
            </ul>
            <Json
              value={{
                provenance: world.provenance,
                spec: world.spec,
                outcome: world.outcome,
              }}
            />
          </details>
        </>
      )}
    </div>
  );
}

function WorldObservation({
  observation,
}: {
  observation: Record<string, unknown> | null;
}) {
  if (!observation)
    return (
      <p>
        The action budget is complete. Inspect the receipts and export this run.
      </p>
    );
  const object = (value: unknown): Record<string, unknown> =>
    value && typeof value === "object" && !Array.isArray(value)
      ? (value as Record<string, unknown>)
      : {};
  const target = object(observation.target_document);
  const browser = object(observation.browser);
  const receipt = object(observation.your_last_tool_result);
  const messages = Array.isArray(observation.received_messages)
    ? observation.received_messages
    : [];
  const reference =
    target.canonical_url ??
    target.canonical_reference ??
    target.your_copied_reference;
  return (
    <div className="sl-observation">
      <div className="sl-observation-goal">
        <span>Shared goal</span>
        <p>{String(observation.task ?? "No goal supplied")}</p>
      </div>
      <dl>
        <dt>Target document</dt>
        <dd>{String(target.title ?? "Unknown")}</dd>
        {reference != null && (
          <>
            <dt>Reference supplied to this role</dt>
            <dd>
              <code>{String(reference)}</code>
            </dd>
          </>
        )}
        <dt>Browser address draft</dt>
        <dd>
          <code>{String(browser.draft_url || "None")}</code>
        </dd>
        <dt>Last navigated address</dt>
        <dd>
          <code>{String(browser.committed_url || "None")}</code>
        </dd>
        <dt>Last tool result</dt>
        <dd>
          {receipt.ok === true
            ? "Succeeded"
            : receipt.ok === false
              ? "Failed"
              : "No result"}
          {receipt.status_code != null
            ? ` · ${String(receipt.status_code)}`
            : ""}
          {receipt.error ? ` · ${String(receipt.error)}` : ""}
        </dd>
      </dl>
      <details open={messages.length > 0}>
        <summary>Received messages ({messages.length})</summary>
        {messages.length ? (
          <Json value={messages} />
        ) : (
          <p>No messages supplied to this role.</p>
        )}
      </details>
      <details>
        <summary>Complete role observation</summary>
        <Json value={observation} />
      </details>
    </div>
  );
}
