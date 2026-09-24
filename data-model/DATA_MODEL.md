# Data-model conformance

The official shared D1–D9 definition was not included in the supplied repository. This explicit mapping avoids claiming undocumented conformance.

| Area | Implementation |
|---|---|
| D1 destinations | `destinations` |
| D2 packages | `packages` (`title`, price, duration) |
| D3 components | `package_components` (`price_delta`, `is_swappable`) |
| D4 accommodation | package component |
| D5 transport | selected flight in `trip_items` |
| D6 guides | `guides` (`display_name`, language, specialization) |
| D7 availability | fixture inventory + traveller bounds |
| D8 booking | `trips`, `trip_items` |
| D9 pricing | integer `price_paise` (INR) |

Additions are `trips`, `trip_items`, and `negotiations`, required for a budget-checked booking session. The backend enforces: nonnegative integer money, ₹5,000–₹500,000 budget, 1–8 travellers, distinct route, ordered dates, and no confirmation with a pending over-budget negotiation.
