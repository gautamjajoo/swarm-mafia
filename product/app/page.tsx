"use client";
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import {
  Network,
  Search,
  BookOpen,
  FlaskConical,
  Terminal,
  Database,
  ArrowUpRight,
  ShieldCheck,
  Clock3,
  Sparkles,
  ArrowUp,
  Loader2,
  Pin,
  Download,
  Save,
  Plus,
  X,
  ChevronRight,
  FileText,
  MessageSquare,
  ListFilter,
  Check,
  AlertCircle,
  Quote,
  Braces,
  ScanLine,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Patterns, Pattern } from "@/components/observatory/patterns";
import { EvidenceGraph } from "@/components/observatory/evidence-graph";
import { Reports } from "@/components/observatory/reports";
import { ReviewPath } from "@/components/observatory/review-path";
import { SocietyLab } from "@/components/society/lab";
import { followReview } from "@/lib/reviews";
import type { BehaviorReport } from "@/lib/reports";
import {
  api,
  evidencePath,
  dateLabel,
  humanize,
  label,
  download,
  sourceNames,
  Source,
  RecordItem,
  Envelope,
  Coverage,
  GraphData,
  SequenceData,
  Message,
  Note,
  Study,
  Pin as PinType,
  Saved,
  WorkspaceState,
  PatternFocus,
  InvestigationResult,
  ReviewJob,
} from "@/lib/evidence";

type View = "explore" | "saved" | "studies" | "access" | "patterns" | "reports" | "society";
const initialFilters = { agent_id: "", table: "", from: "", to: "" };
const emptyStudy = (): Study => ({
  id: crypto.randomUUID(),
  title: "",
  intervention: "",
  metric: "",
  control: "",
  guardrail: "",
  status: "proposed_unrun",
});
const examples = [
  {
    q: "correction",
    ask: "Find examples where an agent corrected another agent. What happened afterward, and what remains unknown?",
    title: "Follow a correction",
    detail: "From feedback to the next recorded action",
  },
  {
    q: "help",
    ask: "Find a task involving multiple agents. Show the recorded handoffs and any ambiguity about who was responsible.",
    title: "Trace a handoff",
    detail: "Who asked, who responded, what followed",
  },
  {
    q: "error",
    ask: "Find a tool failure and inspect how the agent responded. Separate observed recovery from assumed success.",
    title: "Inspect a recovery",
    detail: "A failure, the response, and the evidence",
  },
];
function errorText(e: unknown) {
  return e instanceof Error
    ? e.message
    : "Something went wrong. Your work is still here.";
}
function SourceTag({ type }: { type?: string }) {
  return (
    <span
      className={`evidence-tag ${type === "secondary_generated" ? "secondary" : ""}`}
    >
      {type === "secondary_generated" ? "Generated summary" : "Source record"}
    </span>
  );
}
function num(n?: number) {
  return typeof n === "number" ? n.toLocaleString() : "—";
}
export default function Home() {
  const [source, setSource] = useState<Source>("ai-village"),
    [view, setView] = useState<View>("explore"),
    [labStudy, setLabStudy] = useState<Study | null>(null),
    [labOpened, setLabOpened] = useState(false),
    [reportId, setReportId] = useState<string | null>(null),
    [query, setQuery] = useState(""),
    [filters, setFilterState] =
      useState<Record<string, string>>(initialFilters),
    [showFilters, setShowFilters] = useState(false);
  const [stats, setStats] = useState<Envelope<unknown> | null>(null),
    [agents, setAgents] = useState<RecordItem[]>([]),
    [records, setRecords] = useState<RecordItem[]>([]),
    [result, setResult] = useState<Envelope<RecordItem[]> | null>(null),
    [selected, setSelected] = useState<RecordItem | null>(null),
    [graph, setGraph] = useState<Envelope<GraphData> | null>(null),
    [graphSeed, setGraphSeed] = useState<string | undefined>(),
    [tab, setTab] = useState<"records" | "graph" | "timeline" | "context">(
      "records",
    ),
    [sequence, setSequence] = useState<Envelope<SequenceData> | null>(null),
    [started, setStarted] = useState(false),
    [patternFocus, setPatternFocus] = useState<PatternFocus | undefined>();
  const [messages, setMessages] = useState<Message[]>([]),
    [question, setQuestion] = useState(""),
    [pins, setPins] = useState<PinType[]>([]),
    [notes, setNotes] = useState<Note[]>([]),
    [studies, setStudies] = useState<Study[]>([]),
    [noteText, setNoteText] = useState(""),
    [noteTarget, setNoteTarget] = useState<{
      text: string;
      source_ids: string[];
    } | null>(null),
    [submittedQuery, setSubmittedQuery] = useState(""),
    [noteKind, setNoteKind] = useState<Note["evidence_status"]>("observation"),
    [rightTab, setRightTab] = useState<"assistant" | "notebook">("assistant");
  const [loading, setLoading] = useState(""),
    [thinking, setThinking] = useState(false),
    [deepReview, setDeepReview] = useState(true),
    [reviewJob, setReviewJob] = useState<ReviewJob | null>(null),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [dirty, setDirty] = useState(false),
    [active, setActive] = useState<Saved | null>(null),
    [saved, setSaved] = useState<Saved[]>([]),
    [savedStatus, setSavedStatus] = useState<"idle" | "loading" | "loaded" | "error">("idle"),
    [savedError, setSavedError] = useState(""),
    [saveOpen, setSaveOpen] = useState(false),
    [title, setTitle] = useState(""),
    [saving, setSaving] = useState(false),
    [study, setStudy] = useState<Study | null>(null),
    [showMeta, setShowMeta] = useState(false),
    [raw, setRaw] = useState<Envelope<{
      raw_json: string;
      hash_verified: boolean;
      record_bytes: number;
      bytes_returned: number;
    }> | null>(null);
  const epoch = useRef(0),
    savedEpoch = useRef(0),
    investigationEpoch = useRef(0),
    openEpoch = useRef(0),
    thinkingRef = useRef(false),
    analysisRequest = useRef<{
      controller: AbortController;
      question: string;
      jobId?: string;
    } | null>(null),
    stateFingerprint = useRef(""),
    selectionEpoch = useRef(0),
    chatEnd = useRef<HTMLDivElement>(null),
    actions = useRef<
      Record<string, (input: Record<string, unknown>) => Promise<unknown>>
    >({});
  function setFilters(
    update:
      | Record<string, string>
      | ((old: Record<string, string>) => Record<string, string>),
  ) {
    setFilterState(update);
    epoch.current++;
    selectionEpoch.current++;
    setRecords([]);
    setSelected(null);
    setGraph(null);
    setResult(null);
    setRaw(null);
    setSequence(null);
    setDirty(true);
  }
  const snapshot = stats?.snapshot || result?.snapshot || "unknown";
  const currentState = useCallback(
    (): WorkspaceState => ({
      pattern: patternFocus,
      query,
      filters,
      pins,
      notes,
      studies,
      messages,
      selected_id: selected?.id,
      graph_seed: graphSeed,
      context_seed: sequence?.data.seed,
      context_mode: sequence?.data.scope.mode === "actor" ? "actor" : "source",
      tab,
    }),
    [
      query,
      filters,
      pins,
      notes,
      studies,
      messages,
      selected,
      graphSeed,
      patternFocus,
      sequence,
      tab,
    ],
  );
  useLayoutEffect(() => {
    stateFingerprint.current = JSON.stringify(currentState());
  }, [currentState]);
  useEffect(() => {
    const handler = (event: BeforeUnloadEvent) => {
      if (dirty) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);
  useEffect(() => {
    let live = true;
    Promise.all([
      api<Envelope<unknown>>(evidencePath("stats", source)),
      api<Envelope<RecordItem[]>>(evidencePath("agents", source)),
    ])
      .then(([s, a]) => {
        if (live) {
          setStats(s);
          setAgents(Array.isArray(a.data) ? a.data : []);
        }
      })
      .catch((e) => {
        if (live) setError(errorText(e));
      });
    return () => {
      live = false;
    };
  }, [source]);
  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages, thinking]);
  async function refreshSaved() {
    const generation = ++savedEpoch.current;
    setSavedStatus("loading");
    setSavedError("");
    try {
      const r = await api<{ data: Saved[] }>("/api/investigations");
      if (generation !== savedEpoch.current) return;
      setSaved(r.data);
      setSavedStatus("loaded");
    } catch (e) {
      if (generation !== savedEpoch.current) return;
      setSavedError(errorText(e));
      setSavedStatus("error");
    }
  }
  async function search(q = query, chosenTab = tab, append = false) {
    const generation = ++epoch.current;
    setStarted(true);
    setView("explore");
    setError("");
    setLoading("search");
    const p = {
      ...filters,
      q: chosenTab === "timeline" ? "" : append ? submittedQuery : q,
      limit: "30",
      cursor: append ? String(result?.next_cursor || 0) : "0",
    };
    try {
      const response = await api<Envelope<RecordItem[]>>(
        evidencePath(
          chosenTab === "timeline" ? "timeline" : "search",
          source,
          p,
        ),
      );
      if (generation !== epoch.current) return;
      setRecords((old) =>
        append ? [...old, ...response.data] : response.data,
      );
      setResult(response);
      if (!append) setSubmittedQuery(q);
      setStats((old) => ({ ...response, data: old?.data }));
      return response;
    } catch (e) {
      if (generation === epoch.current) setError(errorText(e));
      throw e;
    } finally {
      if (generation === epoch.current) setLoading("");
    }
  }
  async function inspect(record: RecordItem | string, expand = false) {
    const generation = ++selectionEpoch.current;
    setError("");
    setShowMeta(false);
    setRaw(null);
    try {
      let item: RecordItem;
      if (typeof record === "string") {
        const [table, ...rest] = record.split(":");
        const r = await api<Envelope<RecordItem>>(
          evidencePath(
            `records/${encodeURIComponent(table)}/${encodeURIComponent(rest.join(":"))}`,
            source,
          ),
        );
        item = r.data;
      } else item = record;
      if (generation !== selectionEpoch.current) return;
      setSelected(item);
      if (expand) {
        setLoading("graph");
        const g = await api<Envelope<GraphData>>(
          evidencePath("graph", source, {
            seed: item.id,
            hops: "1",
            limit: "35",
          }),
        );
        if (generation === selectionEpoch.current) {
          setGraph(g);
          setGraphSeed(item.id);
          setTab("graph");
        }
      }
      return item;
    } catch (e) {
      if (generation === selectionEpoch.current) setError(errorText(e));
      throw e;
    } finally {
      if (generation === selectionEpoch.current) setLoading("");
    }
  }
  async function surrounding(item: RecordItem, mode = "source") {
    const generation = ++epoch.current,
      selectionGeneration = selectionEpoch.current;
    setLoading("context");
    setError("");
    try {
      const data = await api<Envelope<SequenceData>>(
        evidencePath("context", source, {
          seed: item.id,
          before: "8",
          after: "8",
          mode,
        }),
      );
      if (
        generation !== epoch.current ||
        selectionGeneration !== selectionEpoch.current
      )
        return;
      setSequence(data);
      setTab("context");
      setSelected(item);
    } catch (e) {
      if (generation === epoch.current) setError(errorText(e));
    } finally {
      if (generation === epoch.current) setLoading("");
    }
  }
  async function openPattern(
    p: Pattern,
    envelope: Envelope<{ kind: string; definition: string; built_at: string }>,
  ) {
    setView("explore");
    setStarted(true);
    setFilters(initialFilters);
    setQuery("");
    setTab("records");
    setLoading("search");
    setError("");
    const generation = investigationEpoch.current,
      scopeGeneration = epoch.current,
      selectedGeneration = selectionEpoch.current;
    const current = () =>
      generation === investigationEpoch.current &&
      scopeGeneration === epoch.current &&
      selectedGeneration === selectionEpoch.current;
    try {
      const samples = await Promise.all(
        p.source_ids.slice(0, 8).map((id) => {
          const [t, ...rest] = id.split(":");
          return api<Envelope<RecordItem>>(
            evidencePath(
              `records/${encodeURIComponent(t)}/${encodeURIComponent(rest.join(":"))}`,
              source,
            ),
          );
        }),
      );
      if (!current()) return;
      const rows = samples.map((s) => s.data);
      setRecords(rows);
      setPatternFocus({
        id: p.id,
        rule: envelope.data.kind,
        definition: envelope.data.definition,
        source_ids: p.source_ids,
        count: p.count,
        share: p.share,
        built_at: envelope.data.built_at,
      });
      const anchors = [rows[0], rows.at(-1)].filter(
        (r): r is RecordItem => !!r,
      );
      setPins((old) =>
        [
          ...anchors.map((r) => ({
            id: r.id,
            excerpt: r.excerpt,
            provenance: r.provenance,
            label: label(r),
            source,
            excerpt_truncated: r.excerpt_truncated,
          })),
          ...old.filter((p) => !anchors.some((r) => r.id === p.id)),
        ].slice(0, 30),
      );
      setSelected(rows[0] || null);
      setResult({
        ...envelope,
        data: rows,
        truncated: true,
        next_cursor: null,
      });
      setQuestion(
        "Compare these pattern examples in their surrounding context. What is directly observable, which explanations compete, and what remains unknown? Do not assume repetition or message volume is a failure.",
      );
      setRightTab("assistant");
      setDirty(true);
      setNotice(
        "Loaded a bounded pattern sample and pinned its first and last examples as AI focus. Counts describe source records, not unique actions.",
      );
    } catch (e) {
      if (current()) setError(errorText(e));
    } finally {
      if (current()) setLoading("");
    }
  }
  async function ask(text = question) {
    if (!text.trim() || thinkingRef.current) return;
    if (messages.length >= 28) {
      setError(
        "This investigation has reached its conversation limit. Save it and start a new investigation to continue.",
      );
      return;
    }
    const generation = investigationEpoch.current,
      evidenceGeneration = epoch.current;
    thinkingRef.current = true;
    const controller = new AbortController();
    analysisRequest.current = { controller, question: text };
    setStarted(true);
    setView("explore");
    setRightTab("assistant");
    setThinking(true);
    setReviewJob(null);
    setError("");
    setQuestion("");
    setDirty(true);
    const history = messages
      .slice(-12)
      .map((m) => ({ role: m.role, content: m.content.slice(0, 1500) }));
    setMessages((m) => [...m, { role: "user", content: text }]);
    let latestReviewJob: ReviewJob | null = null;
    try {
      const initial = await api<InvestigationResult | ReviewJob>(
        evidencePath(deepReview ? "reviews" : "investigate", source),
        {
          question: text,
          history,
          context: {
            filters: {
              source,
              agent_id: filters.agent_id,
              table: filters.table,
              from_time: filters.from,
              to_time: filters.to,
            },
            corrections: notes
              .filter(
                (n) =>
                  n.evidence_status === "counterevidence" ||
                  n.review_status === "disputed",
              )
              .slice(-6)
              .map(
                (n) =>
                  n.text +
                  (n.target_claim
                    ? "\nRegarding AI draft: " +
                      n.target_claim +
                      "\nSources: " +
                      (n.source_ids || []).join(", ")
                    : ""),
              ),
            source_ids: [
              ...new Set([
                ...(selected ? [selected.id] : []),
                ...pins.map((p) => p.id),
              ]),
            ].slice(0, 2),
          },
        },
        "POST",
        controller.signal,
      );
      let response: InvestigationResult;
      if (deepReview) {
        const job = initial as ReviewJob;
        latestReviewJob = job;
        if (generation !== investigationEpoch.current || controller.signal.aborted) {
          void api(`/api/evidence/reviews/${encodeURIComponent(job.id)}`, {}, "DELETE").catch(() => {});
          return;
        }
        if (analysisRequest.current) analysisRequest.current.jobId = job.id;
        response = await followReview(job, controller.signal, (update) => {
          latestReviewJob = update;
          if (generation === investigationEpoch.current) setReviewJob(update);
        }, (id) => api<ReviewJob>(`/api/evidence/reviews/${encodeURIComponent(id)}`, undefined, "GET", controller.signal));
      } else response = initial as InvestigationResult;
      if (generation !== investigationEpoch.current) return;
      setMessages((m) => [
        ...m,
        { role: "assistant", content: response.answer, result: response },
      ]);
      if (evidenceGeneration === epoch.current && response.sources?.length) {
        const cited = new Set(response.findings.flatMap(f => f.source_ids));
        const ordered = [...response.sources].sort((a, b) =>
          Number(cited.has(b.id)) - Number(cited.has(a.id)) ||
          Number(!!b.field_segments?.some(s => s.field !== "indexed_excerpt")) - Number(!!a.field_segments?.some(s => s.field !== "indexed_excerpt")));
        setRecords((current) => (current.length ? current : ordered));
      }
      return response;
    } catch (e) {
      if (generation === investigationEpoch.current) {
        if (latestReviewJob?.progress.length) {
          const failed: InvestigationResult = {
            status: "failed", answer: errorText(e), findings: [], sources: [],
            unknowns: ["This review did not complete. Its retrieval steps are retained below; no completed behavioral assessment is available."],
            suggested_followups: [], proposed_tests: [], coverage: { exhaustive: false },
            progress: latestReviewJob.progress,
          };
          setMessages((m) => [...m, { role: "assistant", content: failed.answer, result: failed }]);
        } else setMessages((m) => m.slice(0, -1));
        setQuestion(text);
        setError(errorText(e));
      }
    } finally {
      if (generation === investigationEpoch.current) {
        thinkingRef.current = false;
        analysisRequest.current = null;
        setThinking(false);
      }
    }
  }
  function cancelAnalysis() {
    const request = analysisRequest.current;
    if (!request) return;
    investigationEpoch.current++;
    request.controller.abort();
    if (request.jobId) void api(`/api/evidence/reviews/${encodeURIComponent(request.jobId)}`, {}, "DELETE").catch(() => {});
    analysisRequest.current = null;
    thinkingRef.current = false;
    setThinking(false);
    setQuestion((current) => (current.trim() ? current : request.question));
    setMessages((old) => old.slice(0, -1));
    setNotice(
      "Review stopped. Refine your question and run it again. A model request already sent may still finish, but no further investigation steps are requested.",
    );
  }
  function pin(r: RecordItem) {
    if (pins.length >= 30 && !pins.some((p) => p.id === r.id)) {
      setError(
        "This investigation already has 30 pins. Remove one before adding another.",
      );
      return;
    }
    setPins((old) =>
      old.some((p) => p.id === r.id)
        ? old
        : [
            ...old,
            {
              id: r.id,
              excerpt: r.excerpt,
              provenance: r.provenance,
              label: label(r),
              source,
              excerpt_truncated: r.excerpt_truncated,
            },
          ].slice(0, 30),
    );
    setDirty(true);
    setNotice("Pinned to this investigation. Save to keep it across sessions.");
  }
  function clearDrafts() {
    if (analysisRequest.current?.jobId) void api(`/api/evidence/reviews/${encodeURIComponent(analysisRequest.current.jobId)}`, {}, "DELETE").catch(() => {});
    analysisRequest.current?.controller.abort();
    setReviewJob(null);
    analysisRequest.current = null;
    setQuestion("");
    setNoteText("");
    setNoteTarget(null);
    setNoteKind("observation");
    setStudy(null);
    setSaveOpen(false);
    setRaw(null);
    setShowMeta(false);
    setRightTab("assistant");
    setGraphSeed(undefined);
    setPatternFocus(undefined);
  }
  function reset(nextSource = source) {
    if (
      dirty &&
      !window.confirm(
        "Start a new investigation? Unsaved notes and findings will be cleared. Save or export first to keep them.",
      )
    )
      return false;
    epoch.current++;
    selectionEpoch.current++;
    investigationEpoch.current++;
    openEpoch.current++;
    thinkingRef.current = false;
    setThinking(false);
    clearDrafts();
    setTitle("");
    setSubmittedQuery("");
    setLoading("");
    if (nextSource !== source) {
      setStats(null);
      setAgents([]);
    }
    setSource(nextSource);
    setActive(null);
    setQuery("");
    setFilters(initialFilters);
    setRecords([]);
    setResult(null);
    setSequence(null);
    setSelected(null);
    setGraph(null);
    setMessages([]);
    setPins([]);
    setNotes([]);
    setStudies([]);
    setStarted(false);
    setDirty(false);
    setError("");
    setNotice("");
    setView("explore");
    setTab("records");
    return true;
  }
  async function openReport(report: BehaviorReport, chosenIds?: string[], question?: string) {
    if (!reset(report.source)) return;
    setReportId(report.id);
    const ids = [...new Set(chosenIds?.length ? chosenIds : report.timeline.map(e => e.id))].slice(0, 16);
    setStarted(true);
    setTitle(report.title);
    setFilters({ ...initialFilters, from: report.from, to: report.to });
    setQuestion(question || report.question);
    setLoading("report");
    const generation = investigationEpoch.current, scopeGeneration = epoch.current, selectedGeneration = selectionEpoch.current;
    const current = () => generation === investigationEpoch.current && scopeGeneration === epoch.current && selectedGeneration === selectionEpoch.current;
    try {
      const samples = await Promise.all(ids.map(id => {
        const [table, ...rest] = id.split(":");
        return api<Envelope<RecordItem>>(evidencePath(`records/${encodeURIComponent(table)}/${encodeURIComponent(rest.join(":"))}`, report.source));
      }));
      if (!current()) return;
      if (samples.some(s => s.snapshot !== report.snapshot)) throw new Error("The source snapshot differs from this report. Review its archived source pointers before continuing.");
      const rows = samples.map(s => s.data);
      setRecords(rows);
      setResult({ ...samples[0], data: rows, truncated: true, next_cursor: null });
      setSelected(rows[0] || null);
      setPins(rows.slice(0, 2).map(r => ({ id: r.id, excerpt: r.excerpt, provenance: r.provenance, label: label(r), source: report.source, excerpt_truncated: r.excerpt_truncated })));
      setNotes([{ id: crypto.randomUUID(), text: `Curated report: ${report.title} (${report.id}). This is an analyst-selected episode, not a population estimate. ${report.finding} Treat the report interpretation as a hypothesis to review against sources.`.slice(0, 1500), source_ids: ids, evidence_status: "hypothesis", review_status: "human_note", created_at: new Date().toISOString() }, ...report.timeline.filter(e => ids.includes(e.id)).map(e => ({ id: crypto.randomUUID(), record_id: e.id, text: `Captured report evidence: ${e.title}\n${e.quote.slice(0, 1100)}${e.quote.length > 1100 ? " [quote shortened; see full report export]" : ""}\nSource row hash checked in the report. Current AI retrieval uses bounded indexed excerpts and may omit this passage.`.slice(0, 1500), source_ids: [e.id], evidence_status: "observation" as const, review_status: "human_note" as const, created_at: new Date().toISOString() }))]);
      setDirty(true);
      setNotice(`Opened ${rows.length} report anchors in a new, unsaved investigation. ${Math.min(2, rows.length)} are pinned as AI focus; no model has run. Captured quotes are in the Notebook; the AI may see shorter indexed excerpts. Save to retain your review.`);
    } catch (e) {
      if (current()) setError(errorText(e));
    } finally {
      if (current()) setLoading("");
    }
  }
  async function save(saveTitle = title) {
    if (!saveTitle.trim()) return;
    if (thinkingRef.current || saving) {
      setError("Wait for the current operation to finish before saving.");
      return;
    }
    const generation = investigationEpoch.current;
    const fingerprint = stateFingerprint.current;
    const state = currentState();
    // Evidence stays addressable by immutable source IDs. Avoid duplicating every
    // retrieved record in each saved turn; citations and matched quotes remain.
    state.messages = state.messages.map((m) =>
      m.result ? { ...m, result: { ...m.result, sources: [] } } : m,
    );
    setSaving(true);
    setError("");
    try {
      const r = await api<{ id: string; revision: number; updated_at: string }>(
        active ? `/api/investigations/${active.id}` : "/api/investigations",
        {
          title: saveTitle.trim(),
          source,
          snapshot,
          state,
          revision: active?.revision,
        },
        active ? "PUT" : "POST",
      );
      if (generation !== investigationEpoch.current) return r;
      setActive({ ...r, title: saveTitle.trim(), source, snapshot });
      setDirty(fingerprint !== stateFingerprint.current);
      setSaveOpen(false);
      setNotice("Investigation saved to your private workspace.");
      await refreshSaved();
      return r;
    } catch (e) {
      if (generation === investigationEpoch.current) setError(errorText(e));
    } finally {
      setSaving(false);
    }
  }
  async function openSaved(id: string) {
    if (
      dirty &&
      !window.confirm(
        "Open saved investigation and discard unsaved changes? Export or save first to keep them.",
      )
    )
      return;
    const requestGeneration = ++openEpoch.current;
    setLoading("saved");
    try {
      const s = await api<Saved>(`/api/investigations/${id}`);
      if (requestGeneration !== openEpoch.current) return;
      if (!s.state) throw new Error("Saved investigation has no state");
      epoch.current++;
      selectionEpoch.current++;
      investigationEpoch.current++;
      thinkingRef.current = false;
      setThinking(false);
      clearDrafts();
      setError("");
      setActive(s);
      if (s.source !== source) {
        setStats(null);
        setAgents([]);
      }
      setSource(s.source);
      setQuery(s.state.query);
      setFilters({ ...initialFilters, ...s.state.filters });
      setPins(s.state.pins);
      setNotes(s.state.notes);
      setStudies(s.state.studies);
      setPatternFocus(s.state.pattern);
      setMessages(s.state.messages);
      setTitle(s.title);
      setRecords([]);
      setSelected(null);
      setGraph(null);
      setResult(null);
      setSequence(null);
      setStarted(true);
      setDirty(false);
      setView("explore");
      setNotice("Saved investigation restored. Refreshing its source view…");
      const restoredGeneration = investigationEpoch.current,
        restoredScope = epoch.current,
        restoredSelection = selectionEpoch.current;
      const current = () =>
        restoredGeneration === investigationEpoch.current &&
        requestGeneration === openEpoch.current &&
        restoredScope === epoch.current &&
        restoredSelection === selectionEpoch.current;
      const restoredTab = s.state.tab || "records";
      // Restore the exact source view independently of a broad search. A busy
      // search must not prevent inspecting an already saved source pointer.
      if (s.state.selected_id) {
        const [t, ...rest] = s.state.selected_id.split(":");
        const record = await api<Envelope<RecordItem>>(
          evidencePath(
            `records/${encodeURIComponent(t)}/${encodeURIComponent(rest.join(":"))}`,
            s.source,
          ),
        );
        if (!current()) return;
        setSelected(record.data);
      }
      const contextSeed = s.state.context_seed || s.state.selected_id;
      if (restoredTab === "graph" && s.state.graph_seed) {
        const graph = await api<Envelope<GraphData>>(
          evidencePath("graph", s.source, {
            seed: s.state.graph_seed,
            hops: "1",
            limit: "35",
          }),
        );
        if (!current()) return;
        setGraph(graph);
        setGraphSeed(s.state.graph_seed);
        setTab("graph");
      } else if (
        restoredTab === "context" &&
        contextSeed &&
        s.source === "ai-village"
      ) {
        const seq = await api<Envelope<SequenceData>>(
          evidencePath("context", s.source, {
            seed: contextSeed,
            before: "8",
            after: "8",
            mode: s.state.context_mode || "source",
          }),
        );
        if (!current()) return;
        setSequence(seq);
        setTab("context");
      } else {
        const timeline =
          restoredTab === "timeline" && s.source === "ai-village";
        const loaded = await api<Envelope<RecordItem[]>>(
          evidencePath(timeline ? "timeline" : "search", s.source, {
            ...s.state.filters,
            q: timeline ? "" : s.state.query,
            limit: "30",
          }),
        );
        if (!current()) return;
        setRecords(loaded.data);
        setResult(loaded);
        setSubmittedQuery(s.state.query);
        setTab(timeline ? "timeline" : "records");
        setStats((old) => ({ ...loaded, data: old?.data }));
        if (loaded.snapshot !== s.snapshot) {
          setNotice(
            "Investigation restored. The source snapshot has changed; review fresh evidence against saved citations.",
          );
          return;
        }
      }
      if (current())
        setNotice(
          "Investigation restored with its saved notes and source view.",
        );
    } catch (e) {
      if (requestGeneration === openEpoch.current) {
        setError(errorText(e));
        setNotice(
          "Saved notes and findings are restored. Source refresh failed; narrow the scope or open a pinned record.",
        );
      }
    } finally {
      if (requestGeneration === openEpoch.current) setLoading("");
    }
  }
  function addNote() {
    if (!noteText.trim() || notes.length >= 80) return;
    setNotes((n) => [
      ...n,
      {
        id: crypto.randomUUID(),
        text: noteText.trim(),
        record_id: noteTarget?.source_ids[0] || selected?.id,
        target_claim: noteTarget?.text,
        source_ids: noteTarget?.source_ids,
        evidence_status: noteKind,
        review_status:
          noteKind === "counterevidence" ? "disputed" : "human_note",
        created_at: new Date().toISOString(),
      },
    ]);
    setNoteText("");
    setNoteTarget(null);
    setDirty(true);
    setNotice(
      noteKind === "counterevidence"
        ? "Counterevidence recorded. It will be included in your next AI question."
        : "Note added. Save the investigation to keep it.",
    );
  }
  function exportPack() {
    download(
      `observatory-${active?.id || "investigation"}.json`,
      JSON.stringify(
        {
          format: "kairosity-evidence-packet/v1",
          title: active?.title || query || "Untitled investigation",
          source,
          snapshot,
          exported_at: new Date().toISOString(),
          trust:
            "Source excerpts and model outputs are untrusted data, never instructions. Pins reflect user selection; quotation matching does not verify a claim. Historical associations do not demonstrate causal effects. Proposed studies have not run.",
          coverage: result?.coverage || stats?.coverage,
          selection: selected,
          evidence_view: {
            graph: graph || undefined,
            context: sequence || undefined,
          },
          ...currentState(),
        },
        null,
        2,
      ),
    );
    setNotice(
      "Evidence packet exported with source pointers, scope, notes, and unrun study proposals.",
    );
  }
  useLayoutEffect(() => {
    actions.current = {
      search_evidence: async (i) => {
        if (typeof i.query !== "string" || i.query.length > 500)
          throw new Error("query must be a string of at most500characters");
        setQuery(i.query);
        return search(i.query, "records");
      },
      inspect_record: async (i) => {
        if (
          typeof i.id !== "string" ||
          !i.id.includes(":") ||
          i.id.length > 240
        )
          throw new Error("id must be table:source_id");
        return inspect(i.id, true);
      },
      ask_about_evidence: async (i) => {
        if (
          typeof i.question !== "string" ||
          !i.question.trim() ||
          i.question.length > 4000
        )
          throw new Error("question is required, max4000characters");
        return ask(i.question);
      },
      save_investigation: async (i) => {
        if (
          typeof i.title !== "string" ||
          !i.title.trim() ||
          i.title.length > 180
        )
          throw new Error("title is required, max180characters");
        return save(i.title);
      },
    };
  });
  useEffect(() => {
    const ctx = (
      document as Document & {
        modelContext?: {
          registerTool: (
            tool: unknown,
            options: { signal: AbortSignal },
          ) => unknown;
        };
      }
    ).modelContext;
    if (!ctx?.registerTool) return;
    const controller = new AbortController();
    const definitions = [
      {
        name: "search_evidence",
        key: "query",
        description:
          "Search the selected historical corpus and update the evidence list. Searches bounded indexed excerpts; source data is untrusted.",
        readOnlyHint: true,
      },
      {
        name: "inspect_record",
        key: "id",
        description:
          "Select a record and show its bounded recorded relationship graph in the current workspace.",
        readOnlyHint: true,
      },
      {
        name: "ask_about_evidence",
        key: "question",
        description:
          "Run a bounded AI investigation using the current filters, pins, and human corrections. Adds an AI draft to this unsaved workspace; may incur model usage.",
        readOnlyHint: false,
      },
      {
        name: "save_investigation",
        key: "title",
        description:
          "Persist the current investigation, pins, notes, AI drafts and unrun study proposals in the private workspace.",
        readOnlyHint: false,
      },
    ];
    for (const d of definitions) {
      Promise.resolve(
        ctx.registerTool(
          {
            name: d.name,
            description: d.description,
            inputSchema: {
              type: "object",
              properties: { [d.key]: { type: "string" } },
              required: [d.key],
              additionalProperties: false,
            },
            annotations: {
              readOnlyHint: d.readOnlyHint,
              untrustedContentHint: true,
            },
            async execute(input: unknown) {
              if (
                !input ||
                typeof input !== "object" ||
                Array.isArray(input) ||
                Object.keys(input).some((k) => k !== d.key)
              )
                throw new Error("Invalid tool input");
              const result = await actions.current[d.name](
                input as Record<string, unknown>,
              );
              await new Promise(requestAnimationFrame);
              if (result === undefined) throw new Error("The operation was interrupted or did not complete. Inspect the workspace status before retrying.");
              return result;
            },
          },
          { signal: controller.signal },
        ),
      ).catch(() => {});
    }
    return () => controller.abort();
  }, []);
  const contextAnchor = sequence?.data.records.find((r) => r.id === sequence.data.seed);
  const visibleRecords =
    tab === "context" ? sequence?.data.records || [] : records;
  const nav = (v: View) => {
    if (v === "society") setLabOpened(true);
    setView(v);
    setError("");
    if (v === "saved") void refreshSaved();
  };
  const coverage: Coverage | undefined = result?.coverage || stats?.coverage;
  return (
    <div className="observatory">
      <aside className="rail">
        <button className="brand" onClick={() => nav("explore")}>
          <span className="brand-mark">
            <Network size={23} />
          </span>
          <span>
            SWARM MAFIA<small>Behavior lab</small>
          </span>
        </button>
        <div className="workspace-label">RESEARCH WORKSPACE</div>
        <nav>
          {(
            [
              { id: "explore", text: "Explore", Icon: Network },
              { id: "reports", text: "Reports", Icon: FileText },
              { id: "patterns", text: "Patterns", Icon: ScanLine },
              { id: "saved", text: "Investigations", Icon: BookOpen },
              { id: "society", text: "Trace & test lab", Icon: Network },
              { id: "studies", text: "Proposed studies", Icon: FlaskConical },
              { id: "access", text: "Agent access", Icon: Terminal },
            ] as const
          ).map((n) => (
            <Button
              key={n.id}
              variant="ghost"
              className={view === n.id ? "nav-active" : ""}
              onClick={() => nav(n.id)}
            >
              <n.Icon />
              {n.text}
              {n.id === "studies" && studies.length > 0 && (
                <span className="nav-count">{studies.length}</span>
              )}
            </Button>
          ))}
        </nav>
        <div className="rail-scope">
          <span>{view === "society" ? "LAB SOURCES" : "ACTIVE CORPUS"}</span>
          <strong>{view === "society" ? "Versioned traces & worlds" : sourceNames[source]}</strong>
          <small>
            {view === "society" ? "Observations and proxy runs stay distinct" : source === "ai-village"
              ? "Recorded activity & relationships"
              : "Artifacts & recovery ancestry"}
          </small>
          <span className="mini-status">
            <i />
            {coverage?.complete
              ? "Index ready"
              : source === "swarmtraces"
                ? "On-demand retrieval"
                : "Live index coverage"}
          </span>
        </div>
        <div className="rail-bottom">
          <ShieldCheck size={16} />
          <span>
            Private workspace<small>Evidence & controlled worlds</small>
          </span>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <span className="breadcrumb">
            Workspace <span>/</span>{" "}
            {view === "explore"
              ? active?.title || "Explore"
              : view === "reports"
                ? "Reports"
              : view === "patterns"
                ? "Patterns"
                : view === "saved"
                  ? "Investigations"
                  : view === "studies"
                    ? "Proposed studies"
                    : view === "society"
                      ? "Trace & test lab"
                    : "Agent access"}
          </span>
          <div className="top-actions">
            {dirty && <span className="unsaved">Unsaved changes</span>}
            {view === "explore" && reportId && <Button variant="ghost" size="sm" onClick={() => setView("reports")}>Return to report</Button>}
            <Button
              variant="ghost"
              size="sm"
              disabled={thinking}
              onClick={() => reset()}
            >
              <Plus size={14} />
              New
            </Button>
            <Button
              variant="outline"
              size="sm"
              aria-label="Export investigation"
              onClick={exportPack}
            >
              <Download size={14} />
              <span>Export</span>
            </Button>
            <Button
              size="sm"
              aria-label="Save investigation"
              disabled={saving || thinking}
              onClick={() => {
                setTitle(
                  active?.title ||
                    query ||
                    messages
                      .find((m) => m.role === "user")
                      ?.content.slice(0, 100) ||
                    "",
                );
                setSaveOpen(true);
              }}
            >
              <Save size={14} />
              <span>Save</span>
            </Button>
          </div>
        </header>
        {error && (
          <div className="message-banner error" role="alert">
            <AlertCircle size={16} />
            <span>
              {error}
              {error.startsWith("Sign in") && (
                <a
                  className="sign-in-link"
                  href="/signin-with-chatgpt?return_to=%2F"
                  target="_top"
                >
                  Sign in
                </a>
              )}
            </span>
            <button aria-label="Dismiss error" onClick={() => setError("")}>
              <X size={15} />
            </button>
          </div>
        )}
        {notice && (
          <div className="message-banner" role="status">
            <Check size={16} />
            <span>{notice}</span>
            <button aria-label="Dismiss message" onClick={() => setNotice("")}>
              <X size={15} />
            </button>
          </div>
        )}
        {view === "explore" && patternFocus && (
          <div className="pattern-focus">
            <ScanLine size={16} />
            <div>
              <strong>Investigating {humanize(patternFocus.rule)}</strong>
              <span>
                {patternFocus.count !== undefined
                  ? `${patternFocus.count} recorded occurrences`
                  : patternFocus.share !== undefined
                    ? `${Math.round(patternFocus.share * 100)}% share of eligible agent messages`
                    : "Pattern candidate"}{" "}
                · {patternFocus.definition}
              </span>
            </div>
            <button
              aria-label="Dismiss pattern focus"
              onClick={() => {
                setPatternFocus(undefined);
                setDirty(true);
              }}
            >
              <X size={14} />
            </button>
          </div>
        )}
        {view === "explore" && (
          <>
            <div className={`page-heading ${started ? "compact-heading" : ""}`}>
              <div>
                <div className="eyebrow">
                  {started ? "INVESTIGATION WORKSPACE" : "EXPLORE BEHAVIOR"}
                </div>
                {!started ? (
                  <>
                    <h1>
                      Start with a question.
                      <br />
                      <span>Follow the evidence.</span>
                    </h1>
                    <p>
                      Study how agents act, interact, and respond to one
                      another.
                    </p>
                  </>
                ) : (
                  <h1>{active?.title || "Follow the evidence"}</h1>
                )}
              </div>
              <label className="source-control">
                <Database size={17} />
                <select
                  aria-label="Evidence corpus"
                  value={source}
                  disabled={thinking}
                  onChange={(e) => reset(e.target.value as Source)}
                >
                  <option value="ai-village">AI Village</option>
                  <option value="swarmtraces">SwarmTraces</option>
                </select>
              </label>
            </div>
            <form
              className="search-box"
              onSubmit={(e) => {
                e.preventDefault();
                setTab("records");
                void search(query, "records").catch(() => {});
              }}
            >
              <Search size={20} />
              <Input
                aria-label="Search source records"
                placeholder={
                  source === "ai-village"
                    ? "Search source text: correction, help, error…"
                    : "Search artifact text or identifiers…"
                }
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setDirty(true);
                }}
              />
              <Button
                variant="ghost"
                type="button"
                className={showFilters ? "filter-active" : ""}
                onClick={() => setShowFilters((s) => !s)}
                aria-expanded={showFilters}
              >
                <ListFilter size={17} />
                <span>Scope</span>
              </Button>
              <Button type="submit" disabled={loading === "search"}>
                {loading === "search" ? (
                  <Loader2 className="spin" size={16} />
                ) : (
                  "Search"
                )}
              </Button>
            </form>
            {showFilters && (
              <div className="filter-bar">
                {source === "ai-village" ? (
                  <>
                    <label>
                      Agent
                      <select
                        value={filters.agent_id}
                        onChange={(e) => {
                          setFilters((f) => ({
                            ...f,
                            agent_id: e.target.value,
                          }));
                          setDirty(true);
                        }}
                      >
                        <option value="">All recorded agents</option>
                        {agents.map((a) => (
                          <option key={a.id} value={a.source_id}>
                            {label(a)}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Record type
                      <select
                        value={filters.table}
                        onChange={(e) => {
                          setFilters((f) => ({ ...f, table: e.target.value }));
                          setDirty(true);
                        }}
                      >
                        <option value="">All record types</option>
                        {coverage?.tables?.map((t) => (
                          <option key={t.table_name} value={t.table_name}>
                            {humanize(t.table_name)}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      From (UTC)
                      <Input
                        type="date"
                        value={filters.from.slice(0, 10)}
                        onChange={(e) => {
                          setDirty(true);
                          setFilters((f) => ({
                            ...f,
                            from: e.target.value
                              ? e.target.value + "T00:00:00Z"
                              : "",
                          }));
                        }}
                      />
                    </label>
                    <label>
                      Through (UTC)
                      <Input
                        type="date"
                        value={filters.to.slice(0, 10)}
                        onChange={(e) => {
                          setDirty(true);
                          setFilters((f) => ({
                            ...f,
                            to: e.target.value
                              ? e.target.value + "T23:59:59.999999Z"
                              : "",
                          }));
                        }}
                      />
                    </label>
                    <Button
                      variant="ghost"
                      onClick={() => {
                        setFilters(initialFilters);
                        setDirty(true);
                      }}
                    >
                      Clear
                    </Button>
                  </>
                ) : (
                  <p>
                    SwarmTraces does not reliably record agent identities or
                    event timestamps. Search and ancestry remain available.
                  </p>
                )}
              </div>
            )}
            <div className="scope-line">
              <span>
                <Clock3 size={12} />
                Historical snapshot
              </span>
              <span>
                {source === "ai-village"
                  ? `${num(coverage?.indexed_records)} / ${num(coverage?.expected_records)} records indexed`
                  : "Bounded queries to the official archive"}
              </span>
              <button onClick={() => setShowFilters((s) => !s)}>
                {Object.values(filters).filter(Boolean).length
                  ? `${Object.values(filters).filter(Boolean).length} scope filters`
                  : "All available scope"}
              </button>
              {source === "ai-village" && !coverage?.complete && (
                <span className="amber">Indexing in progress</span>
              )}
            </div>
            {!started ? (
              <>
                <section className="entry-layout">
                  <div className="question-entry">
                    <div className="card-title">
                      <span>
                        <Sparkles size={17} />
                        Ask an investigative question
                      </span>
                      <span className="muted">AI · source linked</span>
                    </div>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        void ask();
                      }}
                    >
                      <Textarea
                        aria-label="Initial investigation question"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="Find cases where agents’ actions diverged from their claims. Follow what happened next and check alternative explanations."
                        rows={3}
                      />
                      <div>
                        <span>
                          Follows actions and outcomes · several minutes
                        </span>
                        <Button
                          type="submit"
                          disabled={!question.trim() || thinking}
                        >
                          Investigate
                          <ArrowUpRight size={15} />
                        </Button>
                      </div>
                    </form>
                  </div>
                  <div className="starting-points">
                    <div className="section-label">A WAY IN</div>
                    {(source === "ai-village"
                      ? examples
                      : [
                          {
                            title: "Follow artifact ancestry",
                            detail: "Original payload → decoded output",
                            q: "HELLO",
                            ask: "Inspect the recovery ancestry for these artifacts. What is directly recorded, and what behavior cannot be inferred?",
                          },
                        ]
                    ).map((x) => (
                      <button
                        key={x.title}
                        onClick={() => {
                          setQuery(x.q);
                          setQuestion(x.ask);
                          setTab("records");
                          void search(x.q, "records").catch(() => {});
                        }}
                      >
                        <span>
                          <strong>{x.title}</strong>
                          <small>{x.detail}</small>
                        </span>
                        <ChevronRight size={16} />
                      </button>
                    ))}
                  </div>
                </section>
                <section className="method-strip">
                  <div>
                    <Quote size={18} />
                    <span>
                      <strong>Begin with a record</strong>
                      <small>Keep the exact source and its context.</small>
                    </span>
                  </div>
                  <div>
                    <Network size={18} />
                    <span>
                      <strong>Follow recorded links</strong>
                      <small>
                        Relationships show structure, not causality.
                      </small>
                    </span>
                  </div>
                  <div>
                    <MessageSquare size={18} />
                    <span>
                      <strong>Challenge the interpretation</strong>
                      <small>Keep observations and hypotheses distinct.</small>
                    </span>
                  </div>
                </section>
                <details className="coverage-details">
                  <summary>
                    <Database size={14} />
                    Source and search coverage
                    <ChevronRight size={14} />
                  </summary>
                  <p>
                    {coverage?.search_scope ||
                      "Coverage is loaded from the source service. No corpus-wide completeness is assumed."}
                  </p>
                  {coverage?.tables && (
                    <table>
                      <thead>
                        <tr>
                          <th>Source table</th>
                          <th>Indexed</th>
                          <th>Expected</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {coverage.tables.map((t) => (
                          <tr key={t.table_name}>
                            <td>{humanize(t.table_name)}</td>
                            <td>{num(t.indexed)}</td>
                            <td>{num(t.expected)}</td>
                            <td>{t.status}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                  <code>Snapshot {snapshot}</code>
                </details>
              </>
            ) : (
              <div className="investigation-layout">
                <section className="evidence-workspace">
                  <div className="panel-tabs">
                    <div>
                      {(["records", "graph", "timeline", "context"] as const)
                        .filter(
                          (t) =>
                            source === "ai-village" ||
                            (t !== "timeline" && t !== "context"),
                        )
                        .map((t) => (
                          <button
                            key={t}
                            className={tab === t ? "active" : ""}
                            onClick={() => {
                              setTab(t);
                              if (t === "context" && selected)
                                void surrounding(selected);
                              if (t === "records")
                                void search(query, "records").catch(() => {});
                              if (t === "timeline")
                                void search("", "timeline").catch(() => {});
                              if (t === "graph" && !graph && selected)
                                void inspect(selected, true).catch(() => {});
                            }}
                          >
                            {t === "records" ? (
                              <FileText size={15} />
                            ) : t === "graph" ? (
                              <Network size={15} />
                            ) : (
                              <Clock3 size={15} />
                            )}{" "}
                            {humanize(t)}
                          </button>
                        ))}
                    </div>
                    <span>
                      {tab === "context"
                        ? sequence?.data.records.length || 0
                        : records.length}{" "}
                      loaded
                    </span>
                  </div>
                  {tab === "context" && sequence && (
                    <div className="sequence-scope">
                      <strong>Surrounding recorded activity</strong>
                      <span>
                        Scope: {humanize(sequence.data.scope.kind)} ·{" "}
                        {sequence.data.scope.order_unavailable
                          ? "Chronological order unavailable for this center record"
                          : humanize(sequence.data.scope.order)}
                      </span>
                      <div>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={!contextAnchor}
                          onClick={() =>
                            contextAnchor && void surrounding(contextAnchor, "source")
                          }
                        >
                          Same room / session
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={!contextAnchor?.agent_id}
                          onClick={() =>
                            contextAnchor && void surrounding(contextAnchor, "actor")
                          }
                        >
                          Same agent across tables
                        </Button>
                      </div>
                      <small>
                        Source sequence does not prove causality.{" "}
                        {sequence.data.scope.mode === "actor" &&
                          "Rows from different tables may describe the same action. "}
                        {sequence.truncated
                          ? "Bounded window; more records exist."
                          : ""}
                      </small>
                    </div>
                  )}
                  {tab === "graph" ? (
                    <div className="graph-pane">
                      {loading === "graph" ? (
                        <div className="empty-state">
                          <Loader2 className="spin" />
                          Loading recorded relationships…
                        </div>
                      ) : graph ? (
                        <EvidenceGraph
                          data={graph.data}
                          selected={selected?.id}
                          onSelect={(r) => void inspect(r).catch(() => {})}
                          truncated={graph.truncated}
                        />
                      ) : (
                        <div className="empty-state">
                          <Network />
                          <strong>Select a record to start a graph</strong>
                          <p>
                            Each neighborhood contains recorded links and their
                            source fields.
                          </p>
                          <Button
                            variant="outline"
                            onClick={() => setTab("records")}
                          >
                            Browse records
                          </Button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="record-list">
                      {["search", "report"].includes(loading) && !records.length ? (
                        <div className="empty-state">
                          <Loader2 className="spin" />
                          {loading === "report" ? "Opening source records for this report…" : "Searching the evidence index…"}
                        </div>
                      ) : visibleRecords.length ? (
                        visibleRecords.map((r) => (
                          <button
                            key={r.id}
                            className={`record-row ${selected?.id === r.id ? "selected" : ""}`}
                            onClick={() => void inspect(r).catch(() => {})}
                          >
                            <span className="record-dot" />
                            <span className="record-main">
                              <span className="record-heading">
                                <strong>
                                  {agents.find(
                                    (a) => a.source_id === r.agent_id,
                                  )
                                    ? label(
                                        agents.find(
                                          (a) => a.source_id === r.agent_id,
                                        )!,
                                      )
                                    : label(r)}
                                </strong>
                                <time>{dateLabel(r.timestamp)}</time>
                              </span>
                              <span className="record-excerpt">
                                {r.excerpt || "No text excerpt in this record"}
                              </span>
                              <span className="record-meta">
                                {tab === "context" && r.id === sequence?.data.seed && (
                                  <span className="context-anchor">Context center</span>
                                )}
                                {r.action_type && (
                                  <>
                                    <span>
                                      {humanize(r.action_type.toLowerCase())}
                                    </span>
                                    <span>·</span>
                                  </>
                                )}
                                {humanize(r.table)}
                                <span>·</span>
                                {r.source_id.slice(0, 17)}
                                {r.excerpt_truncated && <span>excerpt</span>}
                              </span>
                            </span>
                            <ChevronRight size={14} />
                          </button>
                        ))
                      ) : (
                        <div className="empty-state">
                          <Search />
                          <strong>
                            {result
                              ? "No matching excerpts"
                              : "Your evidence will appear here"}
                          </strong>
                          <p>
                            {result
                              ? "Try fewer words or a wider scope. No search result does not prove the behavior never occurred."
                              : "Search the corpus, or ask the investigator a question."}
                          </p>
                        </div>
                      )}
                      {tab !== "context" &&
                        result?.next_cursor !== null &&
                        result?.next_cursor !== undefined && (
                          <Button
                            className="load-more"
                            variant="outline"
                            onClick={() =>
                              void search(query, tab, true).catch(() => {})
                            }
                            disabled={loading === "search"}
                          >
                            Load more records
                          </Button>
                        )}
                    </div>
                  )}
                  {selected && (
                    <section className="source-inspector">
                      <div className="inspector-header">
                        <div>
                          <SourceTag type={selected.evidence_status} />
                          <strong>{label(selected)}</strong>
                        </div>
                        <div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => pin(selected)}
                          >
                            <Pin size={14} />
                            {pins.some((p) => p.id === selected.id)
                              ? "Pinned"
                              : "Pin"}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              void inspect(selected, true).catch(() => {})
                            }
                          >
                            <Network size={14} />
                            Relationships
                          </Button>
                          <button
                            aria-label="Close source inspector"
                            onClick={() => setSelected(null)}
                          >
                            <X size={17} />
                          </button>
                        </div>
                      </div>
                      <div className="inspector-id">
                        <code>{selected.id}</code>
                        <span>{dateLabel(selected.timestamp)}</span>
                      </div>
                      {selected.field_segments?.some(segment => segment.field !== "indexed_excerpt") ? (
                        <div className="source-fields">
                          <p className="coverage-note">Original fields inspected during this review. Commands show attempts; outputs need interpretation. A nonempty error field can be ordinary stderr.</p>
                          {selected.field_segments.map((segment, i) => <details key={i} open>
                            <summary>{segment.field}{segment.offset ? ` · from character ${segment.offset}` : ""}{segment.redacted ? " · redacted" : ""}</summary>
                            <pre className="source-text">{segment.text}</pre>
                            {segment.field_truncated && <small>Partial field. Open the original JSON for more context.</small>}
                          </details>)}
                        </div>
                      ) : <pre className="source-text">
                        {selected.excerpt || "No text excerpt is recorded."}
                      </pre>}
                      {selected.excerpt_truncated && (
                        <p className="coverage-note">
                          Excerpt truncated. The full original remains in the
                          source corpus; conclusions must respect the missing
                          context.
                        </p>
                      )}
                      <button
                        className="provenance-toggle"
                        onClick={() => setShowMeta((s) => !s)}
                        aria-expanded={showMeta}
                      >
                        <Braces size={14} />
                        {showMeta ? "Hide" : "Inspect"} provenance & metadata
                        <ChevronRight size={13} />
                      </button>
                      {showMeta && (
                        <pre className="metadata-json">
                          {JSON.stringify(
                            {
                              provenance: selected.provenance,
                              metadata: selected.metadata,
                            },
                            null,
                            2,
                          )}
                        </pre>
                      )}
                      {source === "ai-village" && (
                        <div className="raw-source">
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={loading === "raw"}
                            onClick={async () => {
                              setLoading("raw");
                              setError("");
                              const generation = selectionEpoch.current;
                              try {
                                const r = await api<
                                  Envelope<{
                                    raw_json: string;
                                    hash_verified: boolean;
                                    record_bytes: number;
                                    bytes_returned: number;
                                  }>
                                >(
                                  evidencePath(
                                    `records/${selected.table}/${selected.source_id}/raw`,
                                    source,
                                  ),
                                );
                                if (generation === selectionEpoch.current)
                                  setRaw(r);
                              } catch (e) {
                                setError(errorText(e));
                              } finally {
                                setLoading("");
                              }
                            }}
                          >
                            {loading === "raw" ? (
                              <Loader2 className="spin" size={13} />
                            ) : (
                              <Braces size={13} />
                            )}
                            Inspect original JSON
                          </Button>
                          {raw && (
                            <>
                              <p className="coverage-note">
                                {raw.data.hash_verified
                                  ? "Full record SHA-256 matches its source pointer."
                                  : "Partial raw record; full-row hash not verified."}{" "}
                                {num(raw.data.bytes_returned)} /{" "}
                                {num(raw.data.record_bytes)} bytes.
                              </p>
                              <pre className="metadata-json">
                                {raw.data.raw_json}
                              </pre>
                            </>
                          )}
                        </div>
                      )}
                      <div className="inspector-actions">
                        {source === "ai-village" && (
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={loading === "context"}
                            onClick={() => void surrounding(selected)}
                          >
                            <Clock3 size={14} />
                            Surrounding activity
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setQuestion(
                              `Inspect ${selected.id}. What happened around this record, and what evidence would challenge an initial interpretation?`,
                            );
                            setRightTab("assistant");
                          }}
                        >
                          <Sparkles size={14} />
                          Ask about this record
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setRightTab("notebook");
                            setNoteTarget(null);
                            setNoteText("");
                            setNoteKind("counterevidence");
                          }}
                        >
                          <MessageSquare size={14} />
                          Add context or challenge
                        </Button>
                      </div>
                    </section>
                  )}
                  <div className="evidence-footer">
                    <Info size={13} />
                    {source === "ai-village"
                      ? "Search covers indexed excerpts. Recorded links do not establish influence or causation."
                      : "Artifact ancestry is recorded; agents, chronology, and behavioral context may be unknown."}
                  </div>
                </section>
                <aside className="collaborator">
                  <div className="panel-tabs">
                    <div>
                      <button
                        className={rightTab === "assistant" ? "active" : ""}
                        onClick={() => setRightTab("assistant")}
                      >
                        <Sparkles size={15} />
                        Investigator
                      </button>
                      <button
                        className={rightTab === "notebook" ? "active" : ""}
                        onClick={() => setRightTab("notebook")}
                      >
                        <BookOpen size={15} />
                        Notebook
                        <span className="count">
                          {pins.length + notes.length}
                        </span>
                      </button>
                    </div>
                  </div>
                  {rightTab === "assistant" ? (
                    <>
                      <div className="conversation">
                        {!messages.length && (
                          <div className="assistant-intro">
                            <span className="assistant-mark">
                              <Sparkles size={20} />
                            </span>
                            <h2>Investigate together.</h2>
                            <p>
                              Ask what changed in an agent’s behavior. The review
                              follows leads through actions, responses, and outcomes.
                              Challenge a finding to steer the next pass.
                            </p>
                            <div className="assistant-boundary">
                              Historical analysis can reveal evidence and
                              uncertainty. It cannot measure whether an unrun
                              intervention works.
                            </div>
                          </div>
                        )}
                        {messages.map((m, i) => (
                          <article key={i} className={`chat-message ${m.role}`}>
                            <div className="message-byline">
                              {m.role === "user" ? (
                                "You"
                              ) : (
                                <>
                                  <Sparkles size={12} />
                                  Investigator <span>AI draft</span>
                                </>
                              )}
                            </div>
                            {m.result ? (
                              <>
                                {m.result.review_status && <div className={`review-evidence-level ${m.result.review_status}`}>
                                  <strong>{m.result.review_status === "action_evidence_reviewed" ? "Action evidence inspected · AI draft" : m.result.review_status === "candidate_only" ? "Lead only · action evidence incomplete" : "Insufficient evidence for a finding"}</strong>
                                  <small>{String(m.result.coverage?.retrieved_records ?? 0)} source records · {String(m.result.coverage?.raw_records_inspected ?? 0)} originals inspected · bounded sample</small>
                                </div>}
                                {m.result.progress && <ReviewPath steps={m.result.progress} />}
                                <div className="ai-findings">
                                  {m.result.findings?.length ? (
                                    m.result.findings.map((f, j) => (
                                      <div className="finding" key={j}>
                                        <span
                                          className={`finding-kind ${f.evidence_type}`}
                                        >
                                          {typeof f.category === "string" ? ({ opportunity: "Task and opportunity", action: "Action and response", outcome: "Recorded outcome", counterevidence: "Counterevidence", observation: "Candidate observation" }[f.category] || "Interpretation") : f.evidence_type === "observation"
                                            ? "Candidate observation"
                                            : "Interpretation"}
                                          {typeof f.evidence_kind === "string" && ` · ${f.evidence_kind}`}
                                          {f.secondary_evidence
                                            ? " · secondary evidence"
                                            : ""}
                                        </span>
                                        <p>{f.text}</p>
                                        <div className="citation-list">
                                          {f.source_ids.map((id, k) => (
                                            <button
                                              key={id}
                                              onClick={() =>
                                                void inspect(
                                                  m.result?.sources?.find(
                                                    (r) => r.id === id,
                                                  ) || id,
                                                ).catch(() => {})
                                              }
                                              title={id}
                                            >
                                              <Quote size={11} />
                                              {k + 1} ·{" "}
                                              {humanize(id.split(":")[0])}
                                            </button>
                                          ))}
                                        </div>
                                        {!!f.quotes?.length && (
                                          <details className="matched-quotes">
                                            <summary>
                                              Read matched source quotes
                                            </summary>
                                            {f.quotes.map((q, qi) => (
                                              <blockquote key={qi}>
                                                <p>{q.quote}</p>
                                                <cite>{q.source_id}</cite>
                                              </blockquote>
                                            ))}
                                          </details>
                                        )}
                                        {notes
                                          .filter(
                                            (n) =>
                                              n.target_claim === f.text &&
                                              n.source_ids?.length === f.source_ids.length &&
                                              n.source_ids.every((id) => f.source_ids.includes(id)),
                                          )
                                          .map((n) => (
                                            <div
                                              key={n.id}
                                              className="finding-review"
                                            >
                                              <strong>
                                                {n.review_status === "disputed"
                                                  ? "Your challenge"
                                                  : "Your review"}
                                              </strong>
                                              <p>{n.text}</p>
                                              <small>
                                                Human interpretation · retained
                                                with this draft
                                              </small>
                                            </div>
                                          ))}
                                        <div className="finding-actions">
                                          <button
                                            onClick={() => {
                                              setNoteTarget({
                                                text: f.text,
                                                source_ids: f.source_ids,
                                              });
                                              setNoteText("");
                                              setNoteKind("hypothesis");
                                              setRightTab("notebook");
                                            }}
                                          >
                                            Review
                                          </button>
                                          <button
                                            onClick={() => {
                                              setNoteTarget({
                                                text: f.text,
                                                source_ids: f.source_ids,
                                              });
                                              setNoteText("");
                                              setNoteKind("counterevidence");
                                              setRightTab("notebook");
                                            }}
                                          >
                                            Challenge
                                          </button>
                                        </div>
                                      </div>
                                    ))
                                  ) : (
                                    <p>{m.result.answer || "This pass did not establish a supported behavioral finding. Review the missing evidence below or refine the question."}</p>
                                  )}
                                </div>
                                {!!m.result.findings?.length && (
                                  <p className="ai-caveat">
                                    Quotes matched to source excerpts. Whether
                                    they support the interpretation still needs
                                    review.
                                  </p>
                                )}
                                {!!m.result.unknowns?.length && (
                                  <div className="unknowns">
                                    <strong>What remains unknown</strong>
                                    <ul>
                                      {m.result.unknowns.map((u, j) => (
                                        <li key={j}>{u}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                                {(
                                  (m.result.warnings ||
                                    m.result.coverage?.warnings ||
                                    []) as string[]
                                ).map((w, j) => (
                                  <p className="coverage-note" key={j}>
                                    {w}
                                  </p>
                                ))}
                                <details className="retrieval-details">
                                  <summary>Inspect retrieval scope</summary>
                                  <pre>
                                    {JSON.stringify(
                                      {
                                        coverage: m.result.coverage,
                                        query_plan: m.result.query_plan,
                                      },
                                      null,
                                      2,
                                    )}
                                  </pre>
                                </details>
                                {!!m.result.suggested_followups?.length && (
                                  <div className="followups">
                                    {m.result.suggested_followups
                                      .slice(0, 3)
                                      .map((q) => (
                                        <button
                                          key={q}
                                          onClick={() => setQuestion(q)}
                                        >
                                          {q}
                                          <ArrowUpRight size={12} />
                                        </button>
                                      ))}
                                  </div>
                                )}
                                {!!m.result.proposed_tests?.length && (
                                  <button
                                    className="propose-link"
                                    onClick={() =>
                                      setStudy({
                                        ...emptyStudy(),
                                        title: "Follow-up study",
                                        intervention:
                                          m.result!.proposed_tests[0].text,
                                      })
                                    }
                                  >
                                    <FlaskConical size={13} />
                                    Draft an unrun study proposal
                                  </button>
                                )}
                              </>
                            ) : (
                              <p>{m.content}</p>
                            )}
                          </article>
                        ))}
                        {thinking && (
                          <>
                          {deepReview && <ReviewPath steps={reviewJob?.progress || []} running />}
                          <div className="thinking">
                            <Loader2 className="spin" size={15} />
                            <span>
                              {deepReview ? "Reviewing behavior across the selected scope…" : "Retrieving records and comparing evidence…"}
                              <small>
                                {deepReview ? "Checks actions, outcomes, and counterevidence. May take several minutes." : "Your current scope and corrections are included."}
                              </small>
                              <button
                                className="stop-analysis"
                                onClick={cancelAnalysis}
                              >
                                Stop analysis
                              </button>
                            </span>
                          </div>
                          </>
                        )}
                        <div ref={chatEnd} />
                      </div>
                      <form
                        className="chat-composer"
                        onSubmit={(e) => {
                          e.preventDefault();
                          void ask();
                        }}
                      >
                        <label className="review-mode">
                          <input type="checkbox" checked={deepReview} disabled={thinking} onChange={e => setDeepReview(e.target.checked)} />
                          Follow the evidence in depth
                          <span>{deepReview ? "Adaptive review" : "Quick answer"}</span>
                        </label>
                        <Textarea
                          aria-label="Ask the investigator"
                          placeholder={
                            selected
                              ? "Ask about the selected record, or challenge a finding…"
                              : "Ask a question about this evidence…"
                          }
                          value={question}
                          onChange={(e) => setQuestion(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                              e.preventDefault();
                              void ask();
                            }
                          }}
                          rows={3}
                        />
                        <div>
                          <span>
                            {Math.min(
                              2,
                              new Set([
                                ...(selected ? [selected.id] : []),
                                ...pins.map((p) => p.id),
                              ]).size,
                            )}{" "}
                            focused sources · current scope
                          </span>
                          <Button
                            size="icon"
                            type="submit"
                            aria-label="Send investigation question"
                            disabled={!question.trim() || thinking}
                          >
                            <ArrowUp size={17} />
                          </Button>
                        </div>
                      </form>
                    </>
                  ) : (
                    <div className="notebook">
                      <div className="notebook-section">
                        <h3>
                          Pinned evidence <span>{pins.length}/30</span>
                        </h3>
                        {!pins.length && (
                          <p className="empty-copy">
                            Pin a source record to keep it in context for future
                            questions.
                          </p>
                        )}
                        {pins.map((p) => (
                          <div className="pin-card" key={p.id}>
                            <button
                              className="pin-content"
                              onClick={() => void inspect(p.id).catch(() => {})}
                            >
                              <strong>{p.label || p.id}</strong>
                              <p>{p.excerpt.slice(0, 170)}</p>
                              <code>{p.id.slice(0, 40)}</code>
                            </button>
                            <button
                              aria-label={`Unpin ${p.id}`}
                              onClick={() => {
                                setPins((a) => a.filter((x) => x.id !== p.id));
                                setDirty(true);
                              }}
                            >
                              <X size={13} />
                            </button>
                          </div>
                        ))}
                      </div>
                      <div className="notebook-section">
                        <h3>Human notes</h3>
                        {noteTarget && (
                          <div className="note-target">
                            <strong>Regarding this AI draft</strong>
                            <p>{noteTarget.text}</p>
                            <button onClick={() => setNoteTarget(null)}>
                              Clear target
                            </button>
                          </div>
                        )}
                        {selected && (
                          <div className="note-linked">
                            Linked to {selected.id.slice(0, 42)}
                          </div>
                        )}
                        <select
                          aria-label="Note type"
                          value={noteKind}
                          onChange={(e) =>
                            setNoteKind(
                              e.target.value as Note["evidence_status"],
                            )
                          }
                        >
                          <option value="observation">Observation</option>
                          <option value="hypothesis">Hypothesis</option>
                          <option value="counterevidence">
                            Counterevidence / challenge
                          </option>
                          <option value="question">Open question</option>
                        </select>
                        <Textarea
                          aria-label="Human note"
                          maxLength={1500}
                          placeholder="Add what the AI missed, a competing explanation, or a precise question…"
                          value={noteText}
                          onChange={(e) => setNoteText(e.target.value)}
                          rows={4}
                        />
                        <Button
                          size="sm"
                          onClick={addNote}
                          disabled={!noteText.trim() || notes.length >= 80}
                        >
                          <Plus size={14} />
                          Add note
                        </Button>
                        {notes.map((n) => (
                          <article className="note-card" key={n.id}>
                            <div>
                              <span
                                className={`finding-kind ${n.evidence_status}`}
                              >
                                {humanize(n.evidence_status)}
                              </span>
                              <button
                                aria-label="Remove note"
                                onClick={() => {
                                  setNotes((a) =>
                                    a.filter((x) => x.id !== n.id),
                                  );
                                  setDirty(true);
                                }}
                              >
                                <X size={12} />
                              </button>
                            </div>
                            <p>{n.text}</p>
                            {n.target_claim && (
                              <details className="matched-quotes">
                                <summary>Challenged AI draft</summary>
                                <blockquote>
                                  <p>{n.target_claim}</p>
                                  <cite>{n.source_ids?.join(" · ")}</cite>
                                </blockquote>
                              </details>
                            )}
                            {n.record_id && (
                              <button
                                className="note-source"
                                onClick={() =>
                                  void inspect(n.record_id!).catch(() => {})
                                }
                              >
                                View linked source
                                <ArrowUpRight size={12} />
                              </button>
                            )}
                            <span className="human-label">
                              Human note ·{" "}
                              {n.review_status === "disputed"
                                ? "disputed"
                                : "not a verified finding"}
                            </span>
                          </article>
                        ))}
                      </div>
                    </div>
                  )}
                </aside>
              </div>
            )}
          </>
        )}
        {view === "patterns" && (
          <Patterns source={source} onOpen={(p, r) => void openPattern(p, r)} />
        )}
        {view === "reports" && <Reports active={reportId} onSelect={setReportId} onOpen={(report, ids, question) => void openReport(report, ids, question)} />}
        {labOpened && <div hidden={view !== "society"}><SocietyLab active={view === "society"} study={labStudy} evidence={{ source, report_id: reportId, pins, notes, status: "human_selected_context" }} onDraftStudy={(title, _sourceObservation, source_ref) => setStudy({ ...emptyStudy(), title: title.slice(0, 200), source_ref })} /></div>}
        {view === "saved" && (
          <div className="secondary-page">
            <div className="secondary-heading">
              <div className="eyebrow">YOUR RESEARCH</div>
              <h1>Investigations</h1>
              <p>
                Questions, source pointers, human corrections, and proposed
                studies—kept together.
              </p>
            </div>
            {savedStatus === "idle" || savedStatus === "loading" ? (
              <div className="empty-state bordered" role="status">
                <BookOpen />
                <strong>Loading your investigations…</strong>
              </div>
            ) : savedStatus === "error" ? (
              <div className="empty-state bordered" role="alert">
                <BookOpen />
                <strong>Couldn’t load your investigations</strong>
                <p>{savedError}</p>
                <Button onClick={() => void refreshSaved()}>Try again</Button>
              </div>
            ) : saved.length ? (
              <div className="saved-grid">
                {saved.map((s) => (
                  <button
                    className="saved-card"
                    key={s.id}
                    onClick={() => void openSaved(s.id)}
                  >
                    <BookOpen size={20} />
                    <strong>{s.title}</strong>
                    <span>{sourceNames[s.source]}</span>
                    <small>Updated {dateLabel(s.updated_at)}</small>
                    <ArrowUpRight size={17} />
                  </button>
                ))}
              </div>
            ) : (
              <div className="empty-state bordered">
                <BookOpen />
                <strong>No saved investigations yet</strong>
                <p>
                  Start with a question or source record. Save your workspace
                  when you have something worth returning to.
                </p>
                <Button onClick={() => nav("explore")}>Explore evidence</Button>
              </div>
            )}
          </div>
        )}
        {view === "studies" && (
          <div className="secondary-page">
            <div className="secondary-heading">
              <div className="eyebrow">FROM OBSERVATION TO A QUESTION</div>
              <h1>Proposed studies</h1>
              <p>
                These belong to{" "}
                {active ? `“${active.title}”` : "the current investigation"}.
                Every study is unrun; the historical corpus contains no measured
                effect of these changes.
              </p>
              <Button onClick={() => setStudy(emptyStudy())}>
                <Plus size={15} />
                Draft a study
              </Button>
              <Button variant="outline" onClick={() => nav("society")}><FlaskConical size={15}/>Explore controlled worlds</Button>
            </div>
            {studies.length ? (
              <div className="study-list">
                {studies.map((s) => (
                  <article className="study-card" key={s.id}>
                    <span className="finding-kind hypothesis">
                      Proposed · not executed
                    </span>
                    <h2>{s.title}</h2>
                    {s.source_ref && <p>Based on imported trace v{s.source_ref.version} · {s.source_ref.hash.slice(0,12)} · {s.source_ref.event_ids.length} selected events</p>}
                    <dl>
                      <dt>Change to test</dt>
                      <dd>{s.intervention}</dd>
                      <dt>Comparison / control</dt>
                      <dd>{s.control}</dd>
                      <dt>Outcome measure</dt>
                      <dd>{s.metric}</dd>
                      <dt>Guardrail</dt>
                      <dd>{s.guardrail}</dd>
                    </dl>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setStudy(s)}
                    >
                      Edit proposal
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => { setLabStudy(s); nav("society"); }}>Explore test environment</Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setStudies((old) => old.filter((x) => x.id !== s.id));
                        setDirty(true);
                      }}
                    >
                      Remove proposal
                    </Button>
                  </article>
                ))}
              </div>
            ) : (
              <div className="empty-state bordered">
                <FlaskConical />
                <strong>Make the next experiment precise</strong>
                <p>
                  Use an observed pattern to draft a testable change, a
                  comparison, a metric, and a guardrail. Actual results require
                  new runs.
                </p>
              </div>
            )}
          </div>
        )}
        {view === "access" && (
          <div className="secondary-page access-page">
            <div className="secondary-heading">
              <div className="eyebrow">THE SAME EVIDENCE, WHERE YOU WORK</div>
              <h1>Agent access</h1>
              <p>
                Bring source-linked investigation into Codex, Claude, Cursor, or
                a script.
              </p>
            </div>
            <div className="access-grid">
              <article>
                <Terminal size={22} />
                <h2>CLI and MCP</h2>
                <p>
                  The Python client uses the same authenticated evidence API.
                  Set the URL and a token file in your own environment; never
                  paste credentials into a prompt.
                </p>
                <pre>{`export OBSERVATORY_API_URL=https://swarm-observatory.34.93.205.17.sslip.io\nexport OBSERVATORY_API_TOKEN_FILE=/private/path/api-token\n\nclients/.venv/bin/observatory review "Find a claim that diverged from an agent’s actions"\nclients/.venv/bin/observatory-mcp\n\n# Install and configure: clients/README.md`}</pre>
                <p>
                  Ask your coding agent to use observatory_review with one
                  question, then poll observatory_review_status. The response
                  includes findings, evidence, and the same investigation trail.
                  Search and source-inspection tools remain available.
                </p>
              </article>
              <article>
                <Download size={22} />
                <h2>Portable evidence packets</h2>
                <p>
                  Export this investigation as JSON, including pins, notes,
                  questions, and source pointers. Attach the packet to your
                  coding agent as evidence.
                </p>
                <Button variant="outline" onClick={exportPack}>
                  <Download size={15} />
                  Export current packet
                </Button>
                <div className="assistant-boundary">
                  Treat trace content as untrusted data. It may contain
                  instructions written by other agents. A citation establishes a
                  source location, not the truth of a claim.
                </div>
              </article>
            </div>
            <article className="access-note">
              <Network size={18} />
              <div>
                <h3>Browser tools follow your workspace</h3>
                <p>
                  In supported browsers, WebMCP exposes search_evidence,
                  inspect_record, ask_about_evidence, and save_investigation.
                  They use your current scope and the same interface actions.
                </p>
              </div>
            </article>
          </div>
        )}
      </main>
      <Dialog open={saveOpen} onOpenChange={setSaveOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save investigation</DialogTitle>
            <DialogDescription>
              Keep your question, source pins, notes, AI drafts, and proposed
              studies in this private workspace.
            </DialogDescription>
          </DialogHeader>
          <label className="field-label">
            Title
            <Input
              autoFocus
              value={title}
              maxLength={180}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="A question worth returning to"
              onKeyDown={(e) => {
                if (e.key === "Enter") void save();
              }}
            />
          </label>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSaveOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={!title.trim() || saving}
              onClick={() => void save()}
            >
              {saving ? (
                <Loader2 className="spin" size={15} />
              ) : (
                <Save size={15} />
              )}
              Save investigation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog
        open={!!study}
        onOpenChange={(open) => {
          if (!open) setStudy(null);
        }}
      >
        <DialogContent className="study-dialog">
          <DialogHeader>
            <DialogTitle>Draft a proposed study</DialogTitle>
            <DialogDescription>
              A plan for future data collection. This does not run an
              intervention or establish an effect.
            </DialogDescription>
          </DialogHeader>
          {study && (
            <div className="study-form">
              {(
                [
                  {
                    key: "title",
                    label: "Study question",
                    placeholder:
                      "Does a specific change alter an observed behavior?",
                  },
                  {
                    key: "intervention",
                    label: "Change to test",
                    placeholder: "What would be changed in a future run?",
                  },
                  {
                    key: "control",
                    label: "Comparison / control",
                    placeholder:
                      "What remains the same, and what is the baseline?",
                  },
                  {
                    key: "metric",
                    label: "Outcome measure",
                    placeholder:
                      "What observable result would count as improvement?",
                  },
                  {
                    key: "guardrail",
                    label: "Guardrail & alternative explanations",
                    placeholder:
                      "What should not worsen? What could confound the comparison?",
                  },
                ] as const
              ).map((f) => (
                <label className="field-label" key={f.key}>
                  {f.label}
                  <Textarea
                    maxLength={
                      f.key === "title"
                        ? 300
                        : f.key === "intervention"
                          ? 3000
                          : 2000
                    }
                    value={study[f.key]}
                    onChange={(e) =>
                      setStudy({ ...study, [f.key]: e.target.value })
                    }
                    placeholder={f.placeholder}
                    rows={f.key === "title" ? 1 : 2}
                  />
                </label>
              ))}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setStudy(null)}>
              Cancel
            </Button>
            <Button
              disabled={
                (studies.length >= 20 &&
                  !studies.some((s) => s.id === study?.id)) ||
                !study?.title.trim() ||
                !study.intervention.trim() ||
                !study.control.trim() ||
                !study.metric.trim() ||
                !study.guardrail.trim()
              }
              onClick={() => {
                if (
                  !study ||
                  (studies.length >= 20 &&
                    !studies.some((s) => s.id === study.id))
                )
                  return;
                setStudies((old) => [
                  ...old.filter((s) => s.id !== study.id),
                  study,
                ]);
                setDirty(true);
                setStudy(null);
                setNotice(
                  "Unrun study added. Save your investigation to retain it.",
                );
              }}
            >
              {studies.length >= 20 && !studies.some((s) => s.id === study?.id)
                ? "20-study limit reached"
                : "Add proposed study"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
