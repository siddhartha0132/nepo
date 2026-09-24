import { money } from "../api.js";
import { useT } from "../i18n.jsx";

export default function Ledger({ trip }) {
  const { t } = useT();
  if (!trip) return null;
  const pct = Math.min(100, (trip.running_total / trip.budget_cap) * 100);
  const color = pct > 100 ? "var(--brick)" : pct > 90 ? "var(--brass)" : "var(--teal)";

  return (
    <div style={{
      position: "sticky", bottom: 0, background: "var(--paper)",
      borderTop: "1px solid var(--line)", padding: "14px 24px",
      maxWidth: 720, margin: "0 auto",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
        <span className="dim" style={{ fontSize: 12 }}>{t("ledger.running_total")}</span>
        <span className="serif num" style={{ fontSize: 16 }}>
          {money(trip.running_total)} <span className="dim" style={{ fontSize: 12, fontFamily: "var(--font-body)" }}>/ {money(trip.budget_cap)} {t("ledger.cap")}</span>
        </span>
      </div>
      <div style={{ height: 5, background: "var(--paper-raised)", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, transition: "width 200ms ease" }} />
      </div>
    </div>
  );
}
