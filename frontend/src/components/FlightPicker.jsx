import { money } from "../api.js";
import { useT } from "../i18n.jsx";

export default function FlightPicker({ options, onSelect, loading }) {
  const { t } = useT();
  return (
    <div className="panel" style={{ padding: 24 }}>
      <h2 className="serif" style={{ fontSize: 20, fontWeight: 500, margin: "0 0 4px" }}>{t("flight.title")}</h2>
      <p className="dim" style={{ fontSize: 13, margin: "0 0 18px" }}>{t("flight.subtitle")}</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {options.map((f) => (
          <button
            key={f.flight_no}
            onClick={() => onSelect(f.flight_no)}
            disabled={loading}
            style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "14px 16px", border: "1px solid var(--line)", borderRadius: "var(--radius)",
              background: "var(--paper)", textAlign: "left", width: "100%",
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>{f.airline} · {f.flight_no}</div>
              <div className="dim" style={{ fontSize: 12.5 }}>{f.origin} → {f.destination} · {f.depart_time} · {f.duration_min}m</div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div className="serif num" style={{ fontSize: 17 }}>{money(f.price_inr)}</div>
              <div className="dim" style={{ fontSize: 11 }}>{t("flight.confidence", { pct: Math.round(f.confidence * 100) })}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
