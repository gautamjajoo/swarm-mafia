/** Society Lab integration. Replay semantics adapted from Atharvap14/society-lab
 * web/society-replay.js, ac71dc81941c68da21fd7d7ccfcad61ca09737db.
 * Only the visible prefix contributes state; a message address is not exposure. */
export type TraceEvent = {
  id: string;
  occurred_at: string;
  kind: string;
  actor_id?: string;
  task_id?: string;
  parent_task_id?: string;
  recipient_ids?: string[];
  data: Record<string, unknown>;
};
export type TraceRun = {
  id: string;
  version: number;
  hash: string;
  created: string;
  kind: "observability_run";
  payload: {
    source: { id: string; name: string; kind: string };
    run: { id: string; name?: string };
    events: TraceEvent[];
    limitations?: string[];
  };
};
export type TraceSummary = Pick<
  TraceRun,
  "id" | "version" | "hash" | "created"
> & {
  source: TraceRun["payload"]["source"];
  run: TraceRun["payload"]["run"];
  event_count: number;
};
export type TraceGraph = {
  seed_event_id: string;
  nodes: {
    id: string;
    kind: string;
    actor_id?: string;
    capture_position: number;
  }[];
  edges: { source: string; target: string; relation: string; field: string }[];
  diagnostics: {
    event_id: string;
    field: string;
    status: string;
    reference_id: string;
  }[];
  truncated: boolean;
  source_ref: { id: string; version: number; hash: string };
};
export type TraceCheck = {
  kind?: string;
  title?: string;
  text?: string;
  summary?: string;
  detail?: string;
  event_ids?: string[];
  [key: string]: unknown;
};
export type WorldResult = {
  seed: number;
  max_rounds: number;
  steps_used: number;
  max_steps: number;
  terminal: boolean;
  next_role: string | null;
  observation: Record<string, unknown> | null;
  action_schema: {
    properties?: Record<string, { enum?: string[]; type?: string }>;
  };
  action_fields: Record<string, string[]>;
  events: Record<string, unknown>[];
  outcome: Record<string, unknown>;
  spec: Record<string, unknown>;
  spec_hash: string;
  limitations: string[];
  provenance: Record<string, unknown>;
};
export type WorldAction = { role: string; action: Record<string, unknown> };
export const societyPath = (path: string) => `/api/evidence/society/${path}`;
export const eventLabel = (e: TraceEvent) =>
  String(
    e.data.content ??
      e.data.change_summary ??
      e.data.summary ??
      e.data.title ??
      e.data.tool_name ??
      e.data.name ??
      e.kind.replaceAll(".", " · "),
  );
export function audience(e: TraceEvent) {
  if (e.kind === "reasoning.recorded") return "Actor-local record";
  if (e.kind !== "message.sent" && e.kind !== "intervention.delivered")
    return "Recorded action";
  if (e.data.visibility === "private") return "Private / local";
  if (e.data.visibility === "broadcast") return "Declared broadcast";
  if (e.recipient_ids?.length)
    return `Addressed to ${e.recipient_ids.join(", ")}`;
  if (e.data.visibility === "room")
    return `Room: ${e.data.channel_name ?? e.data.channel_id}`;
  return "Audience unknown";
}
export function prefixState(events: TraceEvent[], count: number) {
  const tasks = new Map<
    string,
    { id: string; title: string; status: string; event: string }
  >();
  const calls = new Map<
    string,
    { id: string; title: string; status: string; event: string }
  >();
  const artifacts = new Map<
    string,
    { id: string; title: string; status: string; event: string }
  >();
  const prefix = events.slice(0, Math.max(0, count));
  for (const [index, e] of prefix.entries()) {
    if (e.task_id && e.kind.startsWith("task.")) {
      const old = tasks.get(e.task_id);
      tasks.set(e.task_id, {
        id: e.task_id,
        title: String(e.data.title ?? old?.title ?? e.task_id),
        event: e.id,
        status:
          e.kind === "task.completed"
            ? e.data.success === true
              ? "Reported complete"
              : "Reported incomplete"
            : e.kind === "task.assigned"
              ? "Assigned"
              : "Created",
      });
    }
    if (e.kind === "tool.called")
      calls.set(e.id, {
        id: e.id,
        title: String(e.data.tool_name),
        status: "Receipt not yet recorded",
        event: e.id,
      });
    if (e.kind === "tool.returned") {
      const matched = prefix
        .slice(0, index)
        .filter(
          (x) => x.kind === "tool.called" && x.data.call_id === e.data.call_id,
        );
      if (matched.length === 1 && matched[0].actor_id === e.actor_id) {
        const id = matched[0].id;
        calls.set(id, {
          id,
          title: String(matched[0].data.tool_name),
          status:
            e.data.success === true ? "Reported success" : "Reported failure",
          event: e.id,
        });
      } else
        calls.set(e.id, {
          id: e.id,
          title: String(e.data.call_id),
          status: "Unresolved receipt",
          event: e.id,
        });
    }
    if (e.kind === "artifact.updated")
      artifacts.set(String(e.data.artifact_id), {
        id: String(e.data.artifact_id),
        title: String(e.data.artifact_id),
        status: String(e.data.revision_id),
        event: e.id,
      });
  }
  return {
    tasks: [...tasks.values()],
    calls: [...calls.values()],
    artifacts: [...artifacts.values()],
  };
}
