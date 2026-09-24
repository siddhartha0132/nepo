const BASE = "/api";

async function req(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

// Maps KogniVera SessionResponse to newnew's expected trip state
function adaptSessionToTrip(session, extra = {}) {
  if (!session) return null;

  // Determine what UI step we're on based on what's selected
  let status = "select_flight";
  if (session.budget && session.budget.decision !== "approved") {
    status = "negotiate";
  } else if (session.confirmed) {
    status = "confirmed";
  } else if (!session.selected_flight && session.flight_options?.length > 0 && !session.flight_skipped) {
    status = "select_flight";
  } else if (!session.selected_hotel && session.hotel_options?.length > 0 && !session.hotel_skipped) {
    status = "select_hotel";
  } else if (!session.selected_package_id && session.suggested_plan) {
    status = "select_package";
  } else if (!session.selected_guide_id && !session.guide_skipped) {
    status = "select_guide";
  } else {
    status = "review";
  }

  // Handle if they hit "Next" on package customization
  if (session.package_done && status === "select_package") {
      status = "select_guide";
  }

  return {
    trip_id: session.session_id,
    status: status,
    negotiation_options: session.budget?.structured_negotiation_options || [],
    flight_options: session.flight_options || [],
    hotel_options: session.hotel_options || [],
    package_components: extra.itinerary ? extra.itinerary.components : [],
    running_total: session.budget?.total || session.suggested_plan?.total_cost || 0,
    budget_cap: session.budget?.cap || session.request?.budget?.amount || 0,
    chosen_flight: session.selected_flight,
    chosen_hotel: session.selected_hotel,
    chosen_guide: session.selected_guide_id ? {
      display_name: "Local Guide", // Ideally from API
      days_booked: 1,
      total_cost: session.budget?.total, // Simplified
    } : null,
    trace: session.trace || [],
    ...extra
  };
}


export const api = {
  realityCheck: ({ destination, duration_days, budget_cap, currency = "INR" }) =>
    req(`/reality-check`, { 
        method: "POST", 
        body: JSON.stringify({ 
            destination, duration_days, 
            budget: { amount: String(budget_cap), currency }, 
            language: "en-IN" 
        }) 
    }),

  createTrip: async (payload) => {
    const session = await req("/planner/recommend", { 
        method: "POST", 
        body: JSON.stringify({
            city_id: payload.destination, // assuming destination ID is given or fallback
            start_date: payload.depart_date,
            end_date: payload.return_date,
            travelers: 1, 
            budget: { amount: String(payload.budget_cap), currency: payload.currency },
            preferred_languages: ["en-IN"]
        }) 
    });
    await req(`/sessions/${session.session_id}/suggest-plan`, { method: "POST" });
    const fullSession = await req(`/sessions/${session.session_id}`);
    
    // Auto select the suggested package so the user goes straight to flight selection
    if (fullSession.suggested_plan && fullSession.suggested_plan.package) {
        await req(`/sessions/${fullSession.session_id}/select-package?package_id=${fullSession.suggested_plan.package.package_id}`, { method: "POST" });
    }
    
    const finalSession = await req(`/sessions/${session.session_id}`);
    return adaptSessionToTrip(finalSession);
  },
  
  getTrip: async (id) => {
      const session = await req(`/sessions/${id}`);
      let itinerary = null;
      if (session.selected_package_id) {
          try { itinerary = await req(`/sessions/${id}/itinerary`); } catch (e) {}
      }
      return adaptSessionToTrip(session, { itinerary });
  },

  selectFlight: async (id, flight_no) => {
      const session = await req(`/sessions/${id}`);
      const flight = session.flight_options?.find(f => f.flight_no === flight_no) || null;
      if (!flight) {
          session.flight_skipped = true;
          return adaptSessionToTrip(session);
      }
      const updated = await req(`/sessions/${id}/select-flight`, { method: "POST", body: JSON.stringify(flight) });
      return adaptSessionToTrip(updated);
  },
  
  selectHotel: async (id, name) => {
      const session = await req(`/sessions/${id}`);
      const hotel = session.hotel_options?.find(h => h.name === name) || null;
      if (!hotel) {
          session.hotel_skipped = true;
          return adaptSessionToTrip(session);
      }
      const updated = await req(`/sessions/${id}/select-hotel`, { method: "POST", body: JSON.stringify(hotel) });
      return adaptSessionToTrip(updated);
  },

  getAlternatives: (id, componentId) => [], 
  
  swapComponent: async (id, from_component_id, to_component_id) => {
      const updated = await req(`/sessions/${id}/swap-component`, { 
          method: "POST", 
          body: JSON.stringify({ component_id: from_component_id, replacement_component_id: to_component_id }) 
      });
      const itinerary = await req(`/sessions/${id}/itinerary`);
      return adaptSessionToTrip(updated, { itinerary });
  },
  
  continueFromPackage: async (id) => {
      const session = await req(`/sessions/${id}`);
      session.package_done = true; 
      const itinerary = await req(`/sessions/${id}/itinerary`);
      return adaptSessionToTrip(session, { itinerary });
  },

  listGuides: (id) => req(`/sessions/${id}/guides`).then(res => res.guides),
  
  selectGuide: async (id, guide_id, days = 1) => {
      const updated = await req(`/sessions/${id}/select-guide`, { method: "POST", body: JSON.stringify({ guide_id, service: "full_day" }) });
      return adaptSessionToTrip(updated);
  },
  
  skipGuide: async (id) => {
      const session = await req(`/sessions/${id}`);
      session.guide_skipped = true;
      return adaptSessionToTrip(session);
  },

  negotiate: async (id, choice, new_cap) => {
      let extra = {};
      if (choice === "raise_cap" && new_cap) extra.new_budget = { amount: String(new_cap), currency: "INR" };
      const updated = await req(`/sessions/${id}/negotiate`, { method: "POST", body: JSON.stringify({ option: choice, ...extra }) });
      return adaptSessionToTrip(updated);
  },

  confirm: async (id) => {
      const updated = await req(`/sessions/${id}/confirm`, { method: "POST", body: "{}" });
      return adaptSessionToTrip(updated);
  },
};

export function money(n) {
  const v = Math.round(Number(n) || 0);
  return `₹${v.toLocaleString("en-IN")}`;
}
