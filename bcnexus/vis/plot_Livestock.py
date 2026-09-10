"""Livestock figures for the BC Nexus CLEWs model.

Every figure is a single call from the notebook and returns a plotly figure,
or None when the input frame holds no matching rows - the same contract as
plot_Land.py. ``livestock_figures()`` runs all of them in one call.

The livestock chain, for reading the technology names below:

    LNDLVS{pw}BC1   LBC1 -> LLVS{pw}BC1        land tier, thousand sq km
    LNDAGRBC1C{cc}  LLVS{pw}BC1 -> LVS{pw}BC1  cluster allocation
    LVSHRD{pw}BC1   LVS{pw}BC1 -> HRD{pw}      herd, thousand head
    LVS{pw}BC1      HRD{pw} -> LVS{produce}    product, kt

Note the three technologies whose names all begin LVS or LNDLVS. Matching them
by regex is how you accidentally sum the herd into the product; the maps below
are built explicitly from model_structure.LivestockPathways instead.
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from bcnexus.clews import model_structure as ms
from bcnexus.vis import palette

REGION_LAND = ms.LandRegions[0]

# ---------------------------------------------------------------- units
_AREA_UNIT = "Thousand Square Km"
_PRODUCT_UNIT = "kt"
_HERD_UNIT = "Thousand head"

# Emission unit. model_structure.units['emission'] says "Million Tonnes of
# CO2", but the factors are t CO2e per head against an activity in thousand
# head, which yields kt CO2e - the CH4 total of ~1048 is 1.05 Mt CO2e, the
# right order for BC enteric fermentation. The axis is labelled for what the
# numbers actually are. If the unit question is ever settled in favour of Mt,
# change this one constant rather than each figure.
_EMISSION_UNIT = "kt CO2e"

# ---------------------------------------------------------------- labels
# Pathway -> readable label, straight from the model structure so a new
# pathway shows up in the figures without touching this file.
_PATHWAY_LABELS = {pw: attrs["label"]
                   for pw, attrs in ms.LivestockPathways.items()}

_SOIL_N2O_LABELS = {"N2O_DIR": "Soil N2O, direct",
                    "N2O_IND": "Soil N2O, indirect"}

# Exact technology names, never prefixes.
_LAND_TECH = {f"LNDLVS{pw}{REGION_LAND}": pw for pw in ms.LivestockPathways}
_HERD_TECH = {f"LVSHRD{pw}{REGION_LAND}": pw for pw in ms.LivestockPathways}
_PROD_TECH = {f"LVS{pw}{REGION_LAND}": pw for pw in ms.LivestockPathways}

# Product fuel -> readable label, for the commodity view.
_PRODUCE_LABELS = {f"LVS{code}": name
                   for code, name in ms.LivestockProduce.items()}

# Draw order: heaviest land users first so the stack reads top-down.
_ORDER = list(ms.LivestockPathways)


# ---------------------------------------------------------------- helpers
def _layout(fig, title, ytitle, legend_title=""):
    fig.update_layout(title=title, xaxis_title="Year", yaxis_title=ytitle,
                      legend_title=legend_title, template="plotly_white",
                      hovermode="x unified")
    return fig


def _sfx(scenario):
    return f" [{scenario}]" if scenario else ""


def _ordered(pivot):
    """Columns in pathway order, then anything else alphabetically."""
    known = [_PATHWAY_LABELS[pw] for pw in _ORDER
             if _PATHWAY_LABELS[pw] in pivot.columns]
    rest = sorted(c for c in pivot.columns if c not in known)
    return known + rest


def _stacked_area(pivot, order=None):
    fig = go.Figure()
    for col in (order or _ordered(pivot)):
        if col not in pivot.columns:
            continue
        fig.add_trace(go.Scatter(x=pivot.index, y=pivot[col], name=str(col),
                                 stackgroup="one", mode="lines",
                                 line=dict(color=palette.color(col)),
                                 fillcolor=palette.color(col)))
    return fig


def _by_pathway(df, tech_map, value="VALUE"):
    """Filter to the given technologies and label rows by pathway.

    Returns None when nothing matches, so a figure can bail out early rather
    than render an empty axis that looks like a zero result.
    """
    if df is None or df.empty or "TECHNOLOGY" not in df.columns:
        return None
    d = df[df.TECHNOLOGY.isin(tech_map)].copy()
    if d.empty:
        return None
    d["Animal"] = d.TECHNOLOGY.map(tech_map).map(_PATHWAY_LABELS)
    return d


def _pivot_years(d, column="Animal"):
    g = d.groupby(["YEAR", column], as_index=False).VALUE.sum()
    return g.pivot(index="YEAR", columns=column, values="VALUE").fillna(0)


# ---------------------------------------------------------------- figures
def plot_livestock_land(prod: pd.DataFrame, scenario: str = None):
    """Land occupied per animal type.

    Input: ProductionByTechnologyAnnual. Reads the land-tier technologies
    LNDLVS{pw}BC1, whose activity is the area drawn from the regional land
    pool before any cluster places it.
    """
    d = _by_pathway(prod, _LAND_TECH)
    if d is None:
        return None
    pivot = _pivot_years(d)
    fig = _stacked_area(pivot)
    return _layout(fig, f"Livestock land use by animal{_sfx(scenario)}",
                   _AREA_UNIT, "Animal")


def plot_livestock_production(prod: pd.DataFrame, scenario: str = None,
                              demand: pd.DataFrame = None):
    """Commodity output per animal type, against demand if supplied.

    Input: ProductionByTechnologyAnnual, and optionally
    AccumulatedAnnualDemand for the reference line.

    Demand is a floor, not a target, so production sitting above it is legal.
    The gap is the thing to look at: crop output in this model runs well over
    demand because it is a costless by-product of land allocation, and the
    same question is worth asking of livestock.
    """
    d = _by_pathway(prod, _PROD_TECH)
    if d is None:
        return None
    pivot = _pivot_years(d)
    fig = _stacked_area(pivot)

    if demand is not None and not demand.empty and "FUEL" in demand.columns:
        dem = demand[demand.FUEL.isin(_PRODUCE_LABELS)]
        if not dem.empty:
            total = dem.groupby("YEAR", as_index=False).VALUE.sum()
            fig.add_trace(go.Scatter(
                x=total.YEAR, y=total.VALUE, name="Demand (floor)",
                mode="lines", line=dict(color="#444444", dash="dash", width=2)))

    return _layout(fig, f"Livestock production by animal{_sfx(scenario)}",
                   _PRODUCT_UNIT, "Animal")


def plot_livestock_n2o(emis: pd.DataFrame, scenario: str = None,
                       with_soil: bool = True):
    """Nitrous oxide from manure management, per animal type.

    Input: AnnualTechnologyEmission.

    N2O_MAN is the only N2O livestock emits. When ``with_soil`` is set, the
    agricultural soil N2O (N2O_DIR + N2O_IND, from the crop modes on the
    LNDAGR cluster technologies) is drawn as a reference line, because it is
    roughly ten times larger and manure N2O is easy to over-read on its own
    axis.
    """
    if emis is None or emis.empty or "EMISSION" not in emis.columns:
        return None
    d = _by_pathway(emis[emis.EMISSION == "N2O_MAN"], _PROD_TECH)
    if d is None:
        return None
    pivot = _pivot_years(d)
    fig = _stacked_area(pivot)

    if with_soil:
        soil = emis[emis.EMISSION.isin(_SOIL_N2O_LABELS)]
        if not soil.empty:
            total = soil.groupby("YEAR", as_index=False).VALUE.sum()
            fig.add_trace(go.Scatter(
                x=total.YEAR, y=total.VALUE, name="Agricultural soil N2O",
                mode="lines", line=dict(color="#8A6D3B", dash="dot", width=2)))

    return _layout(fig, f"Livestock N2O (manure management){_sfx(scenario)}",
                   _EMISSION_UNIT, "Animal")


def plot_livestock_ch4(emis: pd.DataFrame, scenario: str = None):
    """Methane per animal type, split into enteric fermentation and manure.

    Input: AnnualTechnologyEmission.

    Two panels on a shared y-axis rather than one stack of ten series: the
    split is the analytically interesting part. Enteric fermentation
    dominates for ruminants and manure for swine, and that contrast is
    invisible once the two are summed.
    """
    if emis is None or emis.empty or "EMISSION" not in emis.columns:
        return None

    panels = [("CH4_FER", "Enteric fermentation"), ("CH4_MAN", "Manure management")]
    frames = {}
    for code, title in panels:
        d = _by_pathway(emis[emis.EMISSION == code], _PROD_TECH)
        if d is not None:
            frames[code] = _pivot_years(d)
    if not frames:
        return None

    fig = make_subplots(rows=1, cols=2, shared_yaxes=True,
                        subplot_titles=[t for _, t in panels])

    for col, (code, _title) in enumerate(panels, start=1):
        pivot = frames.get(code)
        if pivot is None:
            continue
        for name in _ordered(pivot):
            fig.add_trace(go.Scatter(
                x=pivot.index, y=pivot[name], name=str(name),
                stackgroup=f"s{col}", mode="lines",
                legendgroup=str(name), showlegend=(col == 1),
                line=dict(color=palette.color(name)),
                fillcolor=palette.color(name)), row=1, col=col)

    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_xaxes(title_text="Year", row=1, col=2)
    fig.update_yaxes(title_text=_EMISSION_UNIT, row=1, col=1)
    fig.update_layout(title=f"Livestock CH4 by source{_sfx(scenario)}",
                      legend_title="Animal", template="plotly_white",
                      hovermode="x unified")
    return fig


# ---------------------------------------------------------------- one call
DEFAULT_INPUT_DIR = "data/clews_data/clews_build_data/input_csvs"

FIGURES = ("land", "production", "n2o", "ch4")


def livestock_figures(result_pack, scenario: str = None, show: bool = True,
                      input_dir: str | Path = DEFAULT_INPUT_DIR) -> dict:
    """Build every livestock figure in one call.

    Notebook usage::

        from bcnexus.vis import plot_Livestock as Vvis
        figs = Vvis.livestock_figures(result_pack, scene)

    Returns ``{name: figure}`` keyed by FIGURES, omitting any figure whose
    input frame held no matching rows. With ``show=True`` each is displayed as
    it is built, so the single call is enough on its own; keep the return
    value only if you want to restyle or export them.

    ``input_dir`` supplies AccumulatedAnnualDemand for the production
    reference line. A missing file is not an error - the line is simply
    dropped, since the figures are about results, not inputs.
    """
    prod = result_pack.get_df("ProductionByTechnologyAnnual")
    emis = result_pack.get_df("AnnualTechnologyEmission")

    demand = None
    demand_file = Path(input_dir) / "AccumulatedAnnualDemand.csv"
    if demand_file.exists():
        try:
            demand = pd.read_csv(demand_file)
        except Exception:
            demand = None

    figs = {
        "land": plot_livestock_land(prod, scenario),
        "production": plot_livestock_production(prod, scenario, demand=demand),
        "n2o": plot_livestock_n2o(emis, scenario),
        "ch4": plot_livestock_ch4(emis, scenario),
    }
    figs = {k: v for k, v in figs.items() if v is not None}

    missing = [k for k in FIGURES if k not in figs]
    if missing:
        print(f"no rows for: {', '.join(missing)} "
              f"(checked ProductionByTechnologyAnnual and "
              f"AnnualTechnologyEmission)")

    if show:
        for fig in figs.values():
            fig.show()

    return figs
