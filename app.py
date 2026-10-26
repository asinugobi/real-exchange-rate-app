"""Real Exchange Rate app.

Uses monthly IMF CPI and exchange-rate data (SDMX 3.0 API) to compute

    S(t)   = units of Country 2 currency per 1 unit of Country 1 currency
    RER(t) = S(t) * P1(t) / P2(t)
    RER*   = average of RER(t) over valid months in the selected sample
    Real Index(t) = 100 * RER(t) / RER*
"""

import io

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

API_BASE = "https://api.imf.org/external/sdmx/3.0"
DATA_ACCEPT = "application/vnd.sdmx.data+json;version=2.0.0"
STRUCT_ACCEPT = "application/vnd.sdmx.structure+json;version=2.0.0"
START_PERIOD = "1976-01"
EURO_AREA = "G163"
TIMEOUT = 60

# Used only if the IMF country list cannot be downloaded.
FALLBACK_COUNTRIES = {
    "AUS": "Australia", "BRA": "Brazil", "CAN": "Canada", "CHE": "Switzerland",
    "CHN": "China", "G163": "Euro area", "GBR": "United Kingdom", "IND": "India",
    "JPN": "Japan", "KOR": "Korea, Republic of", "MEX": "Mexico", "NGA": "Nigeria",
    "NOR": "Norway", "NZL": "New Zealand", "SWE": "Sweden", "TUR": "Türkiye",
    "USA": "United States", "ZAF": "South Africa",
}


# ---------------------------------------------------------------------------
# IMF data access
# ---------------------------------------------------------------------------
def _get_json(url: str, accept: str, params: dict | None = None) -> dict:
    resp = requests.get(url, headers={"Accept": accept}, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _parse_series(payload: dict) -> dict[str, pd.Series]:
    """Turn an SDMX-JSON 2.0 data message into {series_key: monthly Series}."""
    data = payload.get("data", {})
    datasets = data.get("dataSets") or []
    structures = data.get("structures") or []
    if not datasets or not structures or "series" not in datasets[0]:
        return {}

    dims = structures[0]["dimensions"]
    series_dims = dims["series"]
    periods = [v["value"] for v in dims["observation"][0]["values"]]

    out = {}
    for key, body in datasets[0]["series"].items():
        idx = [int(i) for i in key.split(":")]
        code = ".".join(series_dims[d]["values"][i]["id"] for d, i in enumerate(idx))
        obs = {}
        for pos, values in body.get("observations", {}).items():
            raw = values[0] if values else None
            if raw in (None, "", "NaN"):
                continue
            # IMF periods look like "2024-M01"
            obs[pd.Period(periods[int(pos)].replace("-M", "-"), freq="M")] = float(raw)
        s = pd.Series(obs, dtype="float64").sort_index()
        out[code] = s
    return out


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def fetch_series(flow: str, key: str, start: str = START_PERIOD) -> pd.Series:
    url = f"{API_BASE}/data/dataflow/IMF.STA/{flow}/+/{key}"
    payload = _get_json(url, DATA_ACCEPT, params={"c[TIME_PERIOD]": f"ge:{start}"})
    series = _parse_series(payload)
    if not series:
        return pd.Series(dtype="float64")
    return next(iter(series.values()))


def fetch_cpi(iso3: str) -> tuple[pd.Series, str]:
    """Monthly CPI; falls back to HICP (the IMF stores the Euro area index as HICP)."""
    for index_type in ("CPI", "HICP"):
        s = fetch_series("CPI", f"{iso3}.{index_type}._T.IX.M")
        if not s.empty:
            return s, index_type
    return pd.Series(dtype="float64"), "none"


def fetch_fx_per_usd(iso3: str) -> pd.Series:
    """Local-currency units per USD (period average)."""
    s = fetch_series("ER", f"{iso3}.XDC_USD.PA_RT.M")
    if s.empty and iso3 == "USA":
        # USD per USD is 1 by definition.
        idx = pd.period_range(START_PERIOD, pd.Timestamp.today().to_period("M"), freq="M")
        s = pd.Series(1.0, index=idx)
    return s


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def country_list() -> dict[str, str]:
    """Countries (and the Euro area) that have both IMF monthly CPI and FX data."""
    try:
        recent = {"c[TIME_PERIOD]": "ge:2015-01"}
        er = _get_json(f"{API_BASE}/data/dataflow/IMF.STA/ER/+/*.XDC_USD.PA_RT.M", DATA_ACCEPT, recent)
        cpi = _get_json(f"{API_BASE}/data/dataflow/IMF.STA/CPI/+/*.*._T.IX.M", DATA_ACCEPT, recent)
        er_codes = {k.split(".")[0] for k in _parse_series(er)}
        cpi_codes = {k.split(".")[0] for k in _parse_series(cpi)}
        codes = (er_codes & cpi_codes) | {"USA"}

        cl = _get_json(f"{API_BASE}/structure/codelist/IMF/CL_COUNTRY/+", STRUCT_ACCEPT)
        names = {c["id"]: c.get("name", c["id"]) for c in cl["data"]["codelists"][0]["codes"]}
        result = {c: names.get(c, c) for c in codes}
        if EURO_AREA in result:
            result[EURO_AREA] = "Euro area"
        if len(result) < 10:
            raise ValueError("country list too short")
        return dict(sorted(result.items(), key=lambda kv: kv[1]))
    except Exception:
        return dict(sorted(FALLBACK_COUNTRIES.items(), key=lambda kv: kv[1]))


# ---------------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------------
def build_dataset(c1: str, c2: str) -> tuple[pd.DataFrame, dict]:
    p1, p1_type = fetch_cpi(c1)
    p2, p2_type = fetch_cpi(c2)
    fx1 = fetch_fx_per_usd(c1)
    fx2 = fetch_fx_per_usd(c2)

    df = pd.concat(
        {"FX1_per_USD": fx1, "FX2_per_USD": fx2, "P1": p1, "P2": p2}, axis=1
    ).sort_index()
    df = df[df.index >= pd.Period(START_PERIOD, freq="M")]
    # S(t) = (C2 per USD) / (C1 per USD) = units of C2 per 1 unit of C1
    df["S"] = df["FX2_per_USD"] / df["FX1_per_USD"]
    df["RER"] = df["S"] * df["P1"] / df["P2"]
    meta = {"p1_type": p1_type, "p2_type": p2_type,
            "missing": [n for n, s in (("CPI of Country 1", p1), ("CPI of Country 2", p2),
                                       ("FX of Country 1", fx1), ("FX of Country 2", fx2)) if s.empty]}
    return df, meta


def sample_with_index(df: pd.DataFrame, start: pd.Period, end: pd.Period) -> tuple[pd.DataFrame, float]:
    sample = df.loc[(df.index >= start) & (df.index <= end)].copy()
    valid = sample["RER"].notna()
    rer_star = float(sample.loc[valid, "RER"].mean()) if valid.any() else float("nan")
    sample["RER_star"] = rer_star
    sample["Real_Index"] = 100 * sample["RER"] / rer_star
    sample["Valid_month"] = valid
    return sample, rer_star


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Real Exchange Rate App", layout="wide")
st.title("Real Exchange Rate App")
st.caption(
    "Monthly IMF CPI and exchange-rate data. "
    "S(t) = units of Country 2 currency per 1 unit of Country 1 currency; "
    "RER(t) = S(t) × P1(t) / P2(t); Real Index(t) = 100 × RER(t) / RER*."
)

with st.spinner("Loading IMF country list..."):
    countries = country_list()
codes = list(countries)
label = lambda c: f"{countries[c]} ({c})"  # noqa: E731

col1, col2 = st.columns(2)
c1 = col1.selectbox("Country 1 (base currency)", codes, format_func=label,
                    index=codes.index("GBR") if "GBR" in codes else 0)
c2 = col2.selectbox("Country 2 (quote currency)", codes, format_func=label,
                    index=codes.index("USA") if "USA" in codes else 1)

if c1 == c2:
    st.warning("Choose two different countries.")
    st.stop()

try:
    with st.spinner("Downloading IMF data..."):
        df, meta = build_dataset(c1, c2)
except requests.RequestException as exc:
    st.error(f"Could not download IMF data: {exc}. Please try again in a moment.")
    st.stop()

if meta["missing"]:
    st.error("The IMF has no monthly data for: " + ", ".join(meta["missing"]) + ".")
    st.stop()

valid_months = df.index[df["RER"].notna()]
if valid_months.empty:
    st.error("No months where both CPIs and both exchange rates are available.")
    st.stop()

for code, kind in ((c1, meta["p1_type"]), (c2, meta["p2_type"])):
    if kind == "HICP":
        st.info(f"{countries[code]}: using the IMF HICP index as its CPI.")

months = list(df.loc[valid_months.min():valid_months.max()].index)
start, end = st.select_slider(
    "Sample period (RER* is recalculated over these months)",
    options=months, value=(months[0], months[-1]),
    format_func=lambda p: p.strftime("%Y-%m"),
)

sample, rer_star = sample_with_index(df, start, end)
n_valid = int(sample["Valid_month"].sum())
if n_valid == 0:
    st.error("No valid months in the selected period.")
    st.stop()

cur1, cur2 = countries[c1], countries[c2]
m1, m2, m3, m4 = st.columns(4)
m1.metric("RER*", f"{rer_star:,.4f}")
m2.metric("Valid months", f"{n_valid} / {len(sample)}")
m3.metric("Latest S(t)", f"{sample['S'].dropna().iloc[-1]:,.4f}")
m4.metric("Mean Real Index", f"{sample['Real_Index'].mean():.2f}")
if n_valid < len(sample):
    st.caption("Months with a missing CPI or FX value are excluded from RER* and shown as gaps.")

view = st.radio("Chart", ["Real", "Nominal", "Both"], horizontal=True)
x = sample.index.to_timestamp()
real_trace = go.Scatter(x=x, y=sample["Real_Index"], name="Real Index (sample avg = 100)",
                        line=dict(color="#1f77b4"))
nom_trace = go.Scatter(x=x, y=sample["S"], name=f"Nominal S(t): {c2} currency per {c1} currency",
                       line=dict(color="#d62728"))

if view == "Both":
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(real_trace, secondary_y=False)
    fig.add_trace(nom_trace, secondary_y=True)
    fig.update_yaxes(title_text="Real Index (sample avg = 100)", secondary_y=False)
    fig.update_yaxes(title_text=f"S(t): {c2} per 1 {c1} currency unit", secondary_y=True)
elif view == "Real":
    fig = go.Figure(real_trace)
    fig.add_hline(y=100, line_dash="dot", line_color="gray")
    fig.update_yaxes(title_text="Real Index (sample avg = 100)")
else:
    fig = go.Figure(nom_trace)
    fig.update_yaxes(title_text=f"S(t): {c2} per 1 {c1} currency unit")

fig.update_layout(height=520, hovermode="x unified",
                  title=f"{cur1} (Country 1) vs {cur2} (Country 2)",
                  legend=dict(orientation="h", y=-0.15))
st.plotly_chart(fig, width="stretch")

st.markdown(
    "An **increase** in the Real Index means Country 1's goods have become more expensive "
    "relative to Country 2's goods (a real appreciation of Country 1's currency)."
)

export = sample.reset_index(names="Month")
export["Month"] = export["Month"].astype(str)
export = export.rename(columns={
    "FX1_per_USD": f"FX1_{c1}_per_USD",
    "FX2_per_USD": f"FX2_{c2}_per_USD",
    "S": f"S_{c2}_per_{c1}",
    "P1": f"P1_CPI_{c1}",
    "P2": f"P2_CPI_{c2}",
})
buf = io.StringIO()
export.to_csv(buf, index=False)
st.download_button("Download CSV of sample period", buf.getvalue(),
                   file_name=f"rer_{c1}_{c2}_{start}_{end}.csv", mime="text/csv")

with st.expander("Data table"):
    st.dataframe(export, width="stretch", hide_index=True)

st.caption("Source: IMF SDMX 3.0 API (dataflows IMF.STA:CPI and IMF.STA:ER). "
           "Data may have gaps or limited coverage for some countries.")
