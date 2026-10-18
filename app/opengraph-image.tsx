import { ImageResponse } from "next/og";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "AutoGrant — Find funding that fits your startup";

export default function OpenGraphImage() {
  return new ImageResponse(
    <div style={{ display: "flex", width: "100%", height: "100%", background: "#4945e6", color: "#ffffff", position: "relative", overflow: "hidden", fontFamily: "Arial, sans-serif" }}>
      <div style={{ display: "flex", position: "absolute", width: 500, height: 500, right: -75, top: -60, border: "2px solid #7774ee", borderRadius: 250 }} />
      <div style={{ display: "flex", position: "absolute", width: 360, height: 360, right: 0, top: 15, border: "2px solid #7774ee", borderRadius: 180 }} />
      <div style={{ display: "flex", flexDirection: "column", padding: "55px 65px", width: "100%", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", fontSize: 31, fontWeight: 700, letterSpacing: -1 }}><div style={{ display: "flex", flexWrap: "wrap", width: 32, height: 32, gap: 3, marginRight: 12 }}><span style={{ width: 14, height: 14, borderRadius: 5, background: "#c9f2dd" }} /><span style={{ width: 14, height: 14, borderRadius: 5, background: "#c9f2dd" }} /><span style={{ width: 14, height: 14, borderRadius: 5, background: "#c9f2dd" }} /><span style={{ width: 14, height: 14, borderRadius: 5, background: "#c9f2dd" }} /></div>AutoGrant.</div>
        <div style={{ display: "flex", flexDirection: "column", maxWidth: 720 }}><div style={{ display: "flex", flexDirection: "column", fontSize: 82, lineHeight: 0.95, letterSpacing: -5, fontWeight: 700 }}><span>Find funding</span><span>that fits.</span></div><div style={{ display: "flex", marginTop: 29, fontSize: 26, color: "#e9e7ff" }}>Discover grants. Understand the match. Make your case.</div></div>
        <div style={{ display: "flex", width: 275, height: 8, background: "#c9f2dd", borderRadius: 4 }} />
      </div>
      <div style={{ display: "flex", position: "absolute", width: 265, height: 335, right: 92, top: 165, background: "#f7f8fc", color: "#1e2443", transform: "rotate(8deg)", padding: 25, flexDirection: "column", boxShadow: "18px 20px 0 #3430af" }}><div style={{ display: "flex", fontSize: 17, fontWeight: 700 }}>Your grant path</div><div style={{ display: "flex", height: 2, background: "#1e2443", marginTop: 14 }} /><div style={{ display: "flex", flexDirection: "column", marginTop: 42, fontSize: 25, fontWeight: 700, lineHeight: 1.2 }}><span>Search</span><span>Match</span><span>Draft</span></div><div style={{ display: "flex", marginTop: "auto", fontSize: 18, color: "#4945e6", fontWeight: 700 }}>Built for founders</div></div>
    </div>,
    size
  );
}
