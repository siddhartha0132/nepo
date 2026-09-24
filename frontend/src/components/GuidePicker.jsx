import { useEffect, useState } from "react";
import { api, money } from "../api.js";

export default function GuidePicker({ tripId, onBooked, onSkip, loading }) {
  const [guides, setGuides] = useState(null);
  const [days, setDays] = useState(1);

  useEffect(() => { api.listGuides(tripId).then(setGuides); }, [tripId]);

  return (
    <div className="panel" style={{ padding: 24 }}>
      <h2 className="serif" style={{ fontSize: 20, fontWeight: 500, margin: "0 0 4px" }}>Add a local guide?</h2>
      <p className="dim" style={{ fontSize: 13, margin: "0 0 18px" }}>Matched by language and specialisation. Optional.</p>

      {guides === null ? (
        <div className="dim" style={{ fontSize: 13 }}>Finding guides…</div>
      ) : guides.length === 0 ? (
        <div className="dim" style={{ fontSize: 13, marginBottom: 16 }}>No guides matched for this destination and language yet.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 18 }}>
          {guides.map((g) => (
            <div key={g.guide_id} style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "12px 14px", border: "1px solid var(--line)", borderRadius: "var(--radius)",
            }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{g.display_name}</div>
                <div className="dim" style={{ fontSize: 12 }}>
                  {g.specialisation} · ★{g.rating} ({g.review_count}) · speaks {g.languages}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div className="serif num" style={{ fontSize: 15 }}>{money(g.day_rate)}<span className="dim" style={{ fontSize: 11 }}>/day</span></div>
                <button
                  className="btn-outline"
                  style={{ marginTop: 6, padding: "6px 12px", fontSize: 12 }}
                  disabled={loading}
                  onClick={() => onBooked(g.guide_id, days)}
                >
                  Book {days}d
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12.5, marginBottom: 16 }}>
        <span className="dim">Days:</span>
        <input type="number" min={1} max={14} value={days} onChange={(e) => setDays(Number(e.target.value))} style={{ width: 64 }} />
      </label>

      <button className="btn-ghost" onClick={onSkip} disabled={loading}>Skip guide, continue →</button>
    </div>
  );
}
