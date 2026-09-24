import { useEffect, useState } from "react";
import { api, money } from "../api.js";
import { useT } from "../i18n.jsx";

const SPECS = ["food", "heritage", "photography", "religious", "shopping", "trekking", "wildlife", "accessibility"];

export default function GuidePicker({ tripId, travelerLanguage, onBooked, onSkip, loading }) {
  const { t } = useT();
  const [guides, setGuides] = useState(null);
  const [days, setDays] = useState(1);
  const [spec, setSpec] = useState("");

  useEffect(() => {
    setGuides(null);
    api.listGuides(tripId, spec || undefined).then(setGuides);
  }, [tripId, spec]);

  const speaksTravelerLang = (g) =>
    travelerLanguage && (g.languages || "").toLowerCase().split(",").map((s) => s.trim()).includes(travelerLanguage.toLowerCase());

  const sorted = guides
    ? [...guides].sort((a, b) => {
        const am = speaksTravelerLang(a) ? 1 : 0, bm = speaksTravelerLang(b) ? 1 : 0;
        if (am !== bm) return bm - am; // language matches float to top
        return b.rating - a.rating;
      })
    : null;
  const topRatedId = sorted?.length ? [...sorted].sort((a, b) => b.rating - a.rating)[0].guide_id : null;

  return (
    <div className="panel" style={{ padding: 24 }}>
      <h2 className="serif" style={{ fontSize: 20, fontWeight: 500, margin: "0 0 4px" }}>{t("guide.title")}</h2>
      <p className="dim" style={{ fontSize: 13, margin: "0 0 14px" }}>{t("guide.subtitle")}</p>

      <select value={spec} onChange={(e) => setSpec(e.target.value)} style={{ marginBottom: 16, fontSize: 12.5 }}>
        <option value="">{t("guide.filter_all")}</option>
        {SPECS.map((s) => <option key={s} value={s}>{t(`guide.spec.${s}`)}</option>)}
      </select>

      {sorted === null ? (
        <div className="dim" style={{ fontSize: 13 }}>{t("guide.finding")}</div>
      ) : sorted.length === 0 ? (
        <div className="dim" style={{ fontSize: 13, marginBottom: 16 }}>{t("guide.none")}</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 18 }}>
          {sorted.map((g) => {
            const langMatch = speaksTravelerLang(g);
            return (
              <div key={g.guide_id} style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "12px 14px", border: `1px solid ${langMatch ? "var(--teal)" : "var(--line)"}`, borderRadius: "var(--radius)",
              }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 600, fontSize: 14 }}>
                    {g.display_name}
                    {langMatch && (
                      <span style={{ fontSize: 10, fontWeight: 600, color: "var(--teal)", background: "var(--teal-soft)", padding: "2px 7px", borderRadius: 10 }}>
                        {t("guide.lang_match")}
                      </span>
                    )}
                    {g.guide_id === topRatedId && (
                      <span style={{ fontSize: 10, fontWeight: 600, color: "var(--brass)", background: "#F6EDD9", padding: "2px 7px", borderRadius: 10 }}>
                        {t("guide.top_rated")}
                      </span>
                    )}
                  </div>
                  <div className="dim" style={{ fontSize: 12 }}>
                    {t(`guide.spec.${g.specialisation}`)} · ★{g.rating} ({g.review_count}) · {t("guide.speaks")} {g.languages}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div className="serif num" style={{ fontSize: 15 }}>{money(g.day_rate)}<span className="dim" style={{ fontSize: 11 }}>{t("guide.per_day")}</span></div>
                  <button
                    className="btn-outline"
                    style={{ marginTop: 6, padding: "6px 12px", fontSize: 12 }}
                    disabled={loading}
                    onClick={() => onBooked(g.guide_id, days)}
                  >
                    {t("guide.book", { n: days })}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12.5, marginBottom: 16 }}>
        <span className="dim">{t("guide.days_label")}</span>
        <input type="number" min={1} max={14} value={days} onChange={(e) => setDays(Number(e.target.value))} style={{ width: 64 }} />
      </label>

      <button className="btn-ghost" onClick={onSkip} disabled={loading}>{t("guide.skip")}</button>
    </div>
  );
}
