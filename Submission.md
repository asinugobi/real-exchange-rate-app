# Real Exchange Rate App: Submission

**Streamlit app URL:** https://real-exchange-rate-app-dbyxqkresptdzta3pz4ksd.streamlit.app
**GitHub repository URL:** https://github.com/asinugobi/real-exchange-rate-app

**LLM used:** Claude Opus 5.5 (`claude-opus-5-5`), Anthropic, via the Claude desktop app (Claude Code)
**Date:** 25–26 October 2026

---

## 1. Prompts used

These are the exact prompts sent to the model, in order. Screenshots of the same chat are attached.

| # | Date | Prompt (verbatim) |
|---|---|---|
| 1 | 25 Oct 2026 | "Complete the assignment below for me", followed by the full assignment text pasted in (steps 1–5, the app and economic requirements, and the data hints). |
| 2 | 26 Oct 2026 | "Yes, open GitHub in the in-app browser and help me create the repo and deploy to Streamlit. I'll sign in myself." |
| 3 | 26 Oct 2026 | "I'm signed in to GitHub. Go ahead and create the repo." |
| 4 | 26 Oct 2026 | "I'm signed in to Streamlit Community Cloud. Go ahead and deploy the app." |
| 5 | 26 Oct 2026 | "push this code to github. then pull the repo to my local machine. clone the repo to following directory /Users/obiasinugo/Code/" |
| 6 | 26 Oct 2026 | "Yes, copy Submission.md and the CSV into ~/Code/real-exchange-rate-app but don't commit them." |
| 7 | 26 Oct 2026 | "push the new changes" |
| 8 | 26 Oct 2026 | "I've run gh auth login. Push the commit now." |
| 9 | 26 Oct 2026 | "follow the submission instructions for me and create a document that i can submit." |
| 10 | 26 Oct 2026 | "Yes, update Submission.md in the repo so its prompt section lists the exact prompts, then commit and push." |

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
