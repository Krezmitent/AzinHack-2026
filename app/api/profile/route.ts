import { forwardToPython } from "../_proxy";

export async function GET(request: Request) {
  return forwardToPython(request, "/api/profile", "GET");
}

export async function POST(request: Request) {
  return forwardToPython(request, "/api/profile", "POST");
}
