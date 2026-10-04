"use client";
import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  RefreshCw,
  Repeat2,
  Users,
  Info,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, dateLabel, Envelope, evidencePath, Source } from "@/lib/evidence";
export type Pattern = {
  id: string;
  text?: string;
  count?: number;
  actor_count?: number;
  first?: string;
  last?: string;
  source_ids: string[];
  unknown_actor_occurrences?: number;
  room_id?: string;
  day?: string;
  agent_id?: string;
  agent_name?: string;
  room_name?: string;
  message_count?: number;
  eligible_agent_messages?: number;
  share?: number;
  interpretation?: string;
};
type PatternData = {
  kind: string;
  definition: string;
  qualification: Record<string, unknown>;
  patterns: Pattern[];
  built_at: string;
};
export function Patterns({
  source,
  onOpen,
}: {
  source: Source;
  onOpen: (p: Pattern, result: Envelope<PatternData>) => void;
}) {
  const [kind, setKind] = useState("exact_repetition"),
    [result, setResult] = useState<Envelope<PatternData> | null>(null),
    [loading, setLoading] = useState(false),
    [error, setError] = useState(""),
    [refreshKey, setRefreshKey] = useState(0);
  useEffect(() => {
    let live = true;
    if (source !== "ai-village") return;
    api<Envelope<PatternData>>(
      evidencePath("patterns", source, { kind, limit: "20" }),
    )
      .then((r) => {
        if (live) {
          setResult(r);
          setError("");
        }
      })
      .catch((e) => {
        if (live) setError(e.message);
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [source, kind, refreshKey]);
  return (
    <div className="secondary-page patterns-page">
      <div className="secondary-heading">
        <div className="eyebrow">MEASURABLE SIGNALS · HUMAN INTERPRETATION</div>
        <h1>Patterns worth inspecting</h1>
        <p>
          Find candidates with explicit, reproducible rules. Open the source
          examples, compare context, and decide what the pattern means.
        </p>
      </div>
      {source !== "ai-village" ? (
        <div className="empty-state bordered">
          <Info />
          <strong>This lens uses AI Village chat records</strong>
          <p>
            SwarmTraces has a different artifact structure. Switch to AI Village
            in Explore to use this analysis.
          </p>
        </div>
      ) : (
        <>
          <div className="pattern-controls">
            <div role="group" aria-label="Pattern rule">
              <Button
                variant={kind === "exact_repetition" ? "default" : "outline"}
                onClick={() => setKind("exact_repetition")}
              >
                <Repeat2 size={15} />
                Repeated text
              </Button>
              <Button
                variant={
                  kind === "participation_concentration" ? "default" : "outline"
                }
                onClick={() => setKind("participation_concentration")}
              >
                <Users size={15} />
                Participation
              </Button>
            </div>
            <Button
              variant="ghost"
              size="sm"
              disabled={loading}
              onClick={() => {
                setLoading(true);
                setError("");
                setRefreshKey((k) => k + 1);
              }}
            >
              {loading ? (
                <Loader2 className="spin" size={14} />
              ) : (
                <RefreshCw size={14} />
              )}
              Refresh
            </Button>
          </div>
          <div className="pattern-definition">
            <Info size={17} />
            <div>
              <strong>
                {kind === "exact_repetition"
                  ? "Same text, at least three times"
                  : "Share of recorded messages"}
              </strong>
              <p>
                {kind === "exact_repetition"
                  ? "Chat messages of at least 80 characters, grouped after Unicode case folding and whitespace normalization. Truncated excerpts are excluded. Repetition can be intentional; this rule does not establish a failure."
                  : "Agent message volume within a room and UTC day, using eligible known-agent messages as the denominator. Volume does not measure influence, cooperation, or quality."}
              </p>
              <span>
                Scope: indexed AI Village chat messages · events excluded to
                avoid counting the same message twice
              </span>
            </div>
          </div>
          {error && (
            <div className="message-banner error" role="alert">
              {error}
            </div>
          )}
          {result?.data.kind === kind ? (
            <>
              <div className="pattern-results-heading">
                <span>{result.data.patterns.length} candidates shown</span>
                <small>
                  Built {dateLabel(result.data.built_at)}
                  {result.truncated ? " · bounded result set" : ""}
                </small>
              </div>
              <div className="pattern-list">
                {result.data.patterns.map((p) => (
                  <article className="pattern-card" key={p.id}>
                    <div className="pattern-count">
                      <strong>
                        {kind === "exact_repetition"
                          ? p.count
                          : typeof p.share === "number"
                            ? `${Math.round(p.share * 100)}%`
                            : "—"}
                      </strong>
                      <span>
                        {kind === "exact_repetition"
                          ? "occurrences"
                          : "message share"}
                      </span>
                    </div>
                    <div className="pattern-content">
                      <span className="finding-kind hypothesis">
                        Pattern candidate · not a failure label
                      </span>
                      <p>
                        {p.text ||
                          `${p.agent_name || p.agent_id || "Unknown agent"} · ${p.day || "Day unknown"} · ${p.room_name || p.room_id || "Unknown room"}`}
                      </p>
                      <div className="pattern-meta">
                        {kind === "exact_repetition" ? (
                          <>
                            <span>{p.actor_count ?? "—"} recorded actors</span>
                            <span>
                              {dateLabel(p.first)} → {dateLabel(p.last)}
                            </span>
                            {!!p.unknown_actor_occurrences && (
                              <span>
                                {p.unknown_actor_occurrences} unknown-actor
                                occurrences
                              </span>
                            )}
                          </>
                        ) : (
                          <span>
                            {p.message_count} / {p.eligible_agent_messages}{" "}
                            eligible agent messages
                          </span>
                        )}
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onOpen(p, result)}
                        disabled={!p.source_ids?.length}
                      >
                        Inspect source examples
                        <ArrowUpRight size={14} />
                      </Button>
                    </div>
                  </article>
                ))}
              </div>
              {!result.data.patterns.length && (
                <div className="empty-state bordered">
                  No candidates met this rule in the current indexed corpus.
                </div>
              )}
              <details className="pattern-method">
                <summary>Inspect the reproducible rule and coverage</summary>
                <pre>
                  {JSON.stringify(
                    {
                      definition: result.data.definition,
                      qualification: result.data.qualification,
                      snapshot: result.snapshot,
                      coverage: result.coverage,
                    },
                    null,
                    2,
                  )}
                </pre>
              </details>
            </>
          ) : (
            !error && (
              <div className="empty-state">
                <Loader2 className="spin" />
                Loading the computed pattern index…
              </div>
            )
          )}
        </>
      )}
    </div>
  );
}
