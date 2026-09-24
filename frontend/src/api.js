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

export const api = {
  realityCheck: ({ destination, duration_days, budget_cap, currency = "INR" }) =>
    req(`/reality-check?${new URLSearchParams({ destination, duration_days, budget_cap, currency })}`),

  createTrip: (payload) => req("/trip", { method: "POST", body: JSON.stringify(payload) }),
  getTrip: (id) => req(`/trip/${id}`),

  selectFlight: (id, flight_no) => req(`/trip/${id}/flight`, { method: "POST", body: JSON.stringify({ flight_no }) }),
  selectHotel: (id, name) => req(`/trip/${id}/hotel`, { method: "POST", body: JSON.stringify({ name }) }),

  getAlternatives: (id, componentId) => req(`/trip/${id}/package/alternatives/${componentId}`),
  swapComponent: (id, from_component_id, to_component_id) =>
    req(`/trip/${id}/package/swap`, { method: "POST", body: JSON.stringify({ from_component_id, to_component_id }) }),
  continueFromPackage: (id) => req(`/trip/${id}/package/continue`, { method: "POST" }),

  listGuides: (id, specialisation) => req(`/trip/${id}/guides${specialisation ? `?specialisation=${encodeURIComponent(specialisation)}` : ""}`),
  selectGuide: (id, guide_id, days = 1) =>
    req(`/trip/${id}/guide`, { method: "POST", body: JSON.stringify({ guide_id, days }) }),
  skipGuide: (id) => req(`/trip/${id}/skip-guide`, { method: "POST" }),

  negotiate: (id, choice, new_cap) =>
    req(`/trip/${id}/negotiate`, { method: "POST", body: JSON.stringify({ choice, new_cap }) }),

  confirm: (id) => req(`/trip/${id}/confirm`, { method: "POST" }),
};

export function money(n) {
  const v = Math.round(Number(n) || 0);
  return `₹${v.toLocaleString("en-IN")}`;
}
