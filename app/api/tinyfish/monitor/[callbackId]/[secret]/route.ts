type Context = { params: Promise<{ callbackId: string; secret: string }> };
export const maxDuration = 15;

export async function POST(request: Request, context: Context) {
  const { callbackId, secret } = await context.params;
  if (!/^[a-f0-9]{32}$/.test(callbackId) || !/^[A-Za-z0-9_-]{43}$/.test(secret)) {
    return Response.json({ detail: "Invalid callback." }, { status: 403 });
  }
  const serviceUrl = process.env.PYTHON_SERVICE_URL;
  if (!serviceUrl) return Response.json({ detail: "Callback service unavailable." }, { status: 503 });
  const reader = request.body?.getReader();
  if (!reader) return Response.json({ detail: "Missing callback body." }, { status: 400 });
  const chunks: Uint8Array[] = [];
  let size = 0;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > 512 * 1024) {
      await reader.cancel();
      return Response.json({ detail: "Payload too large." }, { status: 413 });
    }
    chunks.push(value);
  }
  try {
    const body = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { body.set(chunk, offset); offset += chunk.byteLength; }
    const response = await fetch(`${serviceUrl}/webhooks/tinyfish/monitor/${callbackId}/${secret}`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body, signal: AbortSignal.timeout(9000)
    });
    return Response.json(await response.json(), { status: response.status });
  } catch {
    return Response.json({ detail: "Callback persistence unavailable." }, { status: 503 });
  }
}
