import { money } from "../api.js";

export default function HotelPicker({ options, onSelect, loading }) {
  return (
    <div className="panel" style={{ padding: 24 }}>
      <h2 className="serif" style={{ fontSize: 20, fontWeight: 500, margin: "0 0 4px" }}>Choose a hotel</h2>
      <p className="dim" style={{ fontSize: 13, margin: "0 0 18px" }}>Total for your whole stay.</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {options.map((h) => (
          <button
            key={h.name}
            onClick={() => onSelect(h.name)}
            disabled={loading}
            style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "14px 16px", border: "1px solid var(--line)", borderRadius: "var(--radius)",
              background: "var(--paper)", textAlign: "left", width: "100%",
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>{h.name}</div>
              <div className="dim" style={{ fontSize: 12.5 }}>★ {h.rating} · {h.nights} night(s) · {money(h.nightly_rate_inr)}/night</div>
            </div>
            <div className="serif num" style={{ fontSize: 17 }}>{money(h.total_price_inr)}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
