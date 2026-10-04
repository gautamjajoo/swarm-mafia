import { db, fail, signedIn, smallBody, writeGuard } from "@/lib/server";
import { saveSchema } from "@/lib/investigations";
export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  if (!signedIn(request)) return fail("Sign in required", 401);
  try {
    const result = await db()
      .prepare(
        "SELECT id,title,source,snapshot,revision,created_at,updated_at FROM investigations ORDER BY updated_at DESC LIMIT 100",
      )
      .all();
    return Response.json(
      { data: result.results },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch {
    return fail("Saved investigations are temporarily unavailable.", 503);
  }
}
export async function POST(request: Request) {
  if (!signedIn(request)) return fail("Sign in required", 401);
  let parsed;
  try {
    writeGuard(request);
    parsed = saveSchema.safeParse(await smallBody(request));
  } catch {
    return fail("Invalid investigation request.");
  }
  if (!parsed.success)
    return fail(
      "The investigation exceeds a field limit or contains invalid data.",
    );
  try {
    const { title, source, snapshot, state } = parsed.data;
    const id = crypto.randomUUID(),
      now = new Date().toISOString();
    const author =
      request.headers.get("oai-authenticated-user-id") || "workspace-service";
    await db()
      .prepare(
        "INSERT INTO investigations (id,title,source,snapshot,state,revision,created_at,updated_at,author) VALUES (?,?,?,?,?,1,?,?,?)",
      )
      .bind(
        id,
        title,
        source,
        snapshot,
        JSON.stringify(state),
        now,
        now,
        author,
      )
      .run();
    return Response.json({ id, revision: 1, updated_at: now }, { status: 201 });
  } catch {
    return fail(
      "Could not save. Your investigation is still open; retry without leaving the page.",
      503,
    );
  }
}
