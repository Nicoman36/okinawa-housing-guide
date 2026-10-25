# Okinawa Housing Agency Directory

A bilingual (English `/`, Japanese `/ja/`) static directory of housing and rental agencies in Okinawa, with the official housing-office contacts, for U.S. Forces (SOFA) members, other foreign residents and newcomers. Built from the Okinawa Martial Arts Directory template: same generator, same verification-label approach, new subject.

## Before you publish
1. Edit `config.json`: `base_url`, `contact_email`, `github_repo` (placeholders are `okinawahousing.example` / `OWNER`).
2. Push to GitHub, enable Pages (source: GitHub Actions), run **Build & deploy**.
3. Run **Geocode addresses** once (adds map pins and re-triggers the deploy itself).
4. Have a native speaker review the Japanese text (the Japanese layer in `catalog.py` and the `LANG == "ja"` branches in `build_site.py`).
5. Read the policy lines on the About and For-agencies pages ("listing is free, no paid placement") and change them if they are not true for you.

## Layout
- `data/locations.csv` is the source of truth (27 rows); `data/sources.csv` records where facts came from.
- `scripts/`: `build_site.py` (generator, stdlib), `validate_data.py`, `geocode.py` (GSI), `stale_report.py`, `check_links.py`, `catalog.py` (services, labels, Japanese), `geo.py` (municipalities).
- `templates/assets/`: `app.js`, `map.js`, `style.css`.
- `.github/workflows/`: deploy, geocode, validate (PRs), monthly verification queue. `.github/ISSUE_TEMPLATE/`: forms, used only if `use_github` is true.
- Local preview: `python3 scripts/build_site.py && python3 -m http.server --directory dist`.

## Data conventions
- `kind`: `agency`, `organization` (official office) or `portal`. Only agencies count in the headline numbers.
- `services`: `;`-separated slugs from `catalog.py`.
- Verification: A = the agency's or office's own page checked (date in `last_verified`); B = directory, news or older page, not confirmed; C = older list; D = lead, details unconfirmed. Status: active, unverified, needs_check, closed, moved. Closed rows are hidden.
- `english` and `military` are free text. `english` starting "Yes"/"Reported" gives an English chip, "Likely" gives "English (likely)", "unknown — …" displays as "Not stated". `military` starting "Yes" gives a Military families chip; "Reported"/"Likely" give "Military (likely)". Record "approved" or "military-friendly" as the agency's own claim.
- `license`: the broker licence number exactly as the agency publishes it, e.g. `Okinawa Prefectural Governor (2) No. 5027`; verify it in the MLIT register (see sources). Most agencies don't publish one, so the validator warns for each; that list is the to-do.
- Do not publish personal mobile numbers (validator warns on 070/080/090). On-base offices get no map pin.
- Directories (Total Okinawa) are leads only. Don't read sites that disallow automated access (Robinson Housing was skipped for this reason). News reports give context only; don't paste article text.

## Seed data status (17 Oct 2026)
23 agencies: 16 labelled A (own site checked), 5 labelled B (Tokuzato, Oki Corp, Dynasty, Ishiken, Robinson), 2 labelled D (DSH, Tomiya). Plus 2 official offices and 2 portals (Homes.mil, Total Okinawa). Nine Japanese addresses were transcribed from English addresses on the agencies' sites; the listing notes say so, and the geocoder will flag mismatches.

## Reusing the template for another topic
Replace `catalog.py` (SERVICES, labels, Japanese), the CSV values, `config.json`, the long-form functions in `build_site.py` (`build_guide`, `build_about`, `build_sources`, `build_suggest`, `build_agencies`, `build_privacy`, hero text in `build_home`), the brand mark (`家` in `header()`/`page()`) and the colour variables at the top of `style.css`.

## Design notes
Modern, sharp look: Bricolage Grotesque (display) and Instrument Sans (body), both self-hosted variable fonts under the SIL Open Font License (licences in `templates/assets/fonts/`). One accent blue on cool neutrals, full dark mode, icons are CSS masks (no emoji, no icon font). The home-page floor plan is the only animated element and respects `prefers-reduced-motion`. All design lives in `templates/assets/style.css` (tokens at the top).

## Japanese-run agencies (segment)
`data/locations.csv` has a `segment` column. Leave it blank for the main (SOFA/English-oriented) directory; set `local` for Japanese-run agencies, which appear on `/local-agencies/` and in Search only when "Include Japanese-run agencies" is ticked. They are left out of the home counts, service pages, area pages and map.

## Renter reports, base distances and tools

- `data/places.csv` holds reference points (bases, gates, landmarks). Entries marked `area` precision are approximate; distances are straight-line (Haversine), not driving time.
- `data/experiences.csv` holds approved renter reports. Reports arrive as a prefilled GitHub issue (`renter-experience.yml`) or an email draft. A person reads each one, removes personal details, and copies approved ones into this file with `status=approved`. A listing shows an aggregate only once it has 3 approved reports; there is no star score.
- `templates/assets/tools.js` powers the shortlist (browser localStorage only), compare view, checklist progress, cost estimator, glossary filter and per-listing mini-map.
- `/checklist/`, `/costs/`, `/housing-office/`, `/glossary/` are English-only for now; Japanese pages link to them. Fee ranges are typical figures, not quotes; confirm office contacts and hours by phone.
- Pages are built by `scripts/extra_pages.py` (exec'd from `build_site.py`).

## Guides (English only)

`/guides/` hub plus move-in, rent-prices, avoid-problems, living-in-okinawa and oha pages, built by `build_guides()` in `scripts/extra_pages.py`. Each page lists sources and a review date; figures (OHA rates, agency rent ranges) come from Stars and Stripes, 11 May 2026, and must be re-checked when rates change. The Kadena vehicle article and the Stripes mold article are old or undated, so they are used only for general lessons.
