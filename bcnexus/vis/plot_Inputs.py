"""
Input-side plots for BCNexus — what goes INTO the model.

Author: Md Eliasinul Islam

The result plots (plot_Energy/Land/Water/Climate) show what the optimiser
produced. These show what it was *given*: demands, activity bounds, activity
ratios, costs and capacity limits. Reading them first prevents the common
error of reporting a prescribed input as if it were a model finding.

All functions take the INPUT csv directory (the folder holding
AccumulatedAnnualDemand.csv, SpecifiedAnnualDemand.csv, InputActivityRatio.csv,
...), typically:
    data/clews_data/clews_build_data/Model_<algo>/<scenario>/  (or the
    storage_case_input_csvs folder used for the run)

Every function returns a plotly figure, or None when the source CSV is absent
or empty — same contract as the result plots.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from bcnexus.vis import palette

# sector / fuel decoding shared with the result plots
_SECTORS = {"RES": "Residential", "COM": "Commercial", "IND": "Industry",
            "TRA": "Transport", "AGR": "Agriculture", "PWR": "Power"}
_FUEL_CODES = {"BIO": "Biomass", "NGS": "Natural Gas", "DSL": "Diesel",
               "GSL": "Gasoline", "ELC": "Electricity", "HDG": "Hydrogen",
               "HFO": "Heavy Fuel Oil", "JFL": "Jet Fuel", "LPG": "LPG",
               "RPP": "Refined Petroleum Products", "COA": "Coal"}


# ---------------------------------------------------------------- helpers
def read_input(input_dir: str | Path, name: str) -> pd.DataFrame | None:
    """Read <input_dir>/<name>.csv; None if missing or empty."""
    f = Path(input_dir) / f"{name}.csv"
    if not f.exists():
        return None
    try:
        df = pd.read_csv(f)
    except Exception:
        return None
    return df if not df.empty else None


def _layout(fig, title, ytitle, legend=""):
    fig.update_layout(title=title, xaxis_title="Year", yaxis_title=ytitle,
                      legend_title=legend, template="plotly_white",
                      hovermode="x unified")
    return fig


def _split_sector_fuel(series: pd.Series) -> pd.DataFrame:
    """FUEL code (e.g. INDBIO / RESELCB02) -> Sector, Fuel labels."""
    s = series.astype(str)
    return pd.DataFrame({
        "Sector": s.str[:3].map(_SECTORS).fillna("Other"),
        "Fuel": s.str[3:6].map(_FUEL_CODES).fillna(s.str[3:]),
    }, index=series.index)


# ---------------------------------------------------------------- demand
def plot_demand_by_sector(input_dir: str | Path, scenario: str = None):
    """Prescribed end-use demand by sector (AccumulatedAnnualDemand +
    SpecifiedAnnualDemand). This is an INPUT: the model must meet it."""
    sfx = f" [{scenario}]" if scenario else ""
    parts = [d for d in (read_input(input_dir, "AccumulatedAnnualDemand"),
                         read_input(input_dir, "SpecifiedAnnualDemand"))
             if d is not None]
    if not parts:
        return None
    d = pd.concat(parts)
    d = d.join(_split_sector_fuel(d.FUEL))
    g = d.groupby(["YEAR", "Sector"], as_index=False).VALUE.sum()
    fig = px.area(g, x="YEAR", y="VALUE", color="Sector",
                  color_discrete_map=palette.map_for(g.Sector))
    return _layout(fig, f"Prescribed demand by sector{sfx}", "PJ", "Sector")


def plot_demand_by_fuel(input_dir: str | Path, scenario: str = None):
    """Prescribed demand by END-USE FUEL — the plot that reveals whether fuel
    switching is endogenous. Flat shares over time mean the fuel mix is an
    assumption of the demand projection, not a model result."""
    sfx = f" [{scenario}]" if scenario else ""
    parts = [d for d in (read_input(input_dir, "AccumulatedAnnualDemand"),
                         read_input(input_dir, "SpecifiedAnnualDemand"))
             if d is not None]
    if not parts:
        return None
    d = pd.concat(parts)
    d = d.join(_split_sector_fuel(d.FUEL))
    g = d.groupby(["YEAR", "Fuel"], as_index=False).VALUE.sum()
    fig = px.area(g, x="YEAR", y="VALUE", color="Fuel",
                  color_discrete_map=palette.map_for(g.Fuel))
    return _layout(fig, f"Prescribed demand by end-use fuel{sfx}", "PJ", "Fuel")


def plot_demand_heatmap(input_dir: str | Path, scenario: str = None):
    """Sector x fuel demand matrix for first and last year — shows at a glance
    which sector-fuel combinations are fixed by the projection."""
    sfx = f" [{scenario}]" if scenario else ""
    parts = [d for d in (read_input(input_dir, "AccumulatedAnnualDemand"),
                         read_input(input_dir, "SpecifiedAnnualDemand"))
             if d is not None]
    if not parts:
        return None
    d = pd.concat(parts)
    d = d.join(_split_sector_fuel(d.FUEL))
    y0, y1 = int(d.YEAR.min()), int(d.YEAR.max())
    a = d[d.YEAR == y0].pivot_table(index="Sector", columns="Fuel",
                                    values="VALUE", aggfunc="sum", fill_value=0)
    b = d[d.YEAR == y1].pivot_table(index="Sector", columns="Fuel",
                                    values="VALUE", aggfunc="sum", fill_value=0)
    b = b.reindex(index=a.index, columns=a.columns, fill_value=0)
    delta = (b - a)
    fig = go.Figure(go.Heatmap(z=delta.values, x=list(delta.columns),
                               y=list(delta.index), colorscale="RdBu",
                               zmid=0, colorbar=dict(title="Δ PJ")))
    fig.update_layout(title=f"Demand change {y0} → {y1} by sector × fuel{sfx}",
                      template="plotly_white")
    return fig


def plot_demand_growth_index(input_dir: str | Path, scenario: str = None):
    """Demand indexed to the first year (=100) per fuel. Parallel lines are the
    signature of a proportional projection with no fuel substitution."""
    sfx = f" [{scenario}]" if scenario else ""
    parts = [d for d in (read_input(input_dir, "AccumulatedAnnualDemand"),
                         read_input(input_dir, "SpecifiedAnnualDemand"))
             if d is not None]
    if not parts:
        return None
    d = pd.concat(parts)
    d = d.join(_split_sector_fuel(d.FUEL))
    g = d.groupby(["YEAR", "Fuel"]).VALUE.sum().unstack()
    idx = 100 * g / g.iloc[0]
    fig = go.Figure()
    for fuel in idx.columns:
        fig.add_trace(go.Scatter(x=idx.index, y=idx[fuel], name=fuel,
                                 mode="lines",
                                 line=dict(color=palette.color(fuel))))
    fig.add_hline(y=100, line_dash="dot", line_color="grey")
    return _layout(fig, f"Demand index by fuel ({int(d.YEAR.min())} = 100){sfx}",
                   "index", "Fuel")



def plot_demand_for_sector(input_dir: str | Path, sector: str,
                           scenario: str = None, share: bool = False):
    """End-use fuel mix for ONE sector over time.

    Args:
        sector: 'IND' | 'RES' | 'COM' | 'TRA' | 'AGR' | 'PWR' (or the full
            label, e.g. 'Industry').
        share: True -> plot % shares instead of PJ, which makes fuel
            switching (or its absence) unmistakable.
    """
    sfx = f" [{scenario}]" if scenario else ""
    code = sector.upper()[:3]
    label = _SECTORS.get(code, sector)
    parts = [d for d in (read_input(input_dir, "AccumulatedAnnualDemand"),
                         read_input(input_dir, "SpecifiedAnnualDemand"))
             if d is not None]
    if not parts:
        return None
    d = pd.concat(parts)
    d = d[d.FUEL.astype(str).str.startswith(code)].copy()
    if d.empty:
        return None
    d["Fuel"] = d.FUEL.astype(str).str[3:6].map(_FUEL_CODES).fillna(
        d.FUEL.astype(str).str[3:])
    g = d.groupby(["YEAR", "Fuel"], as_index=False).VALUE.sum()
    ytitle = "PJ"
    if share:
        tot = g.groupby("YEAR").VALUE.transform("sum")
        g["VALUE"] = 100 * g.VALUE / tot
        ytitle = "% of sector demand"
    fig = px.area(g, x="YEAR", y="VALUE", color="Fuel",
                  color_discrete_map=palette.map_for(g.Fuel))
    return _layout(fig, f"{label}: demand by end-use fuel"
                        f"{' (share)' if share else ''}{sfx}", ytitle, "Fuel")


def plot_demand_sector_panels(input_dir: str | Path = None,
                              scenario: str = None,
                              share: bool = False,
                              data: pd.DataFrame = None,
                              cols: int = 2):
    """One panel per sector, stacked bars by end-use fuel (shared legend).

    Design ported from the original `plot_demand.create_demand_plots`, but
    driven by the otoole input CSVs and the shared palette, and without file
    side effects.

    Args:
        input_dir: folder with AccumulatedAnnualDemand.csv / SpecifiedAnnualDemand.csv
        data: alternatively a pre-processed frame with columns
            YEAR, VALUE and either (Sector, Fuel) or (sector, end_use_fuel) —
            supports the legacy datapackage intake.
        share: plot % of sector demand instead of PJ.
    """
    sfx = f" [{scenario}]" if scenario else ""
    d = _demand_frame(input_dir, data)
    if d is None or d.empty:
        return None
    d = d[d.Sector != "Other"]
    g = d.groupby(["YEAR", "Sector", "Fuel"], as_index=False).VALUE.sum()
    if share:
        tot = g.groupby(["YEAR", "Sector"]).VALUE.transform("sum")
        g["VALUE"] = 100 * g.VALUE / tot

    sectors = sorted(g.Sector.unique())
    rows = -(-len(sectors) // cols)
    fig = make_subplots(rows=rows, cols=cols, subplot_titles=sectors,
                        vertical_spacing=0.16, horizontal_spacing=0.09)
    shown = set()
    for i, sector in enumerate(sectors):
        r, c = i // cols + 1, i % cols + 1
        sd = g[g.Sector == sector]
        for fuel in sorted(sd.Fuel.unique()):
            fd = sd[sd.Fuel == fuel]
            fig.add_trace(go.Bar(x=fd.YEAR, y=fd.VALUE, name=fuel,
                                 marker_color=palette.color(fuel),
                                 legendgroup=fuel,
                                 showlegend=fuel not in shown),
                          row=r, col=c)
            shown.add(fuel)
    fig.update_layout(barmode="stack", template="plotly_white",
                      height=320 * rows, legend_title="End-use fuel",
                      title=f"Demand by sector and end-use fuel"
                            f"{' (share)' if share else ''}{sfx}")
    fig.update_yaxes(title_text="% of sector" if share else "PJ", col=1)
    return fig


def plot_fuel_across_sectors(input_dir: str | Path, fuel: str,
                             scenario: str = None):
    """One END-USE FUEL split across sectors — the mirror of
    plot_demand_for_sector. `fuel` is a code ('BIO', 'NGS', 'ELC') or label."""
    sfx = f" [{scenario}]" if scenario else ""
    code = fuel.upper()[:3]
    label = _FUEL_CODES.get(code, fuel)
    parts = [d for d in (read_input(input_dir, "AccumulatedAnnualDemand"),
                         read_input(input_dir, "SpecifiedAnnualDemand"))
             if d is not None]
    if not parts:
        return None
    d = pd.concat(parts)
    d = d[d.FUEL.astype(str).str[3:6] == code].copy()
    if d.empty:
        return None
    d["Sector"] = d.FUEL.astype(str).str[:3].map(_SECTORS).fillna("Other")
    g = d.groupby(["YEAR", "Sector"], as_index=False).VALUE.sum()
    fig = px.area(g, x="YEAR", y="VALUE", color="Sector",
                  color_discrete_map=palette.map_for(g.Sector))
    return _layout(fig, f"{label}: demand across sectors{sfx}", "PJ", "Sector")


def list_sectors_and_fuels(input_dir: str | Path) -> dict:
    """{'sectors': [...], 'fuels': [...]} actually present in the demand files —
    use to drive loops without guessing codes."""
    parts = [d for d in (read_input(input_dir, "AccumulatedAnnualDemand"),
                         read_input(input_dir, "SpecifiedAnnualDemand"))
             if d is not None]
    if not parts:
        return {"sectors": [], "fuels": []}
    f = pd.concat(parts).FUEL.astype(str)
    return {"sectors": sorted({c for c in f.str[:3] if c in _SECTORS}),
            "fuels": sorted({c for c in f.str[3:6] if c in _FUEL_CODES})}



def _demand_frame(input_dir: str | Path = None,
                  data: pd.DataFrame = None) -> pd.DataFrame | None:
    """Normalised demand frame: YEAR, VALUE, Sector, Fuel.

    Accepts either the otoole input CSVs (input_dir) or a pre-processed frame
    (legacy `sector` / `end_use_fuel` columns from the datapackage intake).
    """
    if data is not None:
        d = data.copy()
        if "Sector" not in d.columns and "sector" in d.columns:
            d["Sector"] = d["sector"].map(_SECTORS).fillna(d["sector"])
        if "Fuel" not in d.columns and "end_use_fuel" in d.columns:
            d["Fuel"] = d["end_use_fuel"].map(_FUEL_CODES).fillna(d["end_use_fuel"])
        if "Sector" not in d.columns and "FUEL" in d.columns:
            d = d.join(_split_sector_fuel(d.FUEL))
        return d.dropna(subset=["Sector", "Fuel"]) if "Sector" in d.columns else None
    parts = [x for x in (read_input(input_dir, "AccumulatedAnnualDemand"),
                         read_input(input_dir, "SpecifiedAnnualDemand"))
             if x is not None]
    if not parts:
        return None
    d = pd.concat(parts)
    return d.join(_split_sector_fuel(d.FUEL))


def plot_land_for_power(input_dir: str | Path, scenario: str = None,
                        bc_land_kkm2: float = 944.7):
    """Land demanded for power build-out (FUEL == LND4PWR), with the provincial
    land area as context. Ported from `plot_demand.plot_land_for_power_demand`.
    """
    sfx = f" [{scenario}]" if scenario else ""
    parts = [x for x in (read_input(input_dir, "AccumulatedAnnualDemand"),
                         read_input(input_dir, "SpecifiedAnnualDemand"))
             if x is not None]
    if not parts:
        return None
    d = pd.concat(parts)
    d = d[d.FUEL == "LND4PWR"]
    if d.empty:
        return None
    g = d.groupby("YEAR", as_index=False).VALUE.sum()
    g["pct_of_BC"] = 100 * g.VALUE / bc_land_kkm2
    fig = go.Figure(go.Scatter(x=g.YEAR, y=g.VALUE, mode="lines+markers",
                               name="Land for power",
                               line=dict(color=palette.color("Built-up")),
                               customdata=g.pct_of_BC,
                               hovertemplate="%{y:.2f} kkm² "
                                             "(%{customdata:.3f}% of BC)<extra></extra>"))
    fig.add_annotation(x=g.YEAR.iloc[0], y=g.VALUE.max(), showarrow=False,
                       xanchor="left", font=dict(size=11, color="grey"),
                       text=f"BC land area: {bc_land_kkm2:,.0f} thousand km²")
    return _layout(fig, f"Land demand for power build-out{sfx}",
                   "Thousand km²")


# ---------------------------------------------------------------- bounds
def plot_activity_bounds(input_dir: str | Path, scenario: str = None,
                         prefix: str = None, top: int = 15):
    """Upper / lower activity limits per technology (range bars, final year).

    A technology whose upper and lower limits coincide is fully prescribed;
    a missing upper limit means unconstrained supply — both worth spotting
    before interpreting results. `prefix` filters (e.g. 'RNW', 'PWR', 'LND').
    """
    sfx = f" [{scenario}]" if scenario else ""
    up = read_input(input_dir, "TotalTechnologyAnnualActivityUpperLimit")
    lo = read_input(input_dir, "TotalTechnologyAnnualActivityLowerLimit")
    if up is None and lo is None:
        return None
    yr = max([d.YEAR.max() for d in (up, lo) if d is not None])
    def _slice(d):
        if d is None:
            return pd.Series(dtype=float)
        s = d[d.YEAR == yr]
        if prefix:
            s = s[s.TECHNOLOGY.str.startswith(prefix)]
        return s.groupby("TECHNOLOGY").VALUE.sum()
    u, l = _slice(up), _slice(lo)
    techs = (u.abs().add(l.abs(), fill_value=0)
              .sort_values(ascending=False).head(top).index[::-1])
    if len(techs) == 0:
        return None
    fig = go.Figure()
    fig.add_trace(go.Bar(y=list(techs), x=[u.get(t, 0) for t in techs],
                         name="Upper limit", orientation="h",
                         marker_color="#7FA6BF"))
    fig.add_trace(go.Bar(y=list(techs), x=[l.get(t, 0) for t in techs],
                         name="Lower limit", orientation="h",
                         marker_color="#D9534F"))
    fig.update_layout(barmode="overlay", template="plotly_white",
                      title=f"Activity bounds, {yr}{sfx}",
                      xaxis_title="PJ (or model activity unit)",
                      yaxis_title="", legend_title="")
    fig.update_traces(opacity=0.75)
    return fig


def plot_capacity_bounds(input_dir: str | Path, scenario: str = None,
                         top: int = 15):
    """Residual capacity vs max capacity / max investment (final year) —
    what the model is allowed to build."""
    sfx = f" [{scenario}]" if scenario else ""
    res = read_input(input_dir, "ResidualCapacity")
    mx = read_input(input_dir, "TotalAnnualMaxCapacity")
    inv = read_input(input_dir, "TotalAnnualMaxCapacityInvestment")
    if all(d is None for d in (res, mx, inv)):
        return None
    yr = max([d.YEAR.max() for d in (res, mx, inv) if d is not None])
    def _s(d):
        return (d[d.YEAR == yr].groupby("TECHNOLOGY").VALUE.sum()
                if d is not None else pd.Series(dtype=float))
    r, m, i = _s(res), _s(mx), _s(inv)
    techs = (r.add(m, fill_value=0).add(i, fill_value=0)
              .sort_values(ascending=False).head(top).index[::-1])
    fig = go.Figure()
    for s, name, col in ((r, "Residual capacity", "#9AA5B1"),
                         (m, "Max capacity", "#2F6F8F"),
                         (i, "Max investment/yr", "#7FD4C1")):
        if len(s):
            fig.add_trace(go.Bar(y=list(techs), x=[s.get(t, 0) for t in techs],
                                 name=name, orientation="h", marker_color=col))
    fig.update_layout(barmode="group", template="plotly_white",
                      title=f"Capacity limits, {yr}{sfx}",
                      xaxis_title="GW", yaxis_title="", legend_title="")
    return fig


# ---------------------------------------------------------------- ratios
def plot_efficiency(input_dir: str | Path, scenario: str = None,
                    prefix: str = "PWR", top: int = 20):
    """Conversion efficiency = OutputActivityRatio / InputActivityRatio,
    final year. Values of exactly 1.0 flag pass-through technologies (no real
    conversion) — e.g. the DEM<SEC><FUEL> demand-mapping techs."""
    sfx = f" [{scenario}]" if scenario else ""
    iar = read_input(input_dir, "InputActivityRatio")
    oar = read_input(input_dir, "OutputActivityRatio")
    if iar is None or oar is None:
        return None
    yr = min(iar.YEAR.max(), oar.YEAR.max())
    i = iar[iar.YEAR == yr].groupby("TECHNOLOGY").VALUE.sum()
    o = oar[oar.YEAR == yr].groupby("TECHNOLOGY").VALUE.sum()
    eff = (o / i).replace([float("inf")], pd.NA).dropna()
    if prefix:
        eff = eff[eff.index.str.startswith(prefix)]
    eff = eff.sort_values(ascending=False).head(top)[::-1]
    if eff.empty:
        return None
    colors = ["#D9534F" if abs(v - 1.0) < 1e-9 else "#2F6F8F" for v in eff.values]
    fig = go.Figure(go.Bar(y=list(eff.index), x=eff.values, orientation="h",
                           marker_color=colors))
    fig.add_vline(x=1.0, line_dash="dot", line_color="grey")
    fig.update_layout(template="plotly_white",
                      title=f"Conversion efficiency (OAR/IAR), {yr}{sfx} "
                            f"— red = 1.0, pass-through",
                      xaxis_title="output / input", yaxis_title="")
    return fig


def plot_emission_factors(input_dir: str | Path, scenario: str = None,
                          top: int = 20):
    """EmissionActivityRatio by technology (final year) — which technologies
    the model treats as emitting, and how strongly."""
    sfx = f" [{scenario}]" if scenario else ""
    ear = read_input(input_dir, "EmissionActivityRatio")
    if ear is None:
        return None
    yr = ear.YEAR.max()
    g = (ear[ear.YEAR == yr].groupby("TECHNOLOGY").VALUE.sum()
         .sort_values(ascending=False).head(top)[::-1])
    fig = go.Figure(go.Bar(y=list(g.index), x=g.values, orientation="h",
                           marker_color="#D9534F"))
    fig.update_layout(template="plotly_white",
                      title=f"Emission activity ratio, {yr}{sfx}",
                      xaxis_title="Mt CO2 per PJ activity", yaxis_title="")
    return fig


def plot_costs(input_dir: str | Path, scenario: str = None, top: int = 20):
    """Capital vs fixed vs variable cost by technology (final year) — the
    price signals driving every technology choice in the model."""
    sfx = f" [{scenario}]" if scenario else ""
    cap = read_input(input_dir, "CapitalCost")
    fix = read_input(input_dir, "FixedCost")
    var = read_input(input_dir, "VariableCost")
    if all(d is None for d in (cap, fix, var)):
        return None
    yr = max([d.YEAR.max() for d in (cap, fix, var) if d is not None])
    def _s(d):
        return (d[d.YEAR == yr].groupby("TECHNOLOGY").VALUE.mean()
                if d is not None else pd.Series(dtype=float))
    c, f_, v = _s(cap), _s(fix), _s(var)
    techs = c.sort_values(ascending=False).head(top).index[::-1]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=list(techs), x=[c.get(t, 0) for t in techs],
                         name="Capital ($/GW)", orientation="h",
                         marker_color="#2F6F8F"))
    fig.add_trace(go.Bar(y=list(techs), x=[f_.get(t, 0) for t in techs],
                         name="Fixed O&M", orientation="h",
                         marker_color="#7FA6BF"))
    fig.add_trace(go.Bar(y=list(techs), x=[v.get(t, 0) for t in techs],
                         name="Variable ($/GJ)", orientation="h",
                         marker_color="#B7CEDB"))
    fig.update_layout(barmode="group", template="plotly_white",
                      title=f"Technology costs, {yr}{sfx} "
                            f"(mixed units — compare within a series)",
                      xaxis_title="", yaxis_title="", legend_title="")
    return fig


# ---------------------------------------------------------------- temporal
def plot_capacity_factors(input_dir: str | Path, scenario: str = None,
                          year: int = None):
    """CapacityFactor by technology across timeslices — the temporal shape
    given to VRE and hydro."""
    sfx = f" [{scenario}]" if scenario else ""
    cf = read_input(input_dir, "CapacityFactor")
    if cf is None or "TIMESLICE" not in cf.columns:
        return None
    year = year or int(cf.YEAR.min())
    d = cf[cf.YEAR == year]
    piv = d.pivot_table(index="TECHNOLOGY", columns="TIMESLICE",
                        values="VALUE", aggfunc="mean")
    piv = piv.loc[piv.std(axis=1).sort_values(ascending=False).index[:15]]
    if piv.empty:
        return None
    fig = go.Figure(go.Heatmap(z=piv.values, x=list(piv.columns),
                               y=list(piv.index), colorscale="Viridis",
                               colorbar=dict(title="CF")))
    fig.update_layout(title=f"Capacity factors by timeslice, {year}{sfx}",
                      xaxis_title="Timeslice", template="plotly_white")
    return fig


def plot_demand_profile(input_dir: str | Path, scenario: str = None,
                        year: int = None):
    """SpecifiedDemandProfile — how annual demand is spread across timeslices."""
    sfx = f" [{scenario}]" if scenario else ""
    p = read_input(input_dir, "SpecifiedDemandProfile")
    if p is None:
        return None
    year = year or int(p.YEAR.min())
    d = p[p.YEAR == year]
    fig = px.line(d, x="TIMESLICE", y="VALUE", color="FUEL", markers=True,
                  color_discrete_map=palette.map_for(d.FUEL))
    fig.update_layout(template="plotly_white",
                      title=f"Specified demand profile, {year}{sfx}",
                      xaxis_title="Timeslice", yaxis_title="share of annual demand")
    return fig



# ---------------------------------------------------------------- structure
def plot_sets_summary(input_dir: str | Path, scenario: str = None):
    """Size of every SET — the model's dimensions at a glance
    (technologies, fuels, timeslices, modes, years, storages, emissions)."""
    sfx = f" [{scenario}]" if scenario else ""
    sets = ["TECHNOLOGY", "FUEL", "TIMESLICE", "MODE_OF_OPERATION", "YEAR",
            "STORAGE", "EMISSION", "SEASON", "DAYTYPE", "DAILYTIMEBRACKET",
            "REGION"]
    rows = []
    for name in sets:
        d = read_input(input_dir, name)
        if d is not None:
            rows.append((name, len(d)))
    if not rows:
        return None
    rows.sort(key=lambda r: r[1])
    fig = go.Figure(go.Bar(y=[r[0] for r in rows], x=[r[1] for r in rows],
                           orientation="h", marker_color="#2F6F8F",
                           text=[r[1] for r in rows], textposition="outside"))
    fig.update_layout(template="plotly_white", title=f"Model sets{sfx}",
                      xaxis_title="number of elements", yaxis_title="")
    return fig


def plot_model_structure(input_dir: str | Path, scenario: str = None,
                         min_ratio: float = 0.0, year: int = None):
    """Fuel → technology → fuel network from IAR/OAR (Sankey).

    This *is* the model's reference energy system: what each technology
    consumes and produces. Useful for spotting orphan fuels, pass-through
    chains and missing links before trusting any result.
    """
    sfx = f" [{scenario}]" if scenario else ""
    iar = read_input(input_dir, "InputActivityRatio")
    oar = read_input(input_dir, "OutputActivityRatio")
    if iar is None or oar is None:
        return None
    year = year or int(min(iar.YEAR.max(), oar.YEAR.max()))
    i = (iar[iar.YEAR == year].groupby(["FUEL", "TECHNOLOGY"]).VALUE.sum()
         .reset_index())
    o = (oar[oar.YEAR == year].groupby(["TECHNOLOGY", "FUEL"]).VALUE.sum()
         .reset_index())
    i = i[i.VALUE > min_ratio]
    o = o[o.VALUE > min_ratio]
    if i.empty and o.empty:
        return None
    nodes = sorted(set(i.FUEL) | set(i.TECHNOLOGY) | set(o.TECHNOLOGY) | set(o.FUEL))
    idx = {n: k for k, n in enumerate(nodes)}
    src = [idx[f] for f in i.FUEL] + [idx[t] for t in o.TECHNOLOGY]
    tgt = [idx[t] for t in i.TECHNOLOGY] + [idx[f] for f in o.FUEL]
    val = list(i.VALUE) + list(o.VALUE)
    fig = go.Figure(go.Sankey(
        node=dict(label=nodes, pad=10, thickness=11,
                  color=[palette.color(n) for n in nodes]),
        link=dict(source=src, target=tgt, value=val,
                  color="rgba(150,165,180,.30)")))
    fig.update_layout(
        template="plotly_white", height=860,
        margin=dict(t=70, b=40, l=20, r=20),
        title=dict(text=f"Reference energy system · {year}{sfx}<br>"
                        f"<span style='font-size:12px;color:#64748b'>"
                        f"fuel → technology → fuel, from InputActivityRatio / "
                        f"OutputActivityRatio (structure, not flows)</span>",
                   x=0.01, xanchor="left"),
        font=dict(size=11))
    fig.update_traces(node=dict(pad=22, thickness=13,
                                line=dict(color="rgba(0,0,0,.10)", width=0.5)),
                      textfont=dict(size=10.5),
                      selector=dict(type="sankey"))
    return fig


# ---------------------------------------------------------------- storage
def plot_storage_params(input_dir: str | Path, scenario: str = None):
    """Storage inputs: residual capacity, capital cost and operational life."""
    sfx = f" [{scenario}]" if scenario else ""
    res = read_input(input_dir, "ResidualStorageCapacity")
    cc = read_input(input_dir, "CapitalCostStorage")
    ol = read_input(input_dir, "OperationalLifeStorage")
    frames = {"Residual capacity": res, "Capital cost": cc,
              "Operational life": ol}
    have = {k: v for k, v in frames.items() if v is not None}
    if not have:
        return None
    fig = make_subplots(rows=1, cols=len(have), subplot_titles=list(have))
    for c, (name, d) in enumerate(have.items(), start=1):
        key = "STORAGE" if "STORAGE" in d.columns else d.columns[1]
        g = (d[d.YEAR == d.YEAR.max()] if "YEAR" in d.columns else d)
        g = g.groupby(key).VALUE.mean().sort_values()
        fig.add_trace(go.Bar(y=list(g.index), x=g.values, orientation="h",
                             marker_color="#7FD4C1", showlegend=False),
                      row=1, col=c)
    fig.update_layout(template="plotly_white", height=340,
                      title=f"Storage parameters{sfx}")
    return fig


# ---------------------------------------------------------------- temporal
def plot_year_split(input_dir: str | Path, scenario: str = None):
    """YearSplit — the fraction of the year each timeslice represents.
    Uneven splits are fine; they must sum to 1.0 per year (shown in the title)."""
    sfx = f" [{scenario}]" if scenario else ""
    d = read_input(input_dir, "YearSplit")
    if d is None:
        return None
    yr = int(d.YEAR.min())
    g = d[d.YEAR == yr].groupby("TIMESLICE").VALUE.sum()
    total = g.sum()
    fig = go.Figure(go.Bar(x=list(g.index), y=g.values,
                           marker_color="#5B7DB1"))
    fig.update_layout(template="plotly_white",
                      title=f"Year split, {yr}{sfx} — sums to {total:.4f}",
                      xaxis_title="Timeslice", yaxis_title="fraction of year")
    return fig


def plot_availability_factors(input_dir: str | Path, scenario: str = None):
    """AvailabilityFactor by technology (annual maximum availability)."""
    sfx = f" [{scenario}]" if scenario else ""
    d = read_input(input_dir, "AvailabilityFactor")
    if d is None:
        return None
    yr = d.YEAR.max()
    g = (d[d.YEAR == yr].groupby("TECHNOLOGY").VALUE.mean()
         .sort_values().tail(25))
    fig = go.Figure(go.Bar(y=list(g.index), x=g.values, orientation="h",
                           marker_color="#7FA6BF"))
    fig.update_layout(template="plotly_white",
                      title=f"Availability factor, {yr}{sfx}",
                      xaxis_title="fraction", yaxis_title="")
    return fig


# ---------------------------------------------------------------- policy
def plot_emission_policy(input_dir: str | Path, scenario: str = None):
    """Emission limits and penalties — the climate policy given to the model."""
    sfx = f" [{scenario}]" if scenario else ""
    lim = read_input(input_dir, "AnnualEmissionLimit")
    pen = read_input(input_dir, "EmissionsPenalty")
    if lim is None and pen is None:
        return None
    fig = go.Figure()
    if lim is not None:
        g = lim.groupby("YEAR", as_index=False).VALUE.sum()
        g = g[g.VALUE < 900]           # 999 = non-binding placeholder
        if not g.empty:
            fig.add_trace(go.Scatter(x=g.YEAR, y=g.VALUE, name="Emission limit",
                                     mode="lines+markers",
                                     line=dict(color="#D9534F")))
    if pen is not None:
        g = pen.groupby("YEAR", as_index=False).VALUE.mean()
        if g.VALUE.abs().sum() > 0:
            fig.add_trace(go.Scatter(x=g.YEAR, y=g.VALUE, name="Emission penalty",
                                     mode="lines+markers", yaxis="y2",
                                     line=dict(color="#B26A00", dash="dot")))
            fig.update_layout(yaxis2=dict(title="penalty (M$/Mt)",
                                          overlaying="y", side="right",
                                          showgrid=False))
    if not fig.data:
        return None
    return _layout(fig, f"Emission policy inputs{sfx}", "Mt CO2e limit")


def plot_operational_life(input_dir: str | Path, scenario: str = None,
                          prefix: str = "PWR"):
    """OperationalLife by technology — drives retirement and rebuild timing."""
    sfx = f" [{scenario}]" if scenario else ""
    d = read_input(input_dir, "OperationalLife")
    if d is None:
        return None
    g = d.groupby("TECHNOLOGY").VALUE.mean()
    if prefix:
        g = g[g.index.str.startswith(prefix)]
    g = g.sort_values().tail(25)
    if g.empty:
        return None
    fig = go.Figure(go.Bar(y=list(g.index), x=g.values, orientation="h",
                           marker_color="#8F7FB0"))
    fig.update_layout(template="plotly_white",
                      title=f"Operational life{sfx}",
                      xaxis_title="years", yaxis_title="")
    return fig


def plot_discount_and_reserve(input_dir: str | Path, scenario: str = None):
    """Scalar-ish policy inputs: discount rate and reserve margin over time."""
    sfx = f" [{scenario}]" if scenario else ""
    dr = read_input(input_dir, "DiscountRate")
    rm = read_input(input_dir, "ReserveMargin")
    if dr is None and rm is None:
        return None
    fig = go.Figure()
    if dr is not None:
        g = dr.groupby("YEAR", as_index=False).VALUE.mean() if "YEAR" in dr.columns \
            else pd.DataFrame({"YEAR": [0], "VALUE": [dr.VALUE.mean()]})
        fig.add_trace(go.Scatter(x=g.YEAR, y=g.VALUE, name="Discount rate",
                                 mode="lines+markers", line=dict(color="#2F6F8F")))
    if rm is not None and "YEAR" in rm.columns:
        g = rm.groupby("YEAR", as_index=False).VALUE.mean()
        fig.add_trace(go.Scatter(x=g.YEAR, y=g.VALUE, name="Reserve margin",
                                 mode="lines+markers", line=dict(color="#C7A76C")))
    if not fig.data:
        return None
    return _layout(fig, f"Discount rate and reserve margin{sfx}", "value")


# ---------------------------------------------------------------- land / water
def plot_land_availability(input_dir: str | Path, scenario: str = None):
    """Land available per agricultural cluster (activity upper limit on
    LNDAGR* technologies) — the land ceiling the optimiser works within."""
    sfx = f" [{scenario}]" if scenario else ""
    up = read_input(input_dir, "TotalTechnologyAnnualActivityUpperLimit")
    if up is None:
        return None
    d = up[up.TECHNOLOGY.str.startswith("LNDAGR")]
    if d.empty:
        return None
    d = d.copy()
    d["Cluster"] = d.TECHNOLOGY.str.extract(r"(C\d+)$")
    g = d.dropna(subset=["Cluster"]).groupby(["YEAR", "Cluster"],
                                             as_index=False).VALUE.sum()
    fig = px.area(g, x="YEAR", y="VALUE", color="Cluster",
                  color_discrete_map=palette.map_for(g.Cluster))
    return _layout(fig, f"Land availability by cluster{sfx}",
                   "Thousand km²", "Cluster")


def plot_water_inputs(input_dir: str | Path, scenario: str = None):
    """Water requirement per unit activity (IAR on WTR*/AGRWAT fuels) —
    the coefficients that drive every water result."""
    sfx = f" [{scenario}]" if scenario else ""
    iar = read_input(input_dir, "InputActivityRatio")
    if iar is None:
        return None
    d = iar[iar.FUEL.astype(str).str.contains("WAT|WTR", regex=True)]
    if d.empty:
        return None
    yr = d.YEAR.max()
    g = (d[d.YEAR == yr].groupby(["TECHNOLOGY", "FUEL"]).VALUE.mean()
         .reset_index().sort_values("VALUE", ascending=False).head(25))
    fig = px.bar(g, x="VALUE", y="TECHNOLOGY", color="FUEL", orientation="h",
                 color_discrete_map=palette.map_for(g.FUEL))
    fig.update_layout(template="plotly_white",
                      title=f"Water input ratios, {yr}{sfx}",
                      xaxis_title="water per unit activity", yaxis_title="")
    return fig


# ---------------------------------------------------------------- convenience
def build_input_plots(input_dir: str | Path, scenario: str = None) -> dict:
    """{plot_name: figure} for every input plot — feed straight into the
    report as an extra tab: nexus_plots['Inputs'] = build_input_plots(...)."""
    fns = {
        "demand_by_sector": plot_demand_by_sector,
        "demand_by_fuel": plot_demand_by_fuel,
        "demand_sector_panels": plot_demand_sector_panels,
        "land_for_power": plot_land_for_power,
        "demand_growth_index": plot_demand_growth_index,
        "demand_sector_fuel_change": plot_demand_heatmap,
        "demand_profile": plot_demand_profile,
        "activity_bounds": plot_activity_bounds,
        "capacity_bounds": plot_capacity_bounds,
        "efficiency_oar_iar": plot_efficiency,
        "emission_factors": plot_emission_factors,
        "technology_costs": plot_costs,
        "capacity_factors": plot_capacity_factors,
        "year_split": plot_year_split,
        "availability_factors": plot_availability_factors,
        "operational_life": plot_operational_life,
        "storage_parameters": plot_storage_params,
        "emission_policy": plot_emission_policy,
        "discount_reserve": plot_discount_and_reserve,
        "land_availability": plot_land_availability,
        "water_input_ratios": plot_water_inputs,
        "model_sets": plot_sets_summary,
    }
    out = {}
    for name, fn in fns.items():
        try:
            out[name] = fn(input_dir, scenario=scenario)
        except Exception as e:
            print(f"  skipped {name}: {type(e).__name__}: {e}")
            out[name] = None

    # one figure per sector present in the demand files
    found = list_sectors_and_fuels(input_dir)
    for code in found["sectors"]:
        label = _SECTORS.get(code, code).lower()
        try:
            out[f"demand_{label}"] = plot_demand_for_sector(
                input_dir, code, scenario=scenario)
        except Exception as e:
            print(f"  skipped demand_{label}: {type(e).__name__}: {e}")
            out[f"demand_{label}"] = None
    return out
