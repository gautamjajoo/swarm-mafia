import { config, fail, signedIn, smallBody, smallTextBody, writeGuard } from "@/lib/server";

export const dynamic = "force-dynamic";
type Context = { params: Promise<{ path: string[] }> };
const reads = new Set([
  "stats",
  "agents",
  "overview",
  "search",
  "timeline",
  "graph",
  "context",
  "patterns",
]);
const params = new Set([
  "source",
  "q",
  "agent_id",
  "table",
  "from",
  "to",
  "limit",
  "cursor",
  "seed",
  "hops",
  "before",
  "after",
  "mode",
  "kind",
  "version",
]);

async function proxy(request: Request, context: Context) {
  if (!signedIn(request))
    return fail("Sign in to this private workspace to access evidence.", 401);
  const { path } = await context.params;
  const method = request.method;
  const reviewJob = path.length === 2 && path[0] === "reviews" && /^[a-zA-Z0-9_-]{1,80}$/.test(path[1]);
  const society = path[0] === "society";
  const societyRun = path.length >= 3 && path[1] === "runs" && /^[a-zA-Z0-9_-]{1,128}$/.test(path[2]);
  const societyRead = society && (
    (path.length === 2 && ["protocol", "runs"].includes(path[1])) ||
    (societyRun && (path.length === 3 || (path.length === 4 && ["graph", "review"].includes(path[3])))) ||
    (path.length === 3 && path[1] === "worlds" && path[2] === "catalog")
  );
  const societyWrite = society && (
    (path.length === 2 && path[1] === "runs") ||
    (societyRun && path.length === 4 && path[3] === "investigate") ||
    (path.length === 3 && path[1] === "worlds" && path[2] === "replay")
  );
  const valid =
    method === "GET"
      ? societyRead || reviewJob || (path.length === 1 && reads.has(path[0])) ||
        ((path.length === 3 || (path.length === 4 && path[3] === "raw")) &&
          path[0] === "records" &&
          path.slice(1).every((p) => /^[a-zA-Z0-9_.:-]{1,200}$/.test(p)))
      : (method === "POST" && (societyWrite || (path.length === 1 && ["investigate", "reviews"].includes(path[0])))) ||
        (method === "DELETE" && reviewJob);
  if (!valid) return fail("Unknown evidence operation", 404);
  const base = config("OBSERVATORY_API_URL");
  const token = config("OBSERVATORY_API_TOKEN");
  if (!base || !token)
    return fail("The evidence service is not configured yet.", 503);
  const target = new URL("/v1/" + path.map(encodeURIComponent).join("/"), base);
  for (const [key, value] of new URL(request.url).searchParams) {
    if (!params.has(key) || value.length > 2000)
      return fail("Invalid query parameter");
    target.searchParams.set(key, value);
  }
  try {
    let body: string | undefined;
    if (method === "DELETE") writeGuard(request);
    if (method === "POST") {
      writeGuard(request);
      body = society && path.length === 2 && path[1] === "runs"
        ? await smallTextBody(request, 1048576)
        : JSON.stringify(await smallBody(request, 64000));
    }
    const response = await fetch(target, {
      method,
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body,
      signal: AbortSignal.timeout(method === "POST" ? 150000 : 30000),
      redirect: "manual",
    });
    if (response.status >= 300 && response.status < 400)
      return fail("The evidence service returned an unexpected redirect.", 502);
    if (response.status === 401 || response.status === 403)
      return fail(
        "The evidence service could not authenticate this workspace.",
        503,
      );
    if (!response.headers.get("content-type")?.includes("application/json"))
      return fail("The evidence service returned an unexpected response.", 502);
    return new Response(response.body, {
      status: response.status,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch (error) {
    console.warn(
      "Evidence proxy unavailable",
      error instanceof Error
        ? error.name + ": " + error.message
        : "Unknown failure",
    );
    if (
      error instanceof Error &&
      [
        "Request too large",
        "Cross-origin writes are not allowed",
        "JSON body required",
      ].includes(error.message)
    )
      return fail(error.message);
    return fail(
      "The evidence service is temporarily unavailable. Your question has been preserved; try again.",
      503,
    );
  }
}
export const GET = proxy;
export const POST = proxy;
export const DELETE = proxy;
