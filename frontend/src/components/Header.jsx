const STEPS = [
  { key: "intake", label: "Trip" },
  { key: "reality", label: "Reality check" },
  { key: "select_flight", label: "Flight" },
  { key: "select_hotel", label: "Hotel" },
  { key: "select_package", label: "Package" },
  { key: "select_guide", label: "Guide" },
  { key: "review", label: "Confirm" },
];

export default function Header({ current }) {
  const idx = STEPS.findIndex((s) => s.key === (current === "confirmed" ? "review" : current));

  return (
    <header style={{ padding: "28px 24px 20px", maxWidth: 720, margin: "0 auto" }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 22 }}>
        <span className="serif" style={{ fontSize: 22, fontWeight: 600, letterSpacing: "-0.01em" }}>
          Waypoint
        </span>
        <span className="dim" style={{ fontSize: 13 }}>budget-honest trip planning</span>
      </div>

      {idx >= 0 && (
        <div style={{ display: "flex", alignItems: "center" }}>
          {STEPS.map((s, i) => (
            <div key={s.key} style={{ display: "flex", alignItems: "center", flex: i < STEPS.length - 1 ? 1 : "0 0 auto" }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
                <div
                  aria-hidden="true"
                  style={{
                    width: 9, height: 9, borderRadius: "50%",
                    background: i < idx ? "var(--teal)" : i === idx ? "var(--brass)" : "transparent",
                    border: `1.5px solid ${i <= idx ? "transparent" : "var(--line)"}`,
                  }}
                />
                <span
                  className="dim"
                  style={{
                    fontSize: 10.5, whiteSpace: "nowrap",
                    color: i === idx ? "var(--ink)" : undefined,
                    fontWeight: i === idx ? 600 : 400,
                  }}
                >
                  {s.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div style={{ flex: 1, height: 1, background: i < idx ? "var(--teal)" : "var(--line)", margin: "0 6px 16px" }} />
              )}
            </div>
          ))}
        </div>
      )}
    </header>
  );
}

export { STEPS };
