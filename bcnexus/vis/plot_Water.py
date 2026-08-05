"""
Water-dimension plots for BCNexus (the W in CLEW).

Author: Md Eliasinul Islam

Data sources (otoole result CSVs):
- ProductionByTechnologyAnnual : WTR*/AGRWAT/PUBWAT/PWRWAT fuel flows
- StorageLevelYearStart        : reservoir levels (STORAGE column)
- UseByTechnology              : water consumers (optional detail)
All water volumes in BCM (model convention); verify against otoole config.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from bcnexus.vis import palette

_SUPPLY = {"WTRPRC": "Precipitation", "WTRSUR": "Surface water",
           "WTRGRC": "Groundwater recharge"}
_USE = {"WTREVT": "Evapotranspiration", "AGRWAT": "Agriculture",
        "PUBWAT": "Public supply", "PWRWAT": "Power sector"}


def _layout(fig, title, ytitle, legend=""):
    fig.update_layout(title=title, xaxis_title="Year", yaxis_title=ytitle,
                      legend_title=legend, template="plotly_white",
                      hovermode="x unified")
    return fig


def _annual_by_prefix(prod: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    rows = []
    for pref, label in mapping.items():
        s = prod[prod.FUEL.str.startswith(pref)]
        if not s.empty:
            g = s.groupby("YEAR", as_index=False).VALUE.sum()
            g["Flow"] = label
            rows.append(g)
    return pd.concat(rows) if rows else pd.DataFrame(columns=["YEAR", "VALUE", "Flow"])


def plot_water_balance(prod: pd.DataFrame, scenario: str = None):
    """Supply (positive) vs use (negative) stacked — the closure view.

    If supply and use don't roughly mirror, either the model has slack
    water (fine) or an accounting gap (not fine).
    """
    sfx = f" [{scenario}]" if scenario else ""
    sup = _annual_by_prefix(prod, _SUPPLY)
    use = _annual_by_prefix(prod, _USE)
    if sup.empty and use.empty:
        return None
    fig = go.Figure()
    for flow, d in sup.groupby("Flow"):
        fig.add_trace(go.Bar(x=d.YEAR, y=d.VALUE, name=f"{flow} (supply)",
                             marker_color=palette.color(flow)))
    for flow, d in use.groupby("Flow"):
        fig.add_trace(go.Bar(x=d.YEAR, y=-d.VALUE, name=f"{flow} (use)",
                             marker_color=palette.color(flow)))
    fig.update_layout(barmode="relative")
    fig.add_hline(y=0, line_width=1, line_color="grey")
    return _layout(fig, f"Water balance: supply vs use{sfx}", "BCM (use shown negative)")


def plot_water_use_by_purpose(prod: pd.DataFrame, scenario: str = None):
    """Withdrawals by purpose over time (excl. natural ET) — the demand view."""
    sfx = f" [{scenario}]" if scenario else ""
    use = _annual_by_prefix(prod, {k: v for k, v in _USE.items()
                                   if k != "WTREVT"})
    if use.empty:
        return None
    fig = px.area(use, x="YEAR", y="VALUE", color="Flow",
                  color_discrete_map=palette.map_for(use.Flow),
                  title=f"Water withdrawals by purpose{sfx}")
    return _layout(fig, f"Water withdrawals by purpose{sfx}", "BCM", "Purpose")


def plot_reservoir_levels(storage_level: pd.DataFrame, scenario: str = None):
    """Reservoir / storage level at year start, per storage asset.

    Input: StorageLevelYearStart (REGION, STORAGE, YEAR, VALUE). A drifting
    hydro reservoir level signals systematic over/under-use of inflows.
    """
    sfx = f" [{scenario}]" if scenario else ""
    d = storage_level[storage_level.STORAGE.str.contains(
        "HYDRO|WATER|DAM", case=False, na=False)]
    if d.empty:
        d = storage_level  # fall back to all storages
    if d.empty:
        return None
    fig = px.line(d, x="YEAR", y="VALUE", color="STORAGE", markers=True,
                  title=f"Storage level at year start{sfx}")
    return _layout(fig, f"Storage level at year start{sfx}",
                   "Storage units (model convention)", "Storage")


def plot_hydro_water_energy(prod: pd.DataFrame,
                            storage_level: pd.DataFrame = None,
                            scenario: str = None):
    """Hydro generation vs reservoir state — the water-energy coupling.

    Bars: annual generation from PWRHYD* (PJ, left axis). Line: total
    hydro/water storage level at year start (right axis), if provided.
    """
    sfx = f" [{scenario}]" if scenario else ""
    hyd = prod[(prod.FUEL == "ELCB01") &
               prod.TECHNOLOGY.str.startswith("PWRHYD")]
    if hyd.empty:
        return None
    g = hyd.groupby("YEAR", as_index=False).VALUE.sum()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=g.YEAR, y=g.VALUE, name="Hydro generation (PJ)",
                         marker_color=palette.color("Hydro")))
    if storage_level is not None:
        s = storage_level[storage_level.STORAGE.str.contains(
            "HYDRO|WATER|DAM", case=False, na=False)]
        if not s.empty:
            sl = s.groupby("YEAR", as_index=False).VALUE.sum()
            fig.add_trace(go.Scatter(x=sl.YEAR, y=sl.VALUE,
                                     name="Reservoir level (year start)",
                                     mode="lines+markers", yaxis="y2",
                                     line=dict(dash="dot")))
            fig.update_layout(yaxis2=dict(title="Storage level",
                                          overlaying="y", side="right",
                                          showgrid=False))
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                  xanchor="left", x=0))
    return _layout(fig, f"Hydro generation vs reservoir state{sfx}", "PJ")
