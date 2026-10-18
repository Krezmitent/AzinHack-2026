import { forwardToPython } from "../_proxy";
export const maxDuration = 110;
export async function POST(request: Request) { return forwardToPython(request, "/api/discover-grants"); }
