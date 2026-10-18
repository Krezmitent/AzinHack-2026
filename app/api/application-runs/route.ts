import { forwardToPython } from "../_proxy";

export async function GET(request: Request) {
  return forwardToPython(request, "/api/application-runs", "GET");
}
