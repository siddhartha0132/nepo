import { money } from "../api.js";

export default function ReviewConfirm({ trip, onConfirm, loading, confirmed }) {
  return (
    <div className="panel" style={{ padding: 24 }}>
      {confirmed ? (
        <>
          <div style={{ color: "var(--forest)", fontSize: 14, fontWeight: 600, marginBottom: 6 }}>✓ Confirmed</div>
          <h2 className="serif" style={{ fontSize: 22, margin: "0 0 4px" }}>Trip locked in</h2>
          <p className="dim" style={{ fontSize: 13 }}>
            Final total {money(trip.running_total)} of your {money(trip.budget_cap)} cap — never crossed.
          </p>
        </>
      ) : (
        <>
          <h2 className="serif" style={{ fontSize: 20, fontWeight: 500, margin: "0 0 4px" }}>Review & confirm</h2>
          <p className="dim" style={{ fontSize: 13, margin: "0 0 18px" }}>Nothing is booked until you confirm.</p>

          <Row label="Flight" value={trip.chosen_flight ? `${trip.chosen_flight.airline} ${trip.chosen_flight.flight_no}` : "—"} amount={trip.chosen_flight?.price_inr} />
          <Row label="Hotel" value={trip.chosen_hotel?.name || "—"} amount={trip.chosen_hotel?.total_price_inr} />
          <Row label="Guide" value={trip.chosen_guide ? `${trip.chosen_guide.display_name} (${trip.chosen_guide.days_booked}d)` : "Not booked"} amount={trip.chosen_guide?.total_cost} />

          <div className="perforated" />
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 15, marginBottom: 20 }}>
            <span className="serif" style={{ fontWeight: 600 }}>Total</span>
            <span className="serif num" style={{ fontWeight: 600 }}>{money(trip.running_total)}</span>
          </div>

          <button className="btn" onClick={onConfirm} disabled={loading} style={{ width: "100%" }}>
            {loading ? "Confirming…" : "Confirm trip →"}
          </button>
        </>
      )}
    </div>
  );
}

function Row({ label, value, amount }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, padding: "8px 0" }}>
      <div>
        <div className="dim" style={{ fontSize: 11 }}>{label}</div>
        <div>{value}</div>
      </div>
      {amount != null && <span className="num">{money(amount)}</span>}
    </div>
  );
}
