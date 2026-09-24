import { useState } from "react";

export default function TraceLog({ trace }) {
  const [open, setOpen] = useState(false);
  if (!trace?.length) return null;

  return (
    <div style={{ maxWidth: 720, margin: "12px auto 40px", padding: "0 24px" }}>
      <button className="btn-ghost" onClick={() => setOpen((o) => !o)} style={{ padding: 0, fontSize: 12 }}>
        {open ? "Hide" : "Show"} agent trace ({trace.length})
      </button>
      {open && (
        <div className="panel" style={{ marginTop: 10, padding: "14px 16px" }}>
          {trace.map((t, i) => (
            <div key={i} style={{ display: "flex", gap: 10, fontSize: 12, padding: "5px 0", borderBottom: i < trace.length - 1 ? "1px solid var(--line)" : "none" }}>
              <span className="dim" style={{ width: 78, flexShrink: 0, fontFamily: "monospace", fontSize: 10.5, paddingTop: 2 }}>{t.kind}</span>
              <span>{t.text}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
