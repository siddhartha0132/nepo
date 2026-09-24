import { useState } from "react";

const DESTS = ["GOI", "JAI", "UDR", "AGR", "VNS", "SXR", "LKO", "BLR"];

export default function IntakeForm({ onSubmit, loading, error }) {
  const [form, setForm] = useState({
    origin: "DEL",
    destination: "GOI",
    depart_date: "2026-12-05",
    return_date: "2026-12-09",
    travelers: 1,
    budget_cap: 20000,
    currency: "INR",
    language: "en-IN",
  });

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); }

  return (
    <div className="panel" style={{ padding: 28 }}>
      <h1 className="serif" style={{ fontSize: 26, fontWeight: 500, margin: "0 0 6px" }}>
        Where to, and what can you spend?
      </h1>
      <p className="dim" style={{ margin: "0 0 24px", fontSize: 14, maxWidth: 440 }}>
        Set your budget once. Before anything is searched, you'll see whether
        it's realistic for this trip — not just whether it's technically possible.
      </p>

      <form
        onSubmit={(e) => { e.preventDefault(); onSubmit(form); }}
        style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}
      >
        <Field label="From">
          <input value={form.origin} onChange={(e) => set("origin", e.target.value.toUpperCase())} maxLength={3} required />
        </Field>
        <Field label="To">
          <select value={form.destination} onChange={(e) => set("destination", e.target.value)}>
            {DESTS.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </Field>
        <Field label="Depart">
          <input type="date" value={form.depart_date} onChange={(e) => set("depart_date", e.target.value)} required />
        </Field>
        <Field label="Return">
          <input type="date" value={form.return_date} onChange={(e) => set("return_date", e.target.value)} required />
        </Field>
        <Field label="Travelers">
          <input type="number" min={1} value={form.travelers} onChange={(e) => set("travelers", Number(e.target.value))} required />
        </Field>
        <Field label="Language">
          <select value={form.language} onChange={(e) => set("language", e.target.value)}>
            <option value="en-IN">English</option>
            <option value="hi">हिन्दी</option>
            <option value="ta">தமிழ்</option>
            <option value="te">తెలుగు</option>
          </select>
        </Field>
        <div style={{ gridColumn: "1 / -1" }}>
          <Field label="Budget cap (₹, total for the trip)">
            <input
              type="number" min={1000} step={500}
              value={form.budget_cap}
              onChange={(e) => set("budget_cap", Number(e.target.value))}
              required style={{ width: "100%" }}
            />
          </Field>
        </div>

        {error && (
          <div style={{ gridColumn: "1 / -1", fontSize: 13, color: "var(--brick)", background: "var(--brick-soft)", padding: "10px 12px", borderRadius: "var(--radius)" }}>
            {error}
          </div>
        )}

        <div style={{ gridColumn: "1 / -1", marginTop: 4 }}>
          <button className="btn" type="submit" disabled={loading} style={{ width: "100%" }}>
            {loading ? "Checking…" : "Check my budget →"}
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12.5 }}>
      <span className="dim">{label}</span>
      {children}
    </label>
  );
}
