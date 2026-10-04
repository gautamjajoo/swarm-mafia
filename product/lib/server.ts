import { env } from "cloudflare:workers";

export function db(): D1Database {
  if (!env.DB) throw new Error("Workspace storage is unavailable");
  return env.DB;
}

export function signedIn(request: Request) {
  return Boolean(request.headers.get("oai-authenticated-user-id"));
}

export function writeGuard(request: Request) {
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin)
    throw new Error("Cross-origin writes are not allowed");
  if (!request.headers.get("content-type")?.includes("application/json"))
    throw new Error("JSON body required");
}

export async function smallBody(request: Request, max = 1000000) {
  if (Number(request.headers.get("content-length") || 0) > max)
    throw new Error("Request too large");
  const reader = request.body?.getReader();
  if (!reader) throw new Error("Request body required");
  const chunks: Uint8Array[] = [];
  let length = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    length += value.length;
    if (length > max) {
      await reader.cancel();
      throw new Error("Request too large");
    }
    chunks.push(value);
  }
  const bytes = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.length;
  }
  return JSON.parse(new TextDecoder().decode(bytes));
}

export function fail(message: string, status = 400) {
  return Response.json(
    { detail: message },
    { status, headers: { "Cache-Control": "no-store" } },
  );
}

export function config(key: "OBSERVATORY_API_URL" | "OBSERVATORY_API_TOKEN") {
  return (
    (env as unknown as Record<string, string>)[key] || process.env[key] || ""
  );
}
