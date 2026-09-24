# Waypoint — budget-honest trip planning

A from-scratch rebuild of the PS-04 "PackagePro — Dynamic Tour Packages"
concept, built around one bet: the thing missing from AI trip planners
isn't a better itinerary, it's proof that the AI won't quietly blow your
budget. Every number here traces back to the real PackagePro dataset
(`data/PS-04.db`) or a clearly-mocked search — nothing is invented.

## The core idea, in one screen

Before any search happens, you see **two itineraries**: what your stated
budget actually buys (a real package that fits), and what a trip like this
*typically* costs (a market-average benchmark computed from real package
prices for that city, falling back to state/country if the city's data is
thin). You get a verdict — comfortable / tight / unrealistic — and concrete
numbers to act on, not just a warning.

From there: pick a flight, pick a hotel, review a real package's day-by-day
components and swap anything swappable, optionally book a real local guide
(matched by language and specialisation — this exists in the data but was
never reachable from a screen in the original build; it is now), then
confirm. **Every one of those steps routes through one function
(`budget.check`)** — nothing is ever added if it would cross the cap, and a
failed check always returns four concrete moves (approve the overage, swap
cheaper, drop the item, raise the cap) instead of a dead end.

## What's different from the original KogniVera build

- New backend, new frontend, new design direction — nothing copy-pasted.
- Auth and payment-stub scope was deliberately dropped; this build spends
  its effort on the flow that's actually the pitch, done correctly, rather
  than replicating every screen shallowly.
- Guide selection is now wired all the way through — backend matching
  existed before but no screen ever called it.
- Money math is `Decimal` throughout, never `float`.
- The dataset's real column names are used directly (`display_name`,
  `title`, `price_delta`, `is_swappable`, etc.) — checked against the
  actual schema, not assumed.

## Running it

```bash
# backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9000

# frontend (separate terminal)
cd frontend
npm install
npm run dev   # http://localhost:5174, proxies /api -> :9000
```

## API surface

| Method | Path | Does |
|---|---|---|
| GET | `/reality-check` | Dual itinerary comparison, no trip needed |
| POST | `/trip` | Create a trip, search flights |
| POST | `/trip/{id}/flight` | Pick a flight (budget-checked) |
| POST | `/trip/{id}/hotel` | Pick a hotel (budget-checked), loads a real package |
| GET | `/trip/{id}/package/alternatives/{component_id}` | Swap options for one component |
| POST | `/trip/{id}/package/swap` | Swap a component (budget-checked) |
| GET | `/trip/{id}/guides` | Real guides matched by city + language |
| POST | `/trip/{id}/guide` / `/skip-guide` | Book or skip a guide (budget-checked) |
| POST | `/trip/{id}/negotiate` | Resolve a failed budget check |
| POST | `/trip/{id}/confirm` | Lock in the trip (blocked while a negotiation is pending) |

## Round 2 — necessary fixes before real API keys go in

Found by manual testing, then locked down with an actual test suite so it
can't come back silently:

- **Real bug fixed:** declining an over-budget item at the *flight* stage
  (the very first budget-checked step) used to resume the trip at
  `"review"` instead of back at `"select_flight"` — the old `negotiate()`
  endpoint guessed the resume point from which fields happened to be set
  on the trip, rather than tracking it. Same bug existed at the guide
  stage. Fixed by having every budget-checked action state its own
  `advance_to` status explicitly; `negotiate()` just reads that back
  instead of re-deriving it.
- **Guide step is now server-authoritative.** It used to be a
  frontend-only `setTrip()` override with no backing endpoint — a page
  refresh or an unrelated negotiation could lose track of it. There's now
  a real `POST /trip/{id}/package/continue` endpoint and the backend
  status machine includes `select_guide` as a first-class state.
- **Input validation that was missing:** same origin/destination, or a
  return date before the depart date, used to sail through silently.
  Both now return 422 with a clear message.
- **Provider abstraction for real API keys** (`app/config.py` +
  `app/search.py`): `search_flights()`/`search_hotels()` are dispatchers
  that check `USE_MOCK_FLIGHTS`/`USE_MOCK_HOTELS` and call either the mock
  generator or `real_amadeus_flights()`/`real_hotelbeds_hotels()` — both
  already documented with the exact return shape the rest of the app
  expects. Drop keys into `.env` (see `.env.example`), implement those two
  function bodies, flip the flags — nothing else in the codebase changes.
- **CORS origins** now come from `CORS_ORIGINS` in `.env` instead of a
  hardcoded `*`.
- **Test suite added** (`backend/tests/`, 16 tests, `pytest`): unit tests
  for the budget guard, integration tests for the full trip flow through
  the real FastAPI app — including a test that pins the exact bug above so
  it's caught automatically if it ever regresses.

## Round 3 — full multilingual UI + better guide selection

- **Full UI translation** (English, Hindi, Tamil, Telugu) — every screen,
  including the negotiation panel. A language switcher lives in the header
  and the language picked in the intake form drives both the UI and guide
  matching from that point on. (`frontend/src/i18n.jsx`)
- **Negotiation labels are now fully localizable, not English strings
  baked into the API response.** `budget.negotiation_options()` used to
  return a pre-built English sentence like `"Approve the extra ₹1,200 for
  the IndiGo flight"`. That can't be translated on the frontend without
  re-parsing English text. It now returns structured data — `choice`,
  `item_label`, `amount` — and the frontend builds the sentence in
  whatever language is active. (An English `label` field is kept too, as
  a fallback for any client that doesn't localize.)
- **Guide picker is genuinely better, not just translated:** a
  specialisation filter (food / heritage / photography / religious /
  shopping / trekking / wildlife / accessibility — the real categories in
  the dataset), a "speaks your language" badge computed against the
  traveler's chosen language, a "top rated" badge, and language-matching
  guides sorted to the top.
- The one thing *not* localized: the agent trace log's content (still
  English, generated server-side by `trip.log()`) — only the show/hide
  toggle label is translated. Fully localizing trace text would mean
  restructuring every log call into translation keys + template data,
  which felt like lower value than the screens travelers actually act on.
  Flagging it rather than hiding it.

## Everything needed before you drop in API keys — status check

- Money math: `Decimal` throughout. ✅
- Budget guard: every add-to-trip action routes through one function,
  verified by 16 automated tests. ✅
- State machine: explicit `advance_to`/`retry_status` tracking, no
  inferred transitions. ✅
- Guide step: real backend endpoint, not client-side fakery. ✅
- Multilingual: full UI + negotiation text + guide matching. ✅
- Provider seam: `search_flights()`/`search_hotels()` dispatch on
  `USE_MOCK_FLIGHTS`/`USE_MOCK_HOTELS`; implement
  `real_amadeus_flights()`/`real_hotelbeds_hotels()` in `search.py`, drop
  keys into `.env`, flip the two flags. Nothing else changes. ⏳ (this part
  is yours)


## Known scope cuts (deliberate, for a hackathon-scale build)

- Flights/hotels are deterministic mocks (seeded off the route, so a demo
  is repeatable) — clean swap points for Amadeus/Hotelbeds, not wired in.
- No auth, no payment, no persistence beyond process memory — a trip lives
  as long as the backend process does.
- Agent trace log content stays English-only (see Round 3 note above);
  everything else is fully translated.
- Most cities have 0–1 seed packages, so most market benchmarks fall back
  to state/country level rather than city-level — flagged in the API
  response itself (`data_confidence`), not hidden.

## Verified

Full flow driven end-to-end via live HTTP calls (not just unit-level)
through the real `vite dev → /api proxy → uvicorn` path: reality check,
trip creation, flight/hotel selection, guide booking that correctly
triggers negotiation, `raise_cap` resolving it, and confirm — including
confirming that `/confirm` is correctly blocked while a negotiation is
unresolved. `npx vite build` is clean.
# nepo
