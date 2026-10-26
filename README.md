# Real Exchange Rate App

A Streamlit app that computes the bilateral real exchange rate (RER) between any two
IMF countries (including the Euro area) from monthly IMF data, starting January 1976
where available.

## Definitions

- **S(t)**: units of Country 2 currency per one unit of Country 1 currency.
  IMF rates are local-currency units per USD, so
  `S(t) = (Country 2 per USD) / (Country 1 per USD)`.
- **P1(t), P2(t)**: monthly CPI of Country 1 and Country 2.
- **RER(t) = S(t) × P1(t) / P2(t)**
- **RER\*** = average of RER(t) over the valid months (all four inputs present) in the
  selected sample. It is recalculated whenever the sample dates change.
- **Real Index(t) = 100 × RER(t) / RER\***, so it averages 100 over the sample.

Nominal S(t) is plotted in actual currency units (not normalized).

## Features

- Choose Country 1 and Country 2 from IMF countries with monthly CPI and FX data.
- Choose start and end months for the sample.
- Chart Real, Nominal, or Both (Both uses two y-axes).
- Download a CSV with every observation and calculation in the sample period.

## Data

IMF SDMX 3.0 API: `https://api.imf.org/external/sdmx/3.0`

| Series | Dataflow | Key |
|---|---|---|
| CPI | `IMF.STA/CPI` | `{ISO3}.CPI._T.IX.M` (Euro area `G163` uses `HICP` in place of `CPI`) |
| Exchange rate | `IMF.STA/ER` | `{ISO3}.XDC_USD.PA_RT.M` (period average, local currency per USD) |

No API key is needed. IMF data can have gaps; months with a missing input are left out
of RER\* and shown as gaps in the chart. Downloads are cached for 24 hours.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Built for Python 3.12 and deployed on Streamlit Community Cloud.
