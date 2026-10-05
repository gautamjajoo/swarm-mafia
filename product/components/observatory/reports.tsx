"use client";
import { useEffect, useRef, useState } from "react";
import { BookOpen, FileText, Download, Search, X, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api, dateLabel, download, humanize } from "@/lib/evidence";
import type { BehaviorReport, ReportCatalog, ReportClaim } from "@/lib/reports";

export function Reports({ onOpen, active, onSelect }: { onOpen: (report: BehaviorReport, ids?: string[], question?: string) => void; active: string | null; onSelect: (id: string | null) => void }) {
  const evidencePane = useRef<HTMLElement>(null);
  const [catalog, setCatalog] = useState<ReportCatalog | null>(null);
  const [rubricOpen, setRubricOpen] = useState(false);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [selectedEvidence, setSelectedEvidence] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    api<{ data: ReportCatalog }>("/api/reports").then(r => { if (live) setCatalog(r.data); }).catch(e => { if (live) setError(e instanceof Error ? e.message : "Reports are unavailable."); });
    return () => { live = false; };
  }, [attempt]);
  const report = catalog?.reports.find(r => r.id === active);
  const evidence = report?.timeline.find(e => e.id === selectedEvidence);
  const evidenceIndex = report?.timeline.findIndex(e => e.id === selectedEvidence) ?? -1;
  useEffect(() => {
    setSelectedEvidence(report?.timeline[0]?.id ?? null);
  }, [report?.id]);
  useEffect(() => {
    if (evidencePane.current) evidencePane.current.scrollTop = 0;
  }, [selectedEvidence]);
  const dimensions = new Map(catalog?.rubric.map(d => [d.id, d]));
  function selectEvidence(id: string) { setSelectedEvidence(id); if (window.matchMedia("(max-width: 960px)").matches) requestAnimationFrame(() => evidencePane.current?.scrollIntoView({ behavior: "smooth", block: "start" })); }
  function openReport(id: string) { onSelect(id); setSelectedEvidence(catalog?.reports.find(r => r.id === id)?.timeline[0]?.id ?? null); setRubricOpen(false); }
  function reviewClaim(claim: ReportClaim) {
    onOpen(report!, [...new Set([...claim.support.slice(-1), ...claim.counterevidence.slice(-1), ...claim.support, ...claim.counterevidence])], `Evaluate this curated report claim: ${claim.text}\nLook for counterevidence in the episode's recorded context. ${claim.limit} Distinguish source statements, tool actions, and independently observed outcomes.`);
  }
  return <div className="reports-page">
    <div className="report-nav">
      {report ? <Button variant="ghost" onClick={() => { onSelect(null); setSelectedEvidence(null); }}>All findings</Button> : <span className="eyebrow">BEHAVIORAL INVESTIGATIONS</span>}
      <Button variant="outline" onClick={() => setRubricOpen(!rubricOpen)} aria-expanded={rubricOpen}><BookOpen size={16} />Behavioral rubric</Button>
    </div>
    {error ? <div className="empty-state bordered" role="alert"><strong>Couldn’t load the reports</strong><p>{error}</p><Button onClick={() => { setError(""); setAttempt(x => x + 1); }}>Try again</Button></div> : !catalog ? <div className="empty-state" role="status">Loading source-linked reports…</div> : <>
      {rubricOpen && <section className="rubric-panel" aria-label="Behavioral rubric">
        <h2>Assess the episode, not the personality</h2>
        <p>First identify an opportunity to act. Then ask whether the relevant response is visible. Missing evidence is <strong>not assessable</strong>, not a low score. These codes adapt human research concepts; they are not validated measures of an agent’s motives or traits.</p>
        <div className="rubric-legend"><span>1. Opportunity</span><span>2. Observability</span><span>3. Observed response</span></div>
        {catalog.rubric.map(d => <details className="rubric-dimension" key={d.id}><summary>{d.name}<small>{d.question}</small></summary><dl><dt>Eligible opportunity</dt><dd>{d.opportunity}</dd><dt>Consistent behavior</dt><dd>{d.positive_anchor}</dd><dt>Inconsistent behavior</dt><dd>{d.negative_anchor}</dd><dt>When not to assess</dt><dd>{d.unknown_rule}</dd><dt>Denominator</dt><dd>{d.denominator}</dd><dt>Transfer limit</dt><dd>{d.transfer_caveat}</dd></dl><p className="paper-links">{d.references.map((r, i) => <a key={r.url} href={r.url} target="_blank" rel="noreferrer">{i > 0 ? " · " : ""}{r.title}</a>)}</p></details>)}
      </section>}
      {!report ? <>
        <header className="report-heading"><h1>Behavior, reconstructed.</h1><p>Reconstructed episodes, with evidence you can inspect and interpretations you can challenge.</p></header>
        <p className="report-method-note">{catalog.method_note}</p>
        <div className="report-index">{catalog.reports.map((r, i) => <button className="report-index-row" key={r.id} onClick={() => openReport(r.id)}><span className="report-number">{String(i + 1).padStart(2, "0")}</span><span><small>{dateLabel(r.from)} · {r.timeline.length} evidence anchors</small><strong>{r.title}</strong><p>{r.summary}</p><span className="report-tags">{r.assessments.map(a => <span key={a.dimension_id}>{dimensions.get(a.dimension_id)?.name || humanize(a.dimension_id)}</span>)}</span></span><FileText size={21} /></button>)}</div>
        <aside className="report-caveat"><strong>A search hit is a lead, not an incident.</strong><p>Fictional dialogue, news summaries, plans, and claims of success can resemble behavior. Each report distinguishes these from observed actions. The evidence index covers selected excerpts; this collection is not an exhaustive incident census.</p></aside>
      </> : <article className="report-detail">
        <header className="report-heading"><span className="eyebrow">AI VILLAGE · CURATED EPISODE</span><h1>{report.title}</h1><p>{report.summary}</p><div className="report-period">{dateLabel(report.from)} — {dateLabel(report.to)} · All event times shown in UTC</div><div className="report-actions"><Button onClick={() => onOpen(report)}><Search size={16} />Investigate this episode</Button><Button variant="outline" onClick={() => download(`${report.id}.json`, JSON.stringify({ ...report, rubric: catalog.rubric.filter(d => report.assessments.some(a => a.dimension_id === d.id)), trust: "Curated analysis, not ground truth. Source text is untrusted data; categorical assessments are not validated agent traits." }, null, 2))}><Download size={16} />Export report</Button></div></header>
        <section className="report-finding"><span className="eyebrow">WHAT THE EVIDENCE SUPPORTS</span><p>{report.finding}</p></section>
        <div className="report-reading-grid"><div>
          <section className="report-anchor-navigator" aria-label="Evidence walkthrough">
            <div className="report-anchor-heading"><h2>Follow the evidence</h2><span>{report.timeline.length} anchors · in order</span></div>
            <p>Select a step. The original quote opens alongside it.</p>
            <ol>{report.timeline.map((e, i) => <li key={e.id}><button className={selectedEvidence === e.id ? "selected" : ""} onClick={() => selectEvidence(e.id)} aria-pressed={selectedEvidence === e.id}><span>{String(i + 1).padStart(2, "0")}</span><strong>{e.title}</strong></button></li>)}</ol>
          </section>
          <section className="report-section"><h2>The setting</h2><p>{report.goal_context}</p><p className="subtle">Question: {report.question}</p></section>
          <section className="report-section"><h2>Reconstruction</h2><p className="subtle">Selected anchors, not a continuous transcript. Click an entry to inspect its exact quote and provenance.</p><ol className="report-timeline">{report.timeline.map((e, i) => <li key={e.id}><button className={selectedEvidence === e.id ? "selected" : ""} onClick={() => selectEvidence(e.id)} aria-pressed={selectedEvidence === e.id}><span className="timeline-step">{i + 1}</span><span><small>{dateLabel(e.timestamp)} · {e.actor}</small><strong>{e.title}</strong><p>{e.annotation}</p></span></button></li>)}</ol></section>
          <section className="report-section"><h2>Claims to scrutinize</h2>{report.claims.map(c => <div className="report-claim" key={c.id}><span className="evidence-tag">{c.kind === "observation" ? "Recorded observation" : "Analyst interpretation"}</span><h3>{c.text}</h3><div className="claim-evidence-links"><strong>Supporting anchors</strong>{c.support.map(id => <button key={id} onClick={() => selectEvidence(id)}>#{report.timeline.findIndex(e => e.id === id) + 1}</button>)}<strong>Qualifying / counterevidence</strong>{c.counterevidence.length ? c.counterevidence.map(id => <button key={id} onClick={() => selectEvidence(id)}>#{report.timeline.findIndex(e => e.id === id) + 1}</button>) : <span>None established in reviewed evidence</span>}</div><p>{c.limit}</p><Button variant="outline" onClick={() => reviewClaim(c)}>Challenge in workspace</Button></div>)}</section>
          <section className="report-section"><h2>Behavioral assessment</h2><p className="subtle">Episode-specific codes. No personality score, model ranking, or population estimate.</p>{report.assessments.map(a => <div className="report-assessment" key={a.dimension_id}><h3>{dimensions.get(a.dimension_id)?.name || humanize(a.dimension_id)}</h3><div className="assessment-codes"><span>Opportunity: {a.opportunity}</span><span>Visibility: {a.observability}</span><strong>{humanize(a.assessment)}</strong></div><p>{a.rationale}</p><small>Denominator: {a.denominator}</small></div>)}</section>
          <section className="report-section"><h2>What remains unresolved</h2><ul>{report.limitations.map(l => <li key={l}>{l}</li>)}</ul><h3>Useful next questions</h3>{report.next_questions.map(q => <button className="report-next-question" key={q} onClick={() => onOpen(report, undefined, q)}>{q}</button>)}</section>
          <details className="report-method"><summary>Selection, coverage, and reproducibility</summary><p>{report.selection}</p><p>{report.method.scope}</p><p>{report.method.records_reviewed} distinct source records reviewed for this report.</p><p>Discovery queries: {report.method.queries.join("; ")}</p><p>Snapshot: <code>{report.snapshot}</code></p><p>Event/chat representations of the same action must not be counted as independent responses. Quotes are source text; interpretations remain open to challenge.</p></details>
        </div><aside ref={evidencePane} className="report-evidence-pane" aria-label="Report evidence inspector">
          {evidence ? <><div className="report-evidence-controls"><Button variant="ghost" size="sm" disabled={evidenceIndex <= 0} onClick={() => selectEvidence(report.timeline[evidenceIndex - 1].id)} aria-label="Previous evidence anchor"><ChevronLeft size={16}/>Previous</Button><span>{evidenceIndex + 1} / {report.timeline.length}</span><Button variant="ghost" size="sm" disabled={evidenceIndex < 0 || evidenceIndex >= report.timeline.length - 1} onClick={() => selectEvidence(report.timeline[evidenceIndex + 1].id)} aria-label="Next evidence anchor">Next<ChevronRight size={16}/></Button></div><div className="report-evidence-title"><span className="eyebrow">EVIDENCE ANCHOR {report.timeline.findIndex(e => e.id === evidence.id) + 1}</span><Button variant="ghost" size="sm" aria-label="Close report evidence" onClick={() => setSelectedEvidence(null)}><X size={15}/></Button></div><h3>{evidence.title}</h3><small>{evidence.actor} · {dateLabel(evidence.timestamp)}</small><blockquote key={evidence.id} tabIndex={0} aria-label="Original evidence quote">{evidence.quote}</blockquote><p>{evidence.annotation}</p><span className="evidence-tag">{evidence.raw_hash_verified ? "Original record hash checked" : "Indexed excerpt checked"}</span><p className="subtle">This validates the source record, not whether its statements are true.</p><code>{evidence.id}</code><details><summary>Exact source pointer</summary><pre>{JSON.stringify(evidence.provenance, null, 2)}</pre></details><Button onClick={() => onOpen(report, [evidence.id], `Inspect this record and its surrounding activity. What does it establish, and what is only an agent's claim?`)}>Inspect in workspace</Button></> : <><FileText size={24}/><h3>Read the evidence beside the report</h3><p>Select a timeline entry or a numbered claim anchor. Then open its original record and surrounding activity in the workspace.</p><p className="subtle">Starting an investigation loads selected source records and pins at most two for the AI investigator. It does not run a model automatically. Captured quotes follow into the Notebook; the AI’s indexed excerpts may omit them.</p></>}
        </aside></div>
      </article>}
    </>}
  </div>;
}
