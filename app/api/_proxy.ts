import { NextResponse } from "next/server";

export async function forwardToPython(request: Request, endpoint: string) {
  try {
    const body = await request.json();
    const response = await fetch(`${process.env.PYTHON_SERVICE_URL || "http://localhost:8000"}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store"
    });
    const data = await response.json().catch(() => ({ detail: "Automation service returned an invalid response." }));
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ detail: error instanceof Error ? error.message : "Automation service is unavailable." }, { status: 502 });
  }
}
