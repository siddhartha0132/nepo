import { useEffect, useState } from "react";
import { api, money } from "../api.js";
import { useT } from "../i18n.jsx";

export default function PackagePanel({ tripId, components, onSwapped, onNext, loading }) {
  const { t } = useT();
  const [openFor, setOpenFor] = useState(null);
  const [alts, setAlts] = useState([]);
  const [altsLoading, setAltsLoading] = useState(false);

  useEffect(() => {
    if (!openFor) return;
    setAltsLoading(true);
    api.getAlternatives(tripId, openFor).then(setAlts).finally(() => setAltsLoading(false));
  }, [openFor, tripId]);

  const byDay = components.reduce((acc, c) => {
    const day = c.day_index ?? 0;
    (acc[day] ||= []).push(c);
    return acc;
  }, {});

  return (
    <div className="panel" style={{ padding: 24 }}>
      <h2 className="serif" style={{ fontSize: 20, fontWeight: 500, margin: "0 0 4px" }}>{t("pkg.title")}</h2>
      <p className="dim" style={{ fontSize: 13, margin: "0 0 18px" }}>{t("pkg.subtitle")}</p>

      {Object.entries(byDay).sort(([a], [b]) => a - b).map(([day, comps]) => (
        <div key={day} style={{ marginBottom: 16 }}>
          <div className="dim" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8 }}>{t("pkg.day", { n: day })}</div>
          {comps.map((c) => (
            <div key={c.component_id} style={{ marginBottom: 8 }}>
              <div style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "10px 12px", border: "1px solid var(--line)", borderRadius: "var(--radius)",
              }}>
                <div>
                  <div style={{ fontSize: 13.5, fontWeight: 600 }}>{c.title}</div>
                  <div className="dim" style={{ fontSize: 11.5 }}>{c.component_type} · {c.slot}</div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span className="num" style={{ fontSize: 13 }}>{money(c.price_delta)}</span>
                  {c.is_swappable === 1 || c.is_swappable === true ? (
                    <button
                      className="btn-ghost"
                      style={{ fontSize: 11.5 }}
                      onClick={() => setOpenFor(openFor === c.component_id ? null : c.component_id)}
                    >
                      {t("pkg.swap")}
                    </button>
                  ) : null}
                </div>
              </div>

              {openFor === c.component_id && (
                <div style={{ padding: "8px 12px", background: "var(--paper-raised)", borderRadius: "var(--radius)", marginTop: 4 }}>
                  {altsLoading ? (
                    <div className="dim" style={{ fontSize: 12 }}>{t("pkg.loading_alts")}</div>
                  ) : alts.length === 0 ? (
                    <div className="dim" style={{ fontSize: 12 }}>{t("pkg.no_alts")}</div>
                  ) : (
                    alts.map((a) => (
                      <button
                        key={a.component_id}
                        disabled={loading}
                        onClick={async () => { await onSwapped(c.component_id, a.component_id); setOpenFor(null); }}
                        style={{
                          display: "flex", justifyContent: "space-between", width: "100%",
                          padding: "8px 4px", border: "none", background: "none", textAlign: "left", fontSize: 12.5,
                        }}
                      >
                        <span>{a.title}</span>
                        <span className="num">{money(a.price_delta)}</span>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      ))}

      <button className="btn" onClick={onNext} disabled={loading} style={{ width: "100%", marginTop: 8 }}>
        {t("pkg.continue")}
      </button>
    </div>
  );
}
