import { useState } from "react";
import { api } from "./api.js";
import { useT } from "./i18n.jsx";
import Header from "./components/Header.jsx";
import IntakeForm from "./components/IntakeForm.jsx";
import RealityCheck from "./components/RealityCheck.jsx";
import FlightPicker from "./components/FlightPicker.jsx";
import HotelPicker from "./components/HotelPicker.jsx";
import PackagePanel from "./components/PackagePanel.jsx";
import GuidePicker from "./components/GuidePicker.jsx";
import NegotiationPanel from "./components/NegotiationPanel.jsx";
import ReviewConfirm from "./components/ReviewConfirm.jsx";
import Ledger from "./components/Ledger.jsx";
import TraceLog from "./components/TraceLog.jsx";

// Screens shown before a trip exists vs. once it's live
const SCREEN = { INTAKE: "intake", REALITY: "reality", TRIP: "trip" };

export default function App() {
  const { t } = useT();
  const [screen, setScreen] = useState(SCREEN.INTAKE);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pendingForm, setPendingForm] = useState(null);
  const [realityResult, setRealityResult] = useState(null);
  const [trip, setTrip] = useState(null);

  async function handleIntake(form) {
    setLoading(true); setError(null); setPendingForm(form);
    try {
      const duration = daysBetween(form.depart_date, form.return_date);
      const result = await api.realityCheck({
        destination: form.destination, duration_days: duration,
        budget_cap: form.budget_cap, currency: form.currency,
      });
      setRealityResult(result);
      setScreen(SCREEN.REALITY);
    } catch (e) {
      // Reality check is a bonus — don't block the trip if it fails
      await startTrip(form);
    } finally {
      setLoading(false);
    }
  }

  async function startTrip(form) {
    setLoading(true); setError(null);
    try {
      const t = await api.createTrip(form);
      setTrip(t);
      setScreen(SCREEN.TRIP);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function refresh(action) {
    setLoading(true); setError(null);
    try {
      const t = await action();
      setTrip(t);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setScreen(SCREEN.INTAKE); setTrip(null); setRealityResult(null);
    setPendingForm(null); setError(null);
  }

  return (
    <div style={{ minHeight: "100%", display: "flex", flexDirection: "column" }}>
      <Header current={screen === SCREEN.TRIP ? trip?.status : screen} />

      <main style={{ flex: 1, maxWidth: 720, width: "100%", margin: "0 auto", padding: "0 24px 24px" }}>
        {error && (
          <div style={{ marginBottom: 16, fontSize: 13, color: "var(--brick)", background: "var(--brick-soft)", padding: "10px 12px", borderRadius: "var(--radius)" }}>
            {error}
          </div>
        )}

        {screen === SCREEN.INTAKE && (
          <IntakeForm onSubmit={handleIntake} loading={loading} error={null} />
        )}

        {screen === SCREEN.REALITY && (
          <RealityCheck
            result={realityResult}
            loading={loading}
            onAdjust={() => setScreen(SCREEN.INTAKE)}
            onProceed={() => startTrip(pendingForm)}
          />
        )}

        {screen === SCREEN.TRIP && trip && (
          <>
            {trip.status === "negotiate" && (
              <NegotiationPanel
                options={trip.negotiation_options}
                loading={loading}
                onChoose={(choice, new_cap) => refresh(() => api.negotiate(trip.trip_id, choice, new_cap))}
              />
            )}

            {trip.status === "select_flight" && (
              <FlightPicker options={trip.flight_options} loading={loading}
                onSelect={(no) => refresh(() => api.selectFlight(trip.trip_id, no))} />
            )}

            {trip.status === "select_hotel" && (
              <HotelPicker options={trip.hotel_options} loading={loading}
                onSelect={(name) => refresh(() => api.selectHotel(trip.trip_id, name))} />
            )}

            {trip.status === "select_package" && (
              <PackagePanel
                tripId={trip.trip_id} components={trip.package_components} loading={loading}
                onSwapped={(from, to) => refresh(() => api.swapComponent(trip.trip_id, from, to))}
                onNext={() => refresh(() => api.continueFromPackage(trip.trip_id))}
              />
            )}

            {trip.status === "select_guide" && (
              <GuidePicker
                tripId={trip.trip_id} loading={loading} travelerLanguage={trip.language}
                onBooked={(id, days) => refresh(() => api.selectGuide(trip.trip_id, id, days))}
                onSkip={() => refresh(() => api.skipGuide(trip.trip_id))}
              />
            )}

            {(trip.status === "review" || trip.status === "confirmed") && (
              <ReviewConfirm
                trip={trip} loading={loading} confirmed={trip.status === "confirmed"}
                onConfirm={() => refresh(() => api.confirm(trip.trip_id))}
              />
            )}
          </>
        )}
      </main>

      {trip && <Ledger trip={trip} />}
      {trip && <TraceLog trace={trip.trace} />}

      {trip?.status === "confirmed" && (
        <div style={{ maxWidth: 720, margin: "0 auto 40px", padding: "0 24px" }}>
          <button className="btn-ghost" onClick={reset}>{t("app.plan_another")}</button>
        </div>
      )}
    </div>
  );
}

function daysBetween(a, b) {
  const ms = new Date(b) - new Date(a);
  const d = Math.round(ms / 86400000);
  return d > 0 ? d : 3;
}
