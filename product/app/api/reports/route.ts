import { fail, signedIn } from "@/lib/server";
import catalog from "@/data/report-catalog.json";
export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  if (!signedIn(request)) return fail("Sign in required", 401);
  return Response.json({ data: catalog }, { headers: { "Cache-Control": "no-store" } });
}
