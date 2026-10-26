# Real Exchange Rate App: Submission

**Streamlit app URL:** https://real-exchange-rate-app-dbyxqkresptdzta3pz4ksd.streamlit.app
**GitHub repository URL:** https://github.com/asinugobi/real-exchange-rate-app

**LLM used:** Claude Opus 5.5 (`claude-opus-5-5`), Anthropic, via the Claude desktop app (Claude Code)
**Date:** 25–26 October 2026

---

## 1. Prompt used

> Build me a Streamlit app (Python 3.12) and give me three complete files: `app.py`, `requirements.txt`, and `README.md`.
>
> Requirements:
> - Let users choose Country 1 and Country 2 from IMF countries and the Euro area (IMF code G163). Retrieve monthly IMF CPI and exchange-rate data from January 1976 where available, using the IMF SDMX 3.0 API at https://api.imf.org/external/sdmx/3.0. CPI key: `{ISO3}.CPI._T.IX.M`. Exchange-rate key: `{ISO3}.XDC_USD.PA_RT.M`.
> - Define S(t) as units of Country 2 currency per one unit of Country 1 currency. IMF rates are local currency per USD, so convert them to that direction. Let P1(t) and P2(t) be the monthly CPIs. Compute RER(t) = S(t) × P1(t) / P2(t).
> - Over user-selected start and end months, compute RER* = the average of RER(t) over valid months, and plot Real Index(t) = 100 × RER(t) / RER*. Recompute RER* when the dates change. Plot nominal S(t) in actual currency units, not normalized.
> - Let users choose Real, Nominal, or Both in interactive charts (Both on separate y-axes), and add a CSV download button with all observations and calculations for the selected sample period.
> - IMF data may have gaps or limited coverage, so handle missing data gracefully.

The full chat is available as screenshots (attach them here).

## 2. Issues found and fixed during development

- The IMF does not publish the Euro area (G163) index under `CPI`. It publishes it under `HICP` (`G163.HICP._T.IX.M`). The app tries `CPI` first and falls back to `HICP`, and it tells the user when it does this.
- The U.S. CPI has no value for October 2025 in the IMF data. That month is marked `Valid_month = False` and left out of RER*, and it shows as a gap in the chart.

## 3. Checks (UK = Country 1, U.S. = Country 2)

| Check | Result |
|---|---|
| S is USD per GBP | ✅ Column `S_USA_per_GBR` ≈ 1.25–1.64 over 2000–2025 (for example 1.3378 in Dec 2025) |
| Sample changed to 2000-01 … 2025-12 | ✅ RER* recomputed to 1.377365 (full 1976–2026 sample: 1.4249) |
| Exported Real Index averages 100 | ✅ Mean of `Real_Index` over 311 valid months = 100.0000 |
| Real / Nominal / Both charts | ✅ All three render. Both uses a left axis (index) and a right axis (USD per GBP) |
| Other pair (Euro area vs Japan) | ✅ Works, using HICP for the Euro area |

## 4. Manual RER verification (June 2020, from the exported CSV)

Inputs from `rer_GBR_USA_2000-01_2025-12.csv`, row `2020-06`:

- FX1 (GBP per USD) = 0.798597
- FX2 (USD per USD) = 1
- P1 (UK CPI) = 108.8
- P2 (US CPI) = 118.225406
- RER* (2000-01 to 2025-12) = 1.377365

Calculation:

1. S = FX2 / FX1 = 1 / 0.798597 = **1.252195 USD per GBP**
2. RER = S × P1 / P2 = 1.252195 × 108.8 / 118.225406 = 136.2388 / 118.2254 = **1.152365**
3. Real Index = 100 × RER / RER* = 100 × 1.152365 / 1.377365 = **83.66**

These match the app's columns `S_USA_per_GBR` = 1.252195, `RER` = 1.152365 and `Real_Index` = 83.664492. ✅

Interpretation: in June 2020 the pound was about 16% weaker in real terms against the dollar than its 2000–2025 average.

## 5. Attached

- `rer_GBR_USA_2000-01_2025-12.csv` (export from the app)
- Screenshots of the LLM chat
