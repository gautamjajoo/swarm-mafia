export type Source = "ai-village" | "swarmtraces";
export type RecordItem = {
  id: string;
  source_id: string;
  table: string;
  agent_id?: string | null;
  timestamp?: string | null;
  action_type?: string | null;
  excerpt: string;
  excerpt_truncated?: boolean;
  metadata: Record<string, unknown>;
  evidence_status?: string;
  provenance: Record<string, unknown>;
  field_segments?: { field: string; text: string; offset?: number; field_truncated?: boolean; redacted?: boolean }[];
};
export type Coverage = {
  complete?: boolean;
  indexed_records?: number;
  expected_records?: number;
  search_scope?: string;
  tables?: {
    table_name: string;
    expected: number;
    indexed: number;
    status: string;
  }[];
  [key: string]: unknown;
};
export type Envelope<T> = {
  snapshot: string;
  data: T;
  coverage: Coverage;
  truncated: boolean;
  next_cursor: number | null;
};
export type Edge = {
  id: string;
  source: string;
  target: string;
  type: string;
  evidence_status: string;
  provenance?: Record<string, unknown>;
};
export type GraphData = {
  nodes: RecordItem[];
  edges: Edge[];
  ambiguous_references?: number;
  unresolved_references?: number;
  unresolved_source_ids?: string[];
};
export type SequenceData = {
  seed: string;
  records: RecordItem[];
  scope: { kind: string; id: string; order: string; mode: string; order_unavailable?: boolean };
  before_truncated: boolean;
  after_truncated: boolean;
  interpretation?: string;
};
export type Finding = {
  text: string;
  source_ids: string[];
  evidence_type: string;
  quotes?: { source_id: string; quote: string }[];
  secondary_evidence?: boolean;
  [key: string]: unknown;
};
export type InvestigationResult = {
  status: string;
  review_status?: "action_evidence_reviewed" | "candidate_only" | "insufficient_evidence";
  answer: string;
  findings: Finding[];
  unknowns: string[];
  suggested_followups: string[];
  proposed_tests: { text: string; status: string }[];
  sources: RecordItem[];
  coverage: Record<string, unknown>;
  warnings?: string[];
  query_plan?: unknown;
  snapshot?: string;
  progress?: ReviewStep[];
  opportunities?: Finding[];
  action_sequence?: Finding[];
  outcomes?: Finding[];
  counterevidence?: Finding[];
};
export type ReviewStep = {
  step: number;
  action: string;
  reason: string;
  summary: string;
  status: string;
  arguments?: Record<string, unknown>;
};
export type ReviewJob = {
  id: string;
  status: "running" | "cancelling" | "completed" | "failed" | "cancelled";
  progress: ReviewStep[];
  result?: InvestigationResult;
  error?: string;
  expires_at?: string;
};
export type Note = {
  id: string;
  text: string;
  record_id?: string;
  target_claim?: string;
  source_ids?: string[];
  evidence_status:
    | "observation"
    | "hypothesis"
    | "counterevidence"
    | "question";
  review_status: "human_note" | "reviewed" | "disputed";
  created_at: string;
};
export type Study = {
  id: string;
  title: string;
  intervention: string;
  metric: string;
  control: string;
  guardrail: string;
  status: "proposed_unrun";
};
export type Pin = {
  id: string;
  excerpt: string;
  provenance: Record<string, unknown>;
  label?: string;
  source?: Source;
  excerpt_truncated?: boolean;
};
export type Message = {
  role: "user" | "assistant";
  content: string;
  result?: InvestigationResult;
};
export type PatternFocus = {
  id: string;
  rule: string;
  definition: string;
  source_ids: string[];
  count?: number;
  share?: number;
  built_at?: string;
};
export type WorkspaceState = {
  pattern?: PatternFocus;
  context_seed?: string;
  context_mode?: "source" | "actor";
  selected_id?: string;
  graph_seed?: string;
  tab?: "records" | "graph" | "timeline" | "context";
  query: string;
  filters: Record<string, string>;
  pins: Pin[];
  notes: Note[];
  studies: Study[];
  messages: Message[];
};
export type Saved = {
  id: string;
  title: string;
  source: Source;
  snapshot: string;
  revision: number;
  updated_at: string;
  state?: WorkspaceState;
};
export const sourceNames: Record<Source, string> = {
  "ai-village": "AI Village",
  swarmtraces: "SwarmTraces",
};
export const humanize = (s?: string | null) =>
  (s || "Unknown").replaceAll("_", " ");
export function label(r: RecordItem) {
  return String(
    r.metadata?.name || r.metadata?.title || r.action_type || humanize(r.table),
  );
}
export function dateLabel(s?: string | null) {
  if (!s) return "Time not recorded";
  const date = new Date(s);
  return isNaN(date.getTime())
    ? s
    : date.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "UTC",
      }) + " UTC";
}
export async function api<T>(
  path: string,
  body?: unknown,
  method?: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(path, {
    signal,
    method: method || (body ? "POST" : "GET"),
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = (await response.json()) as { detail?: unknown };
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "The request could not be completed.",
    );
  return data as T;
}
export function evidencePath(
  path: string,
  source: Source,
  filters: Record<string, string> = {},
) {
  const p = new URLSearchParams({ source });
  for (const [k, v] of Object.entries(filters)) if (v) p.set(k, v);
  return `/api/evidence/${path}?${p}`;
}
export function download(
  name: string,
  content: string,
  type = "application/json",
) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
