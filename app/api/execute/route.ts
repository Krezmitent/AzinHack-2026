import { forwardToPython } from "../_proxy";
export const maxDuration = 200;
export async function POST(request: Request) { return forwardToPython(request, "/api/execute-application"); }
