import { forwardToPython } from "../_proxy";
export async function POST(request: Request) { return forwardToPython(request, "/api/execute-application"); }
