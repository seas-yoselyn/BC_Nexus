#!/usr/bin/env python3
"""
BCNexus CLEW Dashboard — clean, standard, folder-connected.

Author: Md Eliasinul Islam

Usage:
    pip install streamlit plotly pandas
    streamlit run dashboard_clew/app.py

Point the sidebar at any folder containing otoole result-CSV directories
(e.g. .../8ts/result_csvs_gurobi or legacy 8ts_csvs_gurobi_<runtag>).
Scenarios are auto-discovered; pick one from the dropdown, browse the
C / L / E / W tabs. All plots are Plotly (interactive, PNG-exportable).

Plot set follows common CLEWs reporting practice (UN/KTH CLEWs course,
clewsy examples, OSeMOSYS community): capacity & generation stacks for
energy; land-cover and crop-production stacks for land; withdrawal-by-
source for water; emission trajectories with tech attribution for climate.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------- naming
# Aligned with bcnexus.clews.model_structure NamingConvention.
TECH_LABELS = {
    "PWRHYD": "Hydro", "PWRBIO": "Biomass", "PWRNGS": "Natural gas",
    "PWRSOL": "Solar PV", "PWRWND": "Wind", "PWRGEO": "Geothermal",
    "PWRNUC": "Nuclear", "PWRCOA": "Coal", "PWRTRN": "Transmission",
    "BATTERY_STORAGE": "Battery", "CCS": "CCS", "HDG": "Hydrogen",
}
CROP_LABELS = {
    "ALF": "Alfalfa", "BAR": "Barley", "MAI": "Maize", "OAT": "Oats",
    "PEA": "Peas", "PTW": "Potatoes", "RAP": "Canola", "RYE": "Rye",
    "WHE": "Wheat", "OTH": "Other crops",
}
LAND_LABELS = {
    "AGR": "Agriculture (clusters)", "FOR": "Forest", "GRS": "Grassland",
    "BAR": "Barren", "BLT": "Built-up", "WAT": "Water bodies",
}
WATER_FUELS = {
    "WTRPRC": "Precipitation", "WTRSUR": "Surface water",
    "WTRGRC": "Groundwater recharge", "WTREVT": "Evapotranspiration",
    "AGRWAT": "Agriculture withdrawal", "PUBWAT": "Public supply",
    "PWRWAT": "Power sector water",
}
SECTOR_FUEL_PREFIX = {"RES": "Residential", "COM": "Commercial",
                      "IND": "Industry", "TRA": "Transport"}

RESULT_DIR_PATTERNS = ("result_csvs_*", "*ts_csvs_*")  # new + legacy layouts


# ----------------------------------------------------------------- discovery
@st.cache_data(show_spinner=False)
def discover_runs(root: str) -> dict[str, str]:
    """Map display-name -> result csv dir, searching root recursively."""
    rootp = Path(root)
    found = {}
    if not rootp.exists():
        return found
    for pat in RESULT_DIR_PATTERNS:
        for d in rootp.rglob(pat):
            if d.is_dir() and any(d.glob("*.csv")):
                rel = d.relative_to(rootp)
                # display: scenario-ish path without noisy leaf duplication
                found[str(rel)] = str(d)
    return dict(sorted(found.items()))


@st.cache_data(show_spinner=False)
def load(run_dir: str, name: str) -> pd.DataFrame | None:
    f = Path(run_dir) / f"{name}.csv"
    if not f.exists():
        return None
    df = pd.read_csv(f)
    return df if not df.empty else None


def label_pwr(tech: str) -> str:
    for k, v in TECH_LABELS.items():
        if tech.startswith(k):
            return v
    return tech


def stacked_area(df, x, y, color, title, ytitle):
    fig = px.area(df, x=x, y=y, color=color, title=title)
    fig.update_layout(yaxis_title=ytitle, xaxis_title="", legend_title="",
                      hovermode="x unified", margin=dict(t=50, b=20))
    return fig


def stacked_bar(df, x, y, color, title, ytitle):
    fig = px.bar(df, x=x, y=y, color=color, title=title)
    fig.update_layout(yaxis_title=ytitle, xaxis_title="", legend_title="",
                      barmode="stack", hovermode="x unified",
                      margin=dict(t=50, b=20))
    return fig


# ----------------------------------------------------------------- app
st.set_page_config(page_title="BCNexus CLEW Dashboard", layout="wide")
st.title("BCNexus — CLEW Results Dashboard")

with st.sidebar:
    st.header("Connect results")
    root = st.text_input("Results root folder",
                         value="data/clews_data/clews_build_data",
                         help="Any folder; result dirs are found recursively "
                              "(result_csvs_* or *ts_csvs_*).")
    runs = discover_runs(root)
    if not runs:
        st.warning("No result folders found under this root.")
        st.stop()
    run_name = st.selectbox("Scenario / run", list(runs.keys()))
    run_dir = runs[run_name]
    compare = st.multiselect("Compare with (emissions & capacity)",
                             [k for k in runs if k != run_name])
    st.caption(f"{len(runs)} run(s) discovered")

cap = load(run_dir, "TotalCapacityAnnual")
prod = load(run_dir, "ProductionByTechnologyAnnual")
use = load(run_dir, "UseByTechnology")
em = load(run_dir, "AnnualEmissions")
tem = load(run_dir, "AnnualTechnologyEmission")
newcap = load(run_dir, "NewCapacity")
capex = load(run_dir, "CapitalInvestment")
demand = load(run_dir, "Demand")

# ----------------------------------------------------------------- overview
k1, k2, k3, k4 = st.columns(4)
if em is not None:
    k1.metric("CO₂ in final year (Mt)",
              f"{em[em.YEAR == em.YEAR.max()].VALUE.sum():,.1f}")
if cap is not None:
    pw = cap[cap.TECHNOLOGY.str.startswith("PWR") &
             ~cap.TECHNOLOGY.str.startswith("PWRTRN")]
    k2.metric("Power capacity, final year (GW)",
              f"{pw[pw.YEAR == pw.YEAR.max()].VALUE.sum():,.1f}")
    lnd = cap[cap.TECHNOLOGY.str.startswith("LNDAGR")]
    if not lnd.empty:
        k3.metric("Agricultural land, final year (kkm²)",
                  f"{lnd[lnd.YEAR == lnd.YEAR.max()].VALUE.sum():,.1f}")
if prod is not None:
    wtr = prod[prod.FUEL.str.startswith("AGRWAT") |
               prod.FUEL.str.startswith("PUBWAT")]
    if not wtr.empty:
        k4.metric("Water withdrawal, final year (BCM)",
                  f"{wtr[wtr.YEAR == wtr.YEAR.max()].VALUE.sum():,.2f}")

tab_e, tab_l, tab_w, tab_c, tab_x = st.tabs(
    ["⚡ Energy", "🌾 Land", "💧 Water", "🌡️ Climate", "⚖️ Compare"])

# ----------------------------------------------------------------- ENERGY
with tab_e:
    c1, c2 = st.columns(2)
    if cap is not None:
        pw = cap[cap.TECHNOLOGY.str.startswith("PWR") &
                 ~cap.TECHNOLOGY.str.startswith("PWRTRN")].copy()
        pw["Technology"] = pw.TECHNOLOGY.map(label_pwr)
        g = pw.groupby(["YEAR", "Technology"], as_index=False).VALUE.sum()
        c1.plotly_chart(stacked_bar(g, "YEAR", "VALUE", "Technology",
                                    "Installed power capacity", "GW"),
                        use_container_width=True)
    if prod is not None:
        gen = prod[prod.FUEL == "ELCB01"].copy()
        if not gen.empty:
            gen["Technology"] = gen.TECHNOLOGY.map(label_pwr)
            g = gen.groupby(["YEAR", "Technology"], as_index=False).VALUE.sum()
            c2.plotly_chart(stacked_area(g, "YEAR", "VALUE", "Technology",
                                         "Electricity generation", "PJ"),
                            use_container_width=True)
        # final energy by sector
        sec = prod[prod.FUEL.str[:3].isin(SECTOR_FUEL_PREFIX)].copy()
        if not sec.empty:
            sec["Sector"] = sec.FUEL.str[:3].map(SECTOR_FUEL_PREFIX)
            sec["Carrier"] = sec.FUEL.str[3:].str.replace(r"B\d+$", "", regex=True)
            g = sec.groupby(["YEAR", "Sector"], as_index=False).VALUE.sum()
            st.plotly_chart(stacked_area(g, "YEAR", "VALUE", "Sector",
                                         "Final energy by sector", "PJ"),
                            use_container_width=True)
            g2 = sec.groupby(["YEAR", "Carrier"], as_index=False).VALUE.sum()
            st.plotly_chart(stacked_area(g2, "YEAR", "VALUE", "Carrier",
                                         "Final energy by carrier", "PJ"),
                            use_container_width=True)
    c3, c4 = st.columns(2)
    if newcap is not None:
        nc = newcap[newcap.TECHNOLOGY.str.startswith("PWR")].copy()
        if not nc.empty:
            nc["Technology"] = nc.TECHNOLOGY.map(label_pwr)
            g = nc.groupby(["YEAR", "Technology"], as_index=False).VALUE.sum()
            c3.plotly_chart(stacked_bar(g, "YEAR", "VALUE", "Technology",
                                        "New capacity additions", "GW"),
                            use_container_width=True)
    if capex is not None:
        cx = capex.groupby("YEAR", as_index=False).VALUE.sum()
        fig = px.bar(cx, x="YEAR", y="VALUE", title="Capital investment")
        fig.update_layout(yaxis_title="M$", xaxis_title="")
        c4.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------- LAND
with tab_l:
    c1, c2 = st.columns(2)
    if cap is not None:
        lnd = cap[cap.TECHNOLOGY.str.startswith("LND")].copy()
        if not lnd.empty:
            lnd["Class"] = lnd.TECHNOLOGY.str[3:6].map(LAND_LABELS)\
                                                  .fillna(lnd.TECHNOLOGY)
            g = lnd.groupby(["YEAR", "Class"], as_index=False).VALUE.sum()
            c1.plotly_chart(stacked_area(g, "YEAR", "VALUE", "Class",
                                         "Land allocation", "1000 km²"),
                            use_container_width=True)
            ag = lnd[lnd.TECHNOLOGY.str.startswith("LNDAGR")].copy()
            if not ag.empty:
                ag["Cluster"] = ag.TECHNOLOGY.str.extract(r"(C\d+)$")
                g = ag.dropna(subset=["Cluster"])\
                      .groupby(["YEAR", "Cluster"], as_index=False).VALUE.sum()
                c2.plotly_chart(stacked_area(g, "YEAR", "VALUE", "Cluster",
                                             "Agricultural land by yield cluster",
                                             "1000 km²"),
                                use_container_width=True)
    if prod is not None:
        crp = prod[prod.FUEL.str.startswith("CRP")].copy()
        if not crp.empty:
            crp["Crop"] = crp.FUEL.str[3:6].map(CROP_LABELS).fillna(crp.FUEL)
            g = crp.groupby(["YEAR", "Crop"], as_index=False).VALUE.sum()
            st.plotly_chart(stacked_bar(g, "YEAR", "VALUE", "Crop",
                                        "Crop production", "Mt"),
                            use_container_width=True)

# ----------------------------------------------------------------- WATER
with tab_w:
    if prod is not None:
        rows = []
        for pref, lab in WATER_FUELS.items():
            sel = prod[prod.FUEL.str.startswith(pref)]
            if not sel.empty:
                g = sel.groupby("YEAR", as_index=False).VALUE.sum()
                g["Source"] = lab
                rows.append(g)
        if rows:
            wdf = pd.concat(rows)
            supply = wdf[wdf.Source.isin(["Precipitation", "Surface water",
                                          "Groundwater recharge"])]
            demand_w = wdf[wdf.Source.isin(["Agriculture withdrawal",
                                            "Public supply",
                                            "Power sector water",
                                            "Evapotranspiration"])]
            c1, c2 = st.columns(2)
            if not supply.empty:
                c1.plotly_chart(stacked_area(supply, "YEAR", "VALUE", "Source",
                                             "Water availability by source", "BCM"),
                                use_container_width=True)
            if not demand_w.empty:
                c2.plotly_chart(stacked_area(demand_w, "YEAR", "VALUE", "Source",
                                             "Water use by purpose", "BCM"),
                                use_container_width=True)
        else:
            st.info("No water-commodity results found in this run.")
    sl = load(run_dir, "StorageLevelYearStart")
    if sl is not None and "STORAGE" in sl.columns:
        res = sl[sl.STORAGE.str.contains("HYDRO|WATER", case=False, na=False)]
        if not res.empty:
            fig = px.line(res, x="YEAR", y="VALUE", color="STORAGE",
                          title="Reservoir storage level (year start)")
            fig.update_layout(yaxis_title="Energy-equivalent (PJ)", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------- CLIMATE
with tab_c:
    c1, c2 = st.columns(2)
    if em is not None:
        fig = px.line(em, x="YEAR", y="VALUE", color="EMISSION",
                      title="Annual emissions", markers=True)
        fig.update_layout(yaxis_title="Mt CO₂e", xaxis_title="")
        c1.plotly_chart(fig, use_container_width=True)
        cum = em.groupby("YEAR", as_index=False).VALUE.sum()
        cum["Cumulative"] = cum.VALUE.cumsum()
        fig = px.area(cum, x="YEAR", y="Cumulative",
                      title="Cumulative emissions")
        fig.update_layout(yaxis_title="Mt CO₂e", xaxis_title="")
        c2.plotly_chart(fig, use_container_width=True)
    if tem is not None:
        top = (tem.groupby("TECHNOLOGY").VALUE.sum()
                  .nlargest(10).index.tolist())
        t = tem[tem.TECHNOLOGY.isin(top)].copy()
        t["Technology"] = t.TECHNOLOGY.map(label_pwr)
        g = t.groupby(["YEAR", "Technology"], as_index=False).VALUE.sum()
        st.plotly_chart(stacked_bar(g, "YEAR", "VALUE", "Technology",
                                    "Emissions by technology (top 10)", "Mt CO₂e"),
                        use_container_width=True)
    if prod is not None:
        ccs = prod[prod.FUEL.str.startswith("CO2")]
        if not ccs.empty:
            g = ccs.groupby("YEAR", as_index=False).VALUE.sum()
            fig = px.bar(g, x="YEAR", y="VALUE", title="CO₂ captured (CCS)")
            fig.update_layout(yaxis_title="Mt", xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------------------- COMPARE
with tab_x:
    if not compare:
        st.info("Pick runs to compare in the sidebar.")
    else:
        sel = [run_name] + compare
        emf, capf = [], []
        for r in sel:
            e = load(runs[r], "AnnualEmissions")
            if e is not None:
                e = e.groupby("YEAR", as_index=False).VALUE.sum()
                e["Run"] = r
                emf.append(e)
            c = load(runs[r], "TotalCapacityAnnual")
            if c is not None:
                c = c[c.TECHNOLOGY.str.startswith("PWR") &
                      ~c.TECHNOLOGY.str.startswith("PWRTRN")]
                c = c.groupby("YEAR", as_index=False).VALUE.sum()
                c["Run"] = r
                capf.append(c)
        c1, c2 = st.columns(2)
        if emf:
            fig = px.line(pd.concat(emf), x="YEAR", y="VALUE", color="Run",
                          title="Annual emissions across runs", markers=True)
            fig.update_layout(yaxis_title="Mt CO₂e", xaxis_title="")
            c1.plotly_chart(fig, use_container_width=True)
        if capf:
            fig = px.line(pd.concat(capf), x="YEAR", y="VALUE", color="Run",
                          title="Total power capacity across runs", markers=True)
            fig.update_layout(yaxis_title="GW", xaxis_title="")
            c2.plotly_chart(fig, use_container_width=True)

st.caption("BCNexus CLEW dashboard — otoole result CSVs, auto-discovered. "
           "Units follow model conventions (PJ, GW, Mt, 1000 km², BCM); "
           "verify against models/*/otoole config when in doubt.")
