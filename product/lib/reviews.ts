import type { ReviewJob, InvestigationResult } from "./evidence";

function pause(signal: AbortSignal, ms: number) {
  return new Promise<void>((resolve, reject) => {
    const abort = () => { clearTimeout(timer); reject(new DOMException("Review stopped", "AbortError")); };
    const timer = setTimeout(() => { signal.removeEventListener("abort", abort); resolve(); }, ms);
    if (signal.aborted) abort();
    else signal.addEventListener("abort", abort, { once: true });
  });
}

export async function followReview(
  job: ReviewJob,
  signal: AbortSignal,
  onProgress: (job: ReviewJob) => void,
  read: (id: string) => Promise<ReviewJob>,
  interval = 2000,
): Promise<InvestigationResult> {
  const deadline = Date.now() + 12 * 60 * 1000;
  while (true) {
    signal.throwIfAborted();
    onProgress(job);
    if (job.status === "completed") {
      if (!job.result) throw new Error("The review completed without a result. Your question is preserved.");
      return { ...job.result, progress: job.progress };
    }
    if (job.status === "failed" || job.status === "cancelled")
      throw new Error(job.error || "This review stopped before completion. Your question is preserved.");
    if (Date.now() >= deadline)
      throw new Error("The review took longer than expected. Your question is preserved; the server stops reviews at its time limit.");
    await pause(signal, interval);
    job = await read(job.id);
  }
}
