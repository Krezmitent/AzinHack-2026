import { forwardToPython } from "../_proxy";
export const maxDuration = 75;
export async function POST(request: Request) { return forwardToPython(request, "/api/score-grant"); }
