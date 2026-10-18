# Hawaiʻi 2026 — Oʻahu + Maui

## 📑 Contents

- [Where things live](#where-things-live)
- [Workflow](#workflow)
- [Collaborating](#collaborating)

**Oct 31 – Nov 8, 2026** · first island **Oʻahu** Oct 31–Nov 3 (no car) · Maui Nov 3–8 (no car, Kīhei base) · Shivam's birthday Nov 6 (Maui) · back in NYC Nov 9, office Nov 10

## Where things live

| File | What it is | Rule |
|---|---|---|
| [`oahu.md`](oahu.md) | Island guide for Oct 31 – Nov 3: Waikīkī base, no car, the final plan at the top, options and backups below | Updates the Oʻahu part of the plan |
| [`maui.md`](maui.md) | Island guide for Nov 3 – Nov 8: Kīhei base, no car, birthday rest day, the final plan at the top, options below | Updates the Maui part of the plan |
| [`birthday.md`](birthday.md) | Everything for the Nov 6 birthday: day plan, spa, dinner, cocktails, dancing, weed rules, rides, to-dos, cost, backups | Book details still go in `bookings.md` and costs in `budget.md` |
| [`commute.md`](commute.md) | Every ride of the trip (no car): options per leg, cost, our pick, blockers, no-car vs rental-car cost | Update when a ride is booked; confirmation goes in `bookings.md` |
| [`photos.md`](photos.md) | Photo guide: up to 6 photos of every hotel, restaurant, bar and place in the plan (Oʻahu, Maui, Kauaʻi), with a full index and Google Images/Maps links | Add photos by hand; credit the source under each one |
| [`map.md`](map.md) | Hotel-centred maps per island (normal + satellite), one section per trip out of the hotel, distances/drive times, Google map/terrain/3D links | Regenerate with `maps/tools/` when the plan changes |
| [`tentative_plan.md`](tentative_plan.md) | The clean, day-by-day plan | **Only things that are decided.** If there are still options, it isn't here yet. |
| [`overall_plan.md`](overall_plan.md) | The big master doc: every option per day, photos, research, closures, drive times, costs, rain backups | Mark choices ✅ when decided, then copy them into `tentative_plan.md` |
| [`TODOs.md`](TODOs.md) | Task tracker: what to book/decide, owner, deadline | Tick `[x]` when done; add the confirmation # to `bookings.md` |
| [`bookings.md`](bookings.md) | Every confirmed reservation: conf #, time, address, cancel policy | The single place to look when you're standing at a check-in desk |
| [`budget.md`](budget.md) | Estimated vs. actual spend, and the split between you two | Update when something is paid |
| [`packing.md`](packing.md) | Shared packing checklist | Tick as you pack |
| [`hotels.md`](hotels.md) | Hotel picks, alternatives, Airbnb + round-2 research, booking checklist | Update when a hotel is booked; conf # goes in `bookings.md` |
| [`hotels/`](hotels/) | One page per picked hotel (rooms, reviews, costs, pre-booking checklist) | |
| [`references.md`](references.md) | Index of the 8 Google Docs and every doc in this repo, which are current vs. historical, and where they disagree | Read-only inputs |
| `maps/` | Map images + `maps/tools/` (`gen_md.py` writes `map.md`; `render.py` makes the older day images) | Don't hand-edit `map.md`; regenerate it |
| `photos/` | Photos stored in the repo: public-domain Diamond Head / USS Arizona, and `photos/us/` birthday photos (used by `tentative_plan.md`, `birthday.md`) | Credit the source under each image |
| `docs/` | PDFs/screenshots of tickets & confirmations (**don't commit IDs/passport scans**, see below) | |
| [`2026-10-12_itinerary_options.md`](2026-10-12_itinerary_options.md) | Raw research dump, kept for reference (not maintained) | |

## Workflow

1. Explore/compare in `overall_plan.md` → decide together → mark ✅.
2. Add the booking task to `TODOs.md` → book it → move details into `bookings.md` + cost into `budget.md`.
3. Copy the final version of that day into `tentative_plan.md`.

Status legend used everywhere: ✅ decided/booked · ⬜ to book · 🟡 option / still deciding · ⏳ booked-pending (waitlist, hold) · ❌ dropped.

## Collaborating

Private GitHub repo. Edit right on github.com (pencil icon) or clone it and edit locally. Small commits like "booked Molokini snorkel" make the history readable.

**Privacy:** the repo is private, but still don't commit passport/ID scans or full card numbers. Confirmation numbers are fine.
