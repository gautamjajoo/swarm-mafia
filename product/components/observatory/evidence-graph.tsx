"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Minus, Plus, Maximize2 } from "lucide-react";
import { GraphData, RecordItem, humanize, label } from "@/lib/evidence";
const colors = [
  "#2864de",
  "#0f8275",
  "#8457bf",
  "#b17924",
  "#b34d71",
  "#64748b",
];
export function EvidenceGraph({
  data,
  selected,
  onSelect,
  truncated,
}: {
  data: GraphData;
  selected?: string;
  onSelect: (r: RecordItem) => void;
  truncated: boolean;
}) {
  const [scale, setScale] = useState(1),
    [edgeId, setEdgeId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [viewportWidth, setViewportWidth] = useState(720);
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) =>
      setViewportWidth(entries[0].contentRect.width),
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  const layout = useMemo(() => {
    const groups = new Map<string, RecordItem[]>();
    for (const r of data.nodes) {
      if (!groups.has(r.table)) groups.set(r.table, []);
      groups.get(r.table)!.push(r);
    }
    const width = Math.max(260, groups.size * 240),
      height = Math.max(
        320,
        ...[...groups.values()].map((r) => r.length * 76 + 220),
      );
    const pos = new Map<string, { x: number; y: number; color: string }>();
    [...groups.entries()].forEach(([, rows], col) =>
      rows.forEach((r, i) =>
        pos.set(r.id, {
          x: 35 + col * 240,
          y: 75 + i * 76 + (col % 3) * 60,
          color: colors[col % colors.length],
        }),
      ),
    );
    return { groups, pos, width, height };
  }, [data]);
  const fit = Math.max(0.7, Math.min(1, viewportWidth / layout.width));
  const edge = data.edges.find((e) => e.id === edgeId);
  if (!data.nodes.length)
    return (
      <div className="empty-state">
        No indexed relationships for this record yet.
      </div>
    );
  return (
    <div className="graph-container">
      <div className="graph-toolbar">
        <span>
          {data.nodes.length} records · {data.edges.length} recorded links
        </span>
        <div>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Zoom out"
            onClick={() => setScale((s) => Math.max(0.5, s - 0.15))}
          >
            <Minus size={14} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Reset graph zoom"
            onClick={() => setScale(1)}
          >
            <Maximize2 size={14} />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Zoom in"
            onClick={() => setScale((s) => Math.min(2, s + 0.15))}
          >
            <Plus size={14} />
          </Button>
        </div>
      </div>
      <div className="graph-scroll" ref={scrollRef}>
        <svg
          width={layout.width * scale * fit}
          height={layout.height * scale * fit}
          viewBox={`0 0 ${layout.width} ${layout.height}`}
          role="group"
          aria-label="Recorded relationships. Select a record to inspect it; select a link for its source field."
        >
          <defs>
            <pattern
              id="evidence-dots"
              width="18"
              height="18"
              patternUnits="userSpaceOnUse"
            >
              <circle cx="1" cy="1" r=".6" fill="#c7d2e2" />
            </pattern>
            <marker
              id="edge-arrow"
              markerWidth="7"
              markerHeight="7"
              refX="6"
              refY="3.5"
              orient="auto"
            >
              <path d="M0,0 L7,3.5 L0,7" fill="#a2b2c5" />
            </marker>
          </defs>
          <rect
            width={layout.width}
            height={layout.height}
            fill="url(#evidence-dots)"
          />
          {[...layout.groups.keys()].map((g, i) => (
            <text key={g} x={35 + i * 240} y="30" className="graph-group">
              {humanize(g)}
            </text>
          ))}
          {data.edges.map((e) => {
            const a = layout.pos.get(e.source),
              b = layout.pos.get(e.target);
            if (!a || !b) return null;
            const same = a.x === b.x;
            const startX = same ? a.x + 190 : a.x < b.x ? a.x + 190 : a.x;
            const endX = same ? b.x + 190 : a.x < b.x ? b.x : b.x + 190;
            const path = same
              ? `M${startX},${a.y + 25} C${startX + 28},${a.y + 25} ${endX + 28},${b.y + 25} ${endX},${b.y + 25}`
              : `M${startX},${a.y + 25} C${(startX + endX) / 2},${a.y + 25} ${(startX + endX) / 2},${b.y + 25} ${endX},${b.y + 25}`;
            return (
              <g
                key={e.id}
                tabIndex={0}
                role="button"
                aria-label={`${e.type}: ${e.source} to ${e.target}`}
                onClick={() => setEdgeId(e.id)}
                onKeyDown={(ev) => {
                  if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    setEdgeId(e.id);
                  }
                }}
              >
                <title>{e.type} · recorded relationship</title>
                <path
                  d={path}
                  fill="none"
                  stroke="transparent"
                  strokeWidth="14"
                />
                <path
                  d={path}
                  fill="none"
                  stroke={edgeId === e.id ? "#2864de" : "#adbed2"}
                  strokeWidth={edgeId === e.id ? 2.5 : 1.2}
                  markerEnd="url(#edge-arrow)"
                />
              </g>
            );
          })}
          {data.nodes.map((r) => {
            const p = layout.pos.get(r.id)!;
            return (
              <g
                key={r.id}
                tabIndex={0}
                role="button"
                aria-label={`Inspect ${label(r)} ${r.source_id}`}
                onClick={() => onSelect(r)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onSelect(r);
                  }
                }}
                className="graph-node"
              >
                <title>
                  {label(r)} · {r.id}
                </title>
                <rect
                  x={p.x}
                  y={p.y}
                  width="190"
                  height="52"
                  rx="7"
                  fill={selected === r.id ? "#edf3ff" : "white"}
                  stroke={selected === r.id ? "#2864de" : "#ccd7e5"}
                  strokeWidth={selected === r.id ? 2 : 1}
                />
                <rect
                  x={p.x}
                  y={p.y + 12}
                  width="3"
                  height="28"
                  rx="1"
                  fill={p.color}
                />
                <text x={p.x + 13} y={p.y + 22} fontSize="12" fill="#243650">
                  {(r.table === "agents"
                    ? label(r)
                    : r.excerpt || label(r)
                  ).slice(0, 24)}
                </text>
                <text x={p.x + 13} y={p.y + 39} fontSize="10" fill="#8392a6">
                  {r.source_id.slice(0, 23)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
      <p className="graph-help">
        Select a record to read it. Select a link to inspect its source field.
        Scroll to explore wider graphs.
      </p>
      {edge && (
        <div className="edge-detail">
          <strong>{edge.type}</strong>
          <span>
            Recorded source field ·{" "}
            {String(edge.provenance?.field || "source relationship")}
          </span>
          <code>
            {String(edge.provenance?.source_record_id || edge.source)}
          </code>
        </div>
      )}
      {!!data.ambiguous_references && (
        <p className="coverage-note">
          {data.ambiguous_references} ambiguous source references. Shared keys
          do not identify a unique parent.
        </p>
      )}
      {(truncated ||
        !!(
          data.unresolved_references || data.unresolved_source_ids?.length
        )) && (
        <p className="coverage-note">
          {truncated
            ? "Bounded neighborhood; more relationships may exist. "
            : ""}
          {!!(
            data.unresolved_references || data.unresolved_source_ids?.length
          ) &&
            `${data.unresolved_references || data.unresolved_source_ids?.length} unresolved source references.`}
        </p>
      )}
    </div>
  );
}
