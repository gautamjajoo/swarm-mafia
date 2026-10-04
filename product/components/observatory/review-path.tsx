import type { ReviewStep } from "@/lib/evidence";
import { humanize } from "@/lib/evidence";

export function ReviewPath({ steps, running = false }: { steps: ReviewStep[]; running?: boolean }) {
  return (
    <details className="review-path" open={running || undefined}>
      <summary>{running ? "Following the evidence" : "How this was investigated"} <span>{steps.length} steps</span></summary>
      <ol>
        {steps.map((step, i) => (
          <li key={`${step.step}-${i}`} className={step.status}>
            <span className="review-step-number">{i + 1}</span>
            <div><strong>{humanize(step.action)}</strong>
              {step.reason && <p>{step.reason}</p>}
              {step.summary && <small>{step.summary}</small>}
              {step.arguments && <details className="review-query"><summary>Query and scope</summary><pre>{JSON.stringify(step.arguments, null, 2)}</pre></details>}
            </div>
          </li>
        ))}
      </ol>
      {!steps.length && <p>Opening the source index and checking the available scope…</p>}
    </details>
  );
}
