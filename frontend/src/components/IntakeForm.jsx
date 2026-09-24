import { useState } from "react";
import { useT } from "../i18n.jsx";

const DESTS = ["GOI", "JAI", "UDR", "AGR", "VNS", "SXR", "LKO", "BLR"];

export default function IntakeForm({ onSubmit, loading, error }) {
  const { t, lang, setLang } = useT();
  const [form, setForm] = useState({
    origin: "DEL",
    destination: "GOI",
    depart_date: "2026-12-05",
    return_date: "2026-12-09",
    travelers: 1,
    budget_cap: 20000,
    currency: "INR",
    language: lang,
  });

  function set(k, v) { setForm((f) => ({ ...f, [k]: v })); }

  function setFormLanguage(l) {
    set("language", l);
    setLang(l); // the traveler's chosen language drives both the UI and guide matching
  }

  return (
    <div className="panel" style={{ padding: 28 }}>
      <h1 className="serif" style={{ fontSize: 26, fontWeight: 500, margin: "0 0 6px" }}>
        {t("intake.title")}
      </h1>
      <p className="dim" style={{ margin: "0 0 24px", fontSize: 14, maxWidth: 440 }}>
        {t("intake.subtitle")}
      </p>

      <form
        onSubmit={(e) => { e.preventDefault(); onSubmit(form); }}
        style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}
      >
        <Field label={t("intake.from")}>
          <input value={form.origin} onChange={(e) => set("origin", e.target.value.toUpperCase())} maxLength={3} required />
        </Field>
        <Field label={t("intake.to")}>
          <select value={form.destination} onChange={(e) => set("destination", e.target.value)}>
            {DESTS.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </Field>
        <Field label={t("intake.depart")}>
          <input type="date" value={form.depart_date} onChange={(e) => set("depart_date", e.target.value)} required />
        </Field>
        <Field label={t("intake.return")}>
          <input type="date" value={form.return_date} onChange={(e) => set("return_date", e.target.value)} required />
        </Field>
        <Field label={t("intake.travelers")}>
          <input type="number" min={1} value={form.travelers} onChange={(e) => set("travelers", Number(e.target.value))} required />
        </Field>
        <Field label={t("intake.language")}>
          <select value={form.language} onChange={(e) => setFormLanguage(e.target.value)}>
            <option value="en-IN">English</option>
            <option value="hi">हिन्दी</option>
            <option value="ta">தமிழ்</option>
            <option value="te">తెలుగు</option>
          </select>
        </Field>
        <div style={{ gridColumn: "1 / -1" }}>
          <Field label={t("intake.budget")}>
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
            {loading ? t("intake.checking") : t("intake.submit")}
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
