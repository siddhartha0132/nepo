import { useState } from "react";
import { money } from "../api.js";
import { useT } from "../i18n.jsx";

export default function NegotiationPanel({ options, onChoose, loading }) {
  const { t } = useT();
  const [newCap, setNewCap] = useState("");

  function labelFor(o) {
    switch (o.choice) {
      case "approve_overage": return t("negotiate.approve_overage", { amt: money(o.amount), item: o.item_label });
      case "swap_cheaper": return t("negotiate.swap_cheaper", { item: o.item_label });
      case "remove_item": return t("negotiate.remove_item", { item: o.item_label });
      case "raise_cap": return t("negotiate.raise_cap");
      default: return o.label;
    }
  }

  return (
    <div className="panel" style={{ padding: 24, borderColor: "var(--brick)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <span style={{ color: "var(--brick)", fontSize: 16 }}>!</span>
        <h2 className="serif" style={{ fontSize: 18, fontWeight: 600, margin: 0, color: "var(--brick)" }}>
          {t("negotiate.title")}
        </h2>
      </div>
      <p className="dim" style={{ fontSize: 13, margin: "0 0 18px" }}>{t("negotiate.subtitle")}</p>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {options.map((o) => (
          <div key={o.choice}>
            <button
              className="btn-outline"
              disabled={loading}
              style={{ width: "100%", textAlign: "left" }}
              onClick={() => o.choice !== "raise_cap" && onChoose(o.choice)}
            >
              {labelFor(o)}
            </button>
            {o.choice === "raise_cap" && (
              <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
                <input
                  type="number" placeholder={t("negotiate.new_cap_placeholder")}
                  value={newCap} onChange={(e) => setNewCap(e.target.value)}
                  style={{ flex: 1 }}
                />
                <button
                  className="btn"
                  disabled={loading || !newCap}
                  onClick={() => onChoose("raise_cap", Number(newCap))}
                >
                  {t("negotiate.set")}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
