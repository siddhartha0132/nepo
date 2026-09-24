import { useState } from "react";

export default function NegotiationPanel({ options, onChoose, loading }) {
  const [newCap, setNewCap] = useState("");
  const needsCap = (choice) => choice === "raise_cap";

  return (
    <div className="panel" style={{ padding: 24, borderColor: "var(--brick)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <span style={{ color: "var(--brick)", fontSize: 16 }}>!</span>
        <h2 className="serif" style={{ fontSize: 18, fontWeight: 600, margin: 0, color: "var(--brick)" }}>
          This would go over budget
        </h2>
      </div>
      <p className="dim" style={{ fontSize: 13, margin: "0 0 18px" }}>
        Nothing has been added. Pick how you'd like to handle it.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {options.map((o) => (
          <div key={o.choice}>
            <button
              className="btn-outline"
              disabled={loading}
              style={{ width: "100%", textAlign: "left" }}
              onClick={() => !needsCap(o.choice) && onChoose(o.choice)}
            >
              {o.label}
            </button>
            {needsCap(o.choice) && (
              <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
                <input
                  type="number" placeholder="New total budget (₹)"
                  value={newCap} onChange={(e) => setNewCap(e.target.value)}
                  style={{ flex: 1 }}
                />
                <button
                  className="btn"
                  disabled={loading || !newCap}
                  onClick={() => onChoose("raise_cap", Number(newCap))}
                >
                  Set
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
