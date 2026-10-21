import { forwardToPython } from "../../_proxy";

type Context = { params: Promise<{ path?: string[] }> };
const allowedPath = /^(?:|drafts\/[a-f0-9]{64})$/;

async function forward(request: Request, context: Context, method: "GET" | "POST") {
  const path = ((await context.params).path ?? []).join("/");
  if (!allowedPath.test(path)) return Response.json({ detail: "Unknown workspace endpoint." }, { status: 404 });
  return forwardToPython(request, `/api/workspace${path ? `/${path}` : ""}`, method);
}

export async function GET(request: Request, context: Context) { return forward(request, context, "GET"); }
export async function POST(request: Request, context: Context) { return forward(request, context, "POST"); }
