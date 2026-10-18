import { NextResponse } from "next/server";
import { forwardToPython } from "../../_proxy";

export async function GET(request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  if (!/^[a-f0-9]{64}$/.test(id)) {
    return NextResponse.json({ detail: "Invalid application run ID." }, { status: 422 });
  }
  return forwardToPython(request, `/api/application-runs/${id}`, "GET");
}
