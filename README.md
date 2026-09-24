# RNG Gods

## 1. Team & Problem Statement

- **Team:** RNG Gods
- **Event:** KogniVera Hackathon 2026
- **College:** BMS College Of Engineering
- **Problem statement:** PS-04 — PackagePro: Dynamic Tour Packages

## 2. What we built

- A budget-honest trip intake that validates route, date, traveller, and INR budget boundaries.
- An end-to-end flow to select a flight, package, optional local guide, and confirm a trip.
- A single backend budget guard that blocks all over-cap priced choices and presents actionable negotiation options.
- Seeded, offline package and guide data so the live demo does not depend on external travel-provider keys.
- Language-aware, explainable guide ranking and a grounded itinerary summary.

## 3. Architecture

```text
React + Vite UI  <-->  FastAPI API  <-->  SQLite schema + committed fixture data
                         |                        |
                         +--> central budget guard +--> packages / components / guides
                         +--> grounded assistant prompt contract
```

## 4. Data model

Canonical-style PackagePro data is under `data-model/`: `schema.sql` defines destinations, packages, package components, and guides; `seed/demo_data.json` is the repeatable demo corpus. `DATA_MODEL.md` documents the D1–D9 mapping and the session-specific additions (`trips`, `trip_items`, `negotiations`).

The official shared D1–D9 schema was not present in the provided repository. The mapping is therefore explicitly marked as an assumption instead of claiming unverifiable conformance.

## 5. AI features

- **Grounded itinerary summary:** `POST /api/assistant/summary` derives its result from the selected package and trip only. Its anti-hallucination contract is committed in `ai/prompts/itinerary_summary.md`; the demo uses a deterministic local implementation.
- **Guide retrieval/ranking:** guides are filtered by destination and ranked by language match and rating from the committed guide corpus. This is transparent, data-grounded retrieval rather than an unsupported recommendation claim.

## 6. Run it locally

Requires Python 3.11+ and Node 20+.

```bash
git clone <repository-url>
cd nepo

# terminal 1
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn src.main:app --reload --port 9000

# terminal 2
cd frontend
npm install
npm run dev
```

Open `http://localhost:5174`. The API creates and seeds SQLite from the committed schema and fixture data at startup.

## 7. Demo path

1. Create a Bengaluru → Jaipur trip with a ₹30,000 budget.
2. Select **IndiGo Economy** and then **Jaipur Essentials · 3 days**.
3. Select the Hindi heritage guide or choose **Skip guide**.
4. If an item is over budget, resolve the server-issued negotiation using **Raise cap** or **Drop item**.
5. Confirm the trip, then generate the grounded itinerary summary.

## 8. Tests / proof

```bash
cd backend
python -m pytest ../tests -q
```

The hard-proof integration test asserts that an over-budget package is rejected, confirmation is blocked while its negotiation is unresolved, a cheaper package can be selected, and the completed trip can then be confirmed. A second test covers request-boundary validation, and a third proves the raise-cap resolution advances the original booking step.
