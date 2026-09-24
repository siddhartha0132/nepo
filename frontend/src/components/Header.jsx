import { useT } from "../i18n.jsx";

const STEP_KEYS = [
  "intake", "reality", "select_flight", "select_hotel", "select_package", "select_guide", "review",
];

const LANG_NAMES = { "en-IN": "English", hi: "हिन्दी", ta: "தமிழ்", te: "తెలుగు" };

export default function Header({ current }) {
  const { t, lang, setLang, LANGS } = useT();
  const idx = STEP_KEYS.findIndex((s) => s === (current === "confirmed" ? "review" : current));

  return (
    <header style={{ padding: "28px 24px 20px", maxWidth: 720, margin: "0 auto" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 22 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <span className="serif" style={{ fontSize: 22, fontWeight: 600, letterSpacing: "-0.01em" }}>
            {t("app.title")}
          </span>
          <span className="dim" style={{ fontSize: 13 }}>{t("app.tagline")}</span>
        </div>
        <select
          value={lang}
          onChange={(e) => setLang(e.target.value)}
          aria-label="Interface language"
          style={{ fontSize: 12.5, padding: "5px 8px", width: "auto" }}
        >
          {LANGS.map((l) => <option key={l} value={l}>{LANG_NAMES[l]}</option>)}
        </select>
      </div>

      {idx >= 0 && (
        <div style={{ display: "flex", alignItems: "center" }}>
          {STEP_KEYS.map((s, i) => (
            <div key={s} style={{ display: "flex", alignItems: "center", flex: i < STEP_KEYS.length - 1 ? 1 : "0 0 auto" }}>
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
                  {t(`step.${s}`)}
                </span>
              </div>
              {i < STEP_KEYS.length - 1 && (
                <div style={{ flex: 1, height: 1, background: i < idx ? "var(--teal)" : "var(--line)", margin: "0 6px 16px" }} />
              )}
            </div>
          ))}
        </div>
      )}
    </header>
  );
}
