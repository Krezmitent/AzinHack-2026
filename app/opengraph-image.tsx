import { ImageResponse } from "next/og";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = "AutoGrant — Find grants. Know why.";

export default function OpenGraphImage() {
  return new ImageResponse(
    <div style={{ display: "flex", position: "relative", width: "100%", height: "100%", overflow: "hidden", background: "#fff", color: "#13263d", fontFamily: "Arial, sans-serif" }}>
      <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", width: 740, padding: "58px 0 56px 66px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 11, fontSize: 31, fontWeight: 700, letterSpacing: -2.3 }}>
          <svg width="39" height="39" viewBox="0 0 42 42"><path d="M6 34.5 17.7 7h7.1L13.2 34.5H6Z" fill="#3f5bff"/><path d="m24.8 7 11.6 27.5h-7.2L21.3 15l3.5-8Z" fill="#3f5bff"/><path d="M19.3 25.7h10.1" stroke="#fff" strokeWidth="5.2"/><path d="M32.6 4.5h5.1v5.1h-5.1z" fill="#ff775c"/></svg>
          autogrant
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div style={{ display: "flex", flexDirection: "column", fontSize: 86, lineHeight: .98, letterSpacing: -5.7, fontWeight: 700 }}><span>Find grants.</span><span>Know why.</span></div>
          <div style={{ display: "flex", width: 540, color: "#526a7e", fontSize: 23, lineHeight: 1.4 }}>The source, the fit, and the next step in one place.</div>
        </div>
        <div style={{ display: "flex", width: 540, height: 2, background: "#bdccd6" }} />
      </div>
      <div style={{ display: "flex", position: "absolute", top: 72, right: 62, width: 365, height: 490, flexDirection: "column", padding: 30, border: "1px solid #bdccd6", background: "#edf3f7" }}>
        <div style={{ display: "flex", justifyContent: "space-between", color: "#526a7e", fontSize: 15, fontWeight: 700 }}><span>Search brief</span><span>01 / 03</span></div>
        <div style={{ display: "flex", marginTop: 55, fontSize: 38, lineHeight: 1.1, letterSpacing: -2.1, fontWeight: 700 }}>Your funding search, in focus.</div>
        <div style={{ display: "flex", height: 2, marginTop: 35, background: "#bdccd6" }} />
        <div style={{ display: "flex", marginTop: 24, fontSize: 17, color: "#526a7e" }}>Original sources</div>
        <div style={{ display: "flex", marginTop: 20, fontSize: 17, color: "#526a7e" }}>Fit with context</div>
        <div style={{ display: "flex", marginTop: 20, fontSize: 17, color: "#526a7e" }}>Your decision</div>
        <div style={{ display: "flex", width: 23, height: 23, position: "absolute", right: 26, bottom: 27, background: "#3f5bff", transform: "rotate(45deg)" }} />
      </div>
    </div>, size
  );
}
