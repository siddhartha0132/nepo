import { money } from "../api.js";
import { useT } from "../i18n.jsx";

const VERDICT = {
  comfortable: { color: "var(--forest)", bg: "var(--forest-soft)" },
  tight: { color: "var(--brass)", bg: "#F6EDD9" },
  unrealistic: { color: "var(--brick)", bg: "var(--brick-soft)" },
};

export default function RealityCheck({ result, onProceed, onAdjust, loading }) {
  const { t } = useT();

  if (!result?.resolved) {
    return (
      <div className="panel" style={{ padding: 28 }}>
        <h2 className="serif" style={{ fontSize: 22, margin: "0 0 8px" }}>{t("reality.no_data_title")}</h2>
        <p className="dim" style={{ fontSize: 14, lineHeight: 1.6 }}>{t("reality.no_data_fallback")}</p>
        <button className="btn" onClick={onProceed} disabled={loading} style={{ marginTop: 16 }}>
          {loading ? t("reality.starting") : t("reality.plan_anyway")}
        </button>
      </div>
    );
  }

  const { city, budget_itinerary, market_itinerary, comparison } = result;
  const v = VERDICT[comparison?.verdict] || VERDICT.tight;

  return (
    <div className="panel" style={{ padding: 28 }}>
      <div className="dim" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 6 }}>
        {t("reality.label")} · {city.city_name}
      </div>
      <h2 className="serif" style={{ fontSize: 24, margin: "0 0 18px", fontWeight: 500 }}>
        {t("reality.question", { amt: money(budget_itinerary.budget_cap) })}
      </h2>

      {comparison && (
        <>
          <div role="status" aria-live="polite" style={{
            display: "flex", alignItems: "center", gap: 12, padding: "13px 16px",
            background: v.bg, borderRadius: "var(--radius)", marginBottom: 18,
          }}>
            <span className="serif" style={{ fontSize: 15, fontWeight: 600, color: v.color }}>
              {t(`reality.verdict.${comparison.verdict}`)}
            </span>
            <span style={{ fontSize: 13, color: v.color }}>
              — {comparison.gap_pct >= 0
                ? t("reality.gap_above", { pct: Math.abs(comparison.gap_pct) })
                : t("reality.gap_below", { pct: Math.abs(comparison.gap_pct) })}
            </span>
          </div>

          <div style={{ marginBottom: 20 }}>
            <div style={{ position: "relative", height: 6, background: "var(--paper-raised)", borderRadius: 4 }}>
              <div
                role="img"
                aria-label={money(budget_itinerary.budget_cap)}
                style={{
                  position: "absolute", left: `calc(${comparison.range_position * 100}% - 7px)`, top: -5,
                  width: 16, height: 16, borderRadius: "50%", background: v.color,
                  border: "2px solid var(--paper)", boxShadow: "0 0 0 1px var(--line)",
                }}
                title={money(budget_itinerary.budget_cap)}
              />
            </div>
            <div className="dim num" style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginTop: 8 }}>
              <span>{money(market_itinerary.benchmark_total_min)}</span>
              <span>{t("reality.typical_range")}</span>
              <span>{money(market_itinerary.benchmark_total_max)}</span>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 18 }}>
            <div style={{ borderTop: "2px solid var(--ink)", paddingTop: 10 }}>
              <div className="dim" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>{t("reality.your_budget")}</div>
              <div className="serif num" style={{ fontSize: 22 }}>{money(budget_itinerary.budget_cap)}</div>
              {budget_itinerary.feasible ? (
                <div style={{ fontSize: 12.5, marginTop: 6, lineHeight: 1.5 }}>
                  <div className="dim">{t("reality.closest_pkg")}</div>
                  <div style={{ fontWeight: 600 }}>{budget_itinerary.best_fit_package.name}</div>
                </div>
              ) : (
                <div className="dim" style={{ fontSize: 12.5, marginTop: 6 }}>{t("reality.no_fit")}</div>
              )}
            </div>
            <div style={{ borderTop: "2px solid var(--line)", paddingTop: 10 }}>
              <div className="dim" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>{t("reality.typical_trip")}</div>
              <div className="serif num" style={{ fontSize: 22 }}>{money(market_itinerary.benchmark_total)}</div>
              <div className="dim" style={{ fontSize: 12.5, marginTop: 6 }}>
                {t("reality.sample", { n: market_itinerary.sample_size, level: market_itinerary.fallback_level })}
              </div>
            </div>
          </div>

          {comparison.recommendations && Object.values(comparison.recommendations).some(Boolean) && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 20 }}>
              {comparison.recommendations.budget_needed_for_tight && (
                <Chip>{t("reality.rec_tight", { amt: money(comparison.recommendations.budget_needed_for_tight) })}</Chip>
              )}
              {comparison.recommendations.budget_needed_for_comfortable && (
                <Chip>{t("reality.rec_comfortable", { amt: money(comparison.recommendations.budget_needed_for_comfortable) })}</Chip>
              )}
              {comparison.recommendations.max_days_at_current_budget != null && (
                <Chip>{t("reality.rec_days", { n: comparison.recommendations.max_days_at_current_budget })}</Chip>
              )}
            </div>
          )}
        </>
      )}

      <div style={{ display: "flex", gap: 10 }}>
        <button className="btn-outline" onClick={onAdjust} disabled={loading}>{t("reality.adjust")}</button>
        <button className="btn" onClick={onProceed} disabled={loading} style={{ flex: 1 }}>
          {loading ? t("reality.starting") : t("reality.continue")}
        </button>
      </div>
    </div>
  );
}

function Chip({ children }) {
  return (
    <div className="num" style={{
      fontSize: 12, padding: "6px 12px", borderRadius: 20,
      border: "1px solid var(--line)", background: "var(--paper-raised)",
    }}>
      {children}
    </div>
  );
}
