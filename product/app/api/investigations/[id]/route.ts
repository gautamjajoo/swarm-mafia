import { db, fail, signedIn, smallBody, writeGuard } from "@/lib/server";
import { saveSchema } from "@/lib/investigations";
export const dynamic = "force-dynamic";
type Context = { params: Promise<{ id: string }> };
export async function GET(request: Request, context: Context) {
  if (!signedIn(request)) return fail("Sign in required", 401);
  const { id } = await context.params;
  try {
    const row = await db()
      .prepare("SELECT * FROM investigations WHERE id=?")
      .bind(id)
      .first<{ state: string } & Record<string, unknown>>();
    if (!row) return fail("Investigation not found", 404);
    return Response.json(
      { ...row, state: JSON.parse(row.state) },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch {
    return fail("Could not load this investigation.", 503);
  }
}
export async function PUT(request: Request, context: Context) {
  if (!signedIn(request)) return fail("Sign in required", 401);
  const { id } = await context.params;
  let parsed;
  try {
    writeGuard(request);
    parsed = saveSchema.safeParse(await smallBody(request));
  } catch {
    return fail("Invalid investigation request.");
  }
  if (!parsed.success || !parsed.data.revision)
    return fail("Valid investigation and revision required.");
  try {
    const { title, source, snapshot, state, revision } = parsed.data,
      now = new Date().toISOString();
    const result = await db()
      .prepare(
        "UPDATE investigations SET title=?,source=?,snapshot=?,state=?,revision=revision+1,updated_at=? WHERE id=? AND revision=?",
      )
      .bind(title, source, snapshot, JSON.stringify(state), now, id, revision)
      .run();
    if (result.meta.changes === 0)
      return fail(
        "This investigation changed in another session. Export your current work before reopening the saved version.",
        409,
      );
    return Response.json({ id, revision: revision + 1, updated_at: now });
  } catch {
    return fail("Could not save. Your changes remain on this page.", 503);
  }
}
