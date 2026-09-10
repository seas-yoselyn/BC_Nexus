from functools import lru_cache
from pathlib import Path

from plotly.subplots import make_subplots

from bcnexus import constants as bcnexus_const
from bcnexus.clews import model_structure
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
from bcnexus.vis import palette
import numpy as np
from bcnexus import utils

def add_inventory_emission_traces(AnnualEmissions_fig: go.Figure) -> None:
    years=bcnexus_const.emission_inventory.get('years')
    emissions_MTeCO2=bcnexus_const.emission_inventory.get("emissions_MTeCO2")
    
    AnnualEmissions_fig.add_trace(go.Scatter(
        x=years,
        y=emissions_MTeCO2,
        mode='markers',
        marker=dict(
            size=9,
            color='blue',
            opacity=0.5,
            line=dict(width=1, color='blue')
        ),
        # textposition="top center",
        # text=["2021 actual", "2022 actual", "2023 actual"],  # Text labels
        name="BC Emission Inventory Report"  # Legend name
    ))
    AnnualEmissions_fig_with_inventory_traces=AnnualEmissions_fig
    return AnnualEmissions_fig_with_inventory_traces


def add_emission_target_traces(AnnualEmissions_fig: go.Figure) -> None:
    years=bcnexus_const.emission_targets.get('years')
    emissions_MTeCO2=bcnexus_const.emission_targets.get("emissions_MTeCO2")

    AnnualEmissions_fig.add_trace(go.Scatter(
        x=years,
        y=emissions_MTeCO2,
        mode='markers+text',
        marker=dict(
            size=12,
            color='yellow',
            opacity=0.7,
            line=dict(width=1, color='orange')
        ),
        text=["2030 Target", "2040 Target", "2050 Target"],  # Text labels
        textposition="top center",
        name="BC Emission Targets"  # Legend name
    ))
    AnnualEmissions_fig_with_target_traces=AnnualEmissions_fig
    return AnnualEmissions_fig_with_target_traces


def add_emission_plot_helper_columns(AnnualTechnologyEmission:pd.DataFrame):
    
    AnnualTechnologyEmission['sector'] = np.where(
        AnnualTechnologyEmission['TECHNOLOGY'].str.contains("CCS"),
        None,
        AnnualTechnologyEmission['TECHNOLOGY'].str[3:6]
    )
    AnnualTechnologyEmission['end_use_fuel']= np.where(
        AnnualTechnologyEmission['TECHNOLOGY'].str.contains("CCS"),
        None,
        AnnualTechnologyEmission['TECHNOLOGY'].str[6:9])

    AnnualTechnologyEmission['end_use_fuel_label'] = AnnualTechnologyEmission['end_use_fuel'].map(model_structure.NamingConvention)
    AnnualTechnologyEmission['sector_label'] = AnnualTechnologyEmission['sector'].map(model_structure.NamingConvention)
    return AnnualTechnologyEmission

def get_total_annual_emission(AnnualEmissions:pd.DataFrame,scenario:str):
    if AnnualEmissions is not None:
        df=AnnualEmissions
        AnnualEmissions_fig = px.line(df, x='YEAR', y=df.columns[-1], title=f'Emission Trends [{scenario}]', markers=False)
        AnnualEmissions_fig.update_traces(
            line_color='red',  # Set line color to red
            opacity=0.9        # Set opacity to 70%
        )
        AnnualEmissions_fig.update_xaxes(title_text='Year')
        AnnualEmissions_fig.update_yaxes(title_text=bcnexus_const.units_mapping.get("emissions","Million Tonnes of CO2"))

        AnnualEmissions_fig_with_target_traces=add_emission_target_traces(AnnualEmissions_fig)
        AnnualEmissions_fig_with_all_traces=add_inventory_emission_traces(AnnualEmissions_fig_with_target_traces)
        
        return AnnualEmissions_fig_with_all_traces
    else:
        utils.print_update(level=2,message=f"AnnualEmissions Data empty for {scenario}")

def get_emission_from_fuels(AnnualTechnologyEmission: pd.DataFrame,scenario:str):
    if AnnualTechnologyEmission is not None:
        if 'end_use_fuel_label' not in AnnualTechnologyEmission.columns or 'sector_label' not in AnnualTechnologyEmission.columns:
            AnnualTechnologyEmission = add_emission_plot_helper_columns(AnnualTechnologyEmission)
        
        # Group by YEAR and end_use_fuel, summing the VALUE column
        grouped_data = AnnualTechnologyEmission.groupby(['YEAR', 'end_use_fuel','end_use_fuel_label'], as_index=False)['VALUE'].sum()

        # Create the plot
        fig = px.bar(
            grouped_data,
            x='YEAR',
            y='VALUE',
            color='end_use_fuel_label',
            title=f'Annual Technology Emissions by End Use Fuel [{scenario}]',
            labels={'VALUE': 'Emissions (Million Tonnes of CO2)', 'YEAR': 'Year', 'end_use_fuel_label': 'End Use Fuel'}
        )

        return fig
    else:
        utils.print_update(level=2,message=f"AnnualTechnologyEmission Data empty for {scenario}")


# ---------------------------------------------------------------- helpers (new)
_SECTOR_LABELS = {"RES": "Residential", "COM": "Commercial", "IND": "Industry",
                  "TRA": "Transport", "PWR": "Power", "AGR": "Agriculture"}

def _sector_of(tech: str) -> str:
    if "CCS" in tech:
        return "CCS"
    return _SECTOR_LABELS.get(tech[3:6], tech[3:6])


def plot_cumulative_emissions(AnnualEmissions: pd.DataFrame, scenario: str = None,
                              budget_Mt: float = None):
    """Cumulative net emissions over the horizon; optional carbon-budget line.

    Climate outcome is a stock, not a flow — this is the budget view.
    Input: AnnualEmissions.
    """
    sfx = f" [{scenario}]" if scenario else ""
    g = AnnualEmissions.groupby("YEAR", as_index=False).VALUE.sum()
    g["CUM"] = g.VALUE.cumsum()
    fig = px.area(g, x="YEAR", y="CUM",
                  title=f"Cumulative net emissions{sfx}")
    if budget_Mt is not None:
        fig.add_hline(y=budget_Mt, line_dash="dash", line_color="red",
                      annotation_text=f"budget {budget_Mt:,.0f} Mt")
    fig.update_layout(yaxis_title="Mt CO2e (cumulative)", xaxis_title="Year",
                      template="plotly_white")
    return fig


def plot_net_emissions_ccs(AnnualTechnologyEmission: pd.DataFrame,
                           scenario: str = None):
    """Gross emissions vs CCS capture vs net.

    AnnualEmissions is net (CCS enters negative); this decomposes how much
    of decarbonization is capture rather than avoidance.
    Input: AnnualTechnologyEmission.
    """
    sfx = f" [{scenario}]" if scenario else ""
    d = AnnualTechnologyEmission.copy()
    gross = d[d.VALUE > 0].groupby("YEAR").VALUE.sum()
    captured = -d[d.VALUE < 0].groupby("YEAR").VALUE.sum()
    net = d.groupby("YEAR").VALUE.sum()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=gross.index, y=gross.values, name="Gross emissions",
                         marker_color="indianred"))
    fig.add_trace(go.Bar(x=captured.index, y=-captured.values,
                         name="CCS captured", marker_color="seagreen"))
    fig.add_trace(go.Scatter(x=net.index, y=net.values, name="Net",
                             mode="lines+markers", line=dict(color="black")))
    fig.update_layout(barmode="relative", template="plotly_white",
                      title=f"Gross vs captured vs net emissions{sfx}",
                      yaxis_title="Mt CO2e", xaxis_title="Year",
                      hovermode="x unified")
    return fig


def plot_electricity_carbon_intensity(AnnualTechnologyEmission: pd.DataFrame,
                                      ProductionByTechnologyAnnual: pd.DataFrame,
                                      scenario: str = None):
    """Grid carbon intensity in g CO2/kWh: power-sector emissions
    (DEMPWR* techs) / electricity generation (fuel ELCB01).

    Benchmarkable: BC Hydro grid today is roughly 10-20 g/kWh.
    Conversion: 1 Mt/PJ = 3600 g/kWh.
    """
    sfx = f" [{scenario}]" if scenario else ""
    pe = AnnualTechnologyEmission[
        AnnualTechnologyEmission.TECHNOLOGY.str.startswith("DEMPWR")]\
        .groupby("YEAR").VALUE.sum()
    gen = ProductionByTechnologyAnnual[
        ProductionByTechnologyAnnual.FUEL == "ELCB01"]\
        .groupby("YEAR").VALUE.sum()
    ci = (pe.reindex(gen.index).fillna(0) / gen * 3600).dropna()
    if ci.empty:
        return None
    fig = px.line(x=ci.index, y=ci.values, markers=True,
                  title=f"Electricity carbon intensity{sfx}")
    fig.update_layout(yaxis_title="g CO2 / kWh", xaxis_title="Year",
                      template="plotly_white")
    return fig


def plot_sector_emission_intensity(AnnualTechnologyEmission: pd.DataFrame,
                                   ProductionByTechnologyAnnual: pd.DataFrame,
                                   scenario: str = None):
    """Emission intensity of final energy per sector (g CO2/MJ).

    Separates 'the sector shrank' from 'the sector cleaned up'.
    Sector emissions: DEM<sector>* techs; sector final energy: fuels
    prefixed RES/COM/IND/TRA. 1 Mt/PJ = 1000 g/MJ.
    """
    sfx = f" [{scenario}]" if scenario else ""
    d = AnnualTechnologyEmission[
        AnnualTechnologyEmission.TECHNOLOGY.str.startswith("DEM")].copy()
    d["Sector"] = d.TECHNOLOGY.map(_sector_of)
    emis = d[d.Sector.isin(["Residential", "Commercial", "Industry", "Transport"])]\
        .groupby(["YEAR", "Sector"]).VALUE.sum()
    fe = ProductionByTechnologyAnnual[
        ProductionByTechnologyAnnual.FUEL.str[:3].isin(_SECTOR_LABELS)].copy()
    fe["Sector"] = fe.FUEL.str[:3].map(_SECTOR_LABELS)
    energy = fe.groupby(["YEAR", "Sector"]).VALUE.sum()
    intensity = (emis / energy * 1000).dropna().reset_index(name="Intensity")
    if intensity.empty:
        return None
    fig = px.line(intensity, x="YEAR", y="Intensity", color="Sector",
                  color_discrete_map=palette.map_for(intensity.Sector),
                  markers=True, title=f"Final-energy emission intensity{sfx}")
    fig.update_layout(yaxis_title="g CO2 / MJ", xaxis_title="Year",
                      template="plotly_white", hovermode="x unified")
    return fig


def plot_emissions_penalty_cost(DiscountedTechnologyEmissionsPenalty: pd.DataFrame,
                                scenario: str = None):
    """Discounted emissions-penalty cost by sector over time (M$).

    Connects the climate story to the cost story.
    Input: DiscountedTechnologyEmissionsPenalty.
    """
    sfx = f" [{scenario}]" if scenario else ""
    d = DiscountedTechnologyEmissionsPenalty.copy()
    d["Sector"] = d.TECHNOLOGY.map(_sector_of)
    g = d.groupby(["YEAR", "Sector"], as_index=False).VALUE.sum()
    fig = px.bar(g, x="YEAR", y="VALUE", color="Sector",
                 color_discrete_map=palette.map_for(g.Sector),
                 title=f"Discounted emissions penalty by sector{sfx}")
    fig.update_layout(yaxis_title="M$", xaxis_title="Year", barmode="stack",
                      template="plotly_white", hovermode="x unified")
    return fig


def plot_scenario_emission_wedges(tech_emissions_by_run: dict,
                                  reference: str):
    """Abatement wedges: sector emissions in <reference> minus each other run.

    tech_emissions_by_run: {run_name: AnnualTechnologyEmission df}. Positive
    wedge = that sector emits less than in the reference. The scenario-paper
    plot: where does each policy actually cut?
    """
    if reference not in tech_emissions_by_run:
        return None
    def by_sector(df):
        d = df[df.VALUE > 0].copy()
        d["Sector"] = d.TECHNOLOGY.map(_sector_of)
        return d.groupby(["YEAR", "Sector"]).VALUE.sum()
    ref = by_sector(tech_emissions_by_run[reference])
    figs = go.Figure()
    for run, df in tech_emissions_by_run.items():
        if run == reference:
            continue
        wedge = (ref - by_sector(df)).dropna().reset_index(name="Abated")
        for sector, dd in wedge.groupby("Sector"):
            figs.add_trace(go.Scatter(
                x=dd.YEAR, y=dd.Abated, stackgroup=run, mode="lines",
                name=f"{run}: {sector}"))
    figs.update_layout(title=f"Abatement wedges vs {reference}",
                       yaxis_title="Mt CO2e avoided", xaxis_title="Year",
                       template="plotly_white", hovermode="x unified")
    return figs


def plot_target_gap(AnnualEmissions: pd.DataFrame, scenario: str = None):
    """Model emissions vs BC legislated targets at target years (gap bars).

    Uses bcnexus_const.emission_targets (as the existing overlay does).
    """
    sfx = f" [{scenario}]" if scenario else ""
    targets = getattr(bcnexus_const, "emission_targets", None)
    if not targets:
        return None
    tg = dict(zip(targets["years"], targets["emissions_MTeCO2"]))
    g = AnnualEmissions.groupby("YEAR").VALUE.sum()
    rows = [(y, g.get(y), t, (g.get(y) - t) if g.get(y) is not None else None)
            for y, t in tg.items() if y in g.index]
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["YEAR", "Model", "Target", "Gap"])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df.YEAR, y=df.Model, name="Model",
                         marker_color="indianred"))
    fig.add_trace(go.Bar(x=df.YEAR, y=df.Target, name="Target",
                         marker_color="seagreen"))
    for _, r in df.iterrows():
        fig.add_annotation(x=r.YEAR, y=max(r.Model, r.Target),
                           text=f"gap {r.Gap:+.1f} Mt", showarrow=False,
                           yshift=12)
    fig.update_layout(barmode="group", template="plotly_white",
                      title=f"Emissions vs BC targets{sfx}",
                      yaxis_title="Mt CO2e", xaxis_title="Target year")
    return fig


def get_emission_from_sector(AnnualTechnologyEmission:pd.DataFrame,scenario:str):
    if AnnualTechnologyEmission is not None:
        if 'end_use_fuel_label' not in AnnualTechnologyEmission.columns or 'sector_label' not in AnnualTechnologyEmission.columns:
            AnnualTechnologyEmission = add_emission_plot_helper_columns(AnnualTechnologyEmission)
        # Group by YEAR and end_use_fuel, summing the VALUE column
        grouped_data = AnnualTechnologyEmission.groupby(['YEAR', 'sector','sector_label'], as_index=False)['VALUE'].sum()

        fig = px.bar(
            grouped_data,
            x='YEAR',
            y='VALUE',
            color='sector_label',
            title=f'Annual Technology Emissions by End Use Fuel [{scenario}]',
            labels={'VALUE': 'Emissions (Million Tonnes of CO2)', 'YEAR': 'Year', 'sector_label': 'Sector'}
        )

        return fig
    else:
        utils.print_update(level=2,message=f"AnnualTechnologyEmission Data empty for {scenario}")

# ==========================================================================
# Agricultural emissions
# ==========================================================================
# Enteric fermentation, manure management and agricultural soils, grouped the
# way the national inventory groups them (IPCC 3.A, 3.B, 3.D).
#
# These live here rather than in plot_Livestock so the agricultural sources
# can be read against each other and against the energy system, which is the
# comparison that matters once livestock and crops compete for the same land.
#
# A NOTE ON CO2 EQUIVALENCE, because it is easy to get wrong twice over.
# Every emission factor in this model ALREADY has a GWP applied: they are IPCC
# 2006 Tier 1 implied factors multiplied by AR5 GWP100 (CH4 28, N2O 265).
# Dairy enteric fermentation is 128 kg CH4/head x 28 = 3.584; dairy manure N2O
# is 0.1 kg N2O/head x 265 = 0.0265. So CH4_FER, CH4_MAN, N2O_MAN, N2O_DIR and
# N2O_IND are all in CO2e already, they are directly summable, and applying a
# GWP in the figure would double-count. Nothing below multiplies by anything.

_EMISSION_UNIT = "kt CO2e"
# model_structure.units['emission'] declares Million Tonnes, but the factors
# are t CO2e per head against an activity in thousand head, which yields kt.
# The CH4 total of ~1048 is 1.05 Mt CO2e, the right order for BC enteric
# fermentation. Change this one constant if that question is ever settled the
# other way.

SETS_DIR = "data/clews_data/SETs"

# IPCC agricultural source categories. Manure management carries both its
# methane and its nitrous oxide, which is why it is a tuple rather than a
# single code.
AGRICULTURE_CATEGORIES = {
    "Enteric fermentation": ("CH4_FER",),
    "Manure management": ("CH4_MAN", "N2O_MAN"),
    "Agricultural soils": ("N2O_DIR", "N2O_IND"),
}

_SOIL_N2O = {"N2O_DIR": "Direct", "N2O_IND": "Indirect"}

_REGION_LAND = model_structure.LandRegions[0]
_PATHWAY_LABELS = {pw: a["label"]
                   for pw, a in model_structure.LivestockPathways.items()}
_LVS_PROD_TECH = {f"LVS{pw}{_REGION_LAND}": pw
                  for pw in model_structure.LivestockPathways}


def _ag_layout(fig, title, ytitle, legend_title=""):
    fig.update_layout(title=title, xaxis_title="Year", yaxis_title=ytitle,
                      legend_title=legend_title, template="plotly_white",
                      hovermode="x unified")
    return fig


def _ag_sfx(scenario):
    return f" [{scenario}]" if scenario else ""


def _ag_stack(pivot, order=None):
    fig = go.Figure()
    for col in (order or list(pivot.columns)):
        if col not in pivot.columns:
            continue
        fig.add_trace(go.Scatter(x=pivot.index, y=pivot[col], name=str(col),
                                 stackgroup="one", mode="lines",
                                 line=dict(color=palette.color(col)),
                                 fillcolor=palette.color(col)))
    return fig


def _ag_pivot(d, column):
    g = d.groupby(["YEAR", column], as_index=False).VALUE.sum()
    return g.pivot(index="YEAR", columns=column, values="VALUE").fillna(0)


@lru_cache(maxsize=None)
def _mode_labels_cached(sets_dir: str) -> dict:
    """{mode_number: label} from ModeList.txt.

    ModeList.txt is written after every module has appended its modes, so it
    names all of them - crops, land covers, agrivoltaics and livestock. It is
    the only place the mapping exists; reconstructing it from a hardcoded
    ordering breaks the moment a mode is inserted ahead of another.
    """
    path = Path(sets_dir) / "ModeList.txt"
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        if ":" not in line:
            continue
        num, label = line.split(":", 1)
        try:
            out[int(num.strip())] = label.strip()
        except ValueError:
            continue
    return out


def mode_labels(sets_dir=None) -> dict:
    """Mode number -> label, cached.

    Call ``mode_labels.cache_clear()`` after a rebuild, or a new numbering is
    read against the old names.
    """
    return _mode_labels_cached(str(Path(sets_dir or SETS_DIR).resolve()))


mode_labels.cache_clear = _mode_labels_cached.cache_clear


def _crop_of_mode(label: str):
    """Crop code for a crop mode label, else None.

    'WHEHI' -> 'WHE'. 'AGVWHEHI' -> 'WHE' as well: an agrivoltaic field is the
    same crop on the same soil emitting the same soil N2O, so it belongs in
    that crop's total rather than in a category of its own.
    """
    if label.startswith("AGV") and len(label) == 8:
        code = label[3:6]
    elif len(label) == 5:
        code = label[:3]
    else:
        return None
    return code if code in model_structure.CropYieldFactors else None


# ---------------------------------------------------------------- livestock
def plot_livestock_n2o(AnnualTechnologyEmission: pd.DataFrame,
                       scenario: str = None):
    """Nitrous oxide from manure management, per animal type.

    N2O_MAN is the only N2O livestock emits.

    No soil-N2O reference line. Soil N2O is roughly fifteen times larger, so
    putting it on this axis flattens the animals it is meant to give context
    to into an unreadable band at the bottom. Read it against
    plot_agriculture_emissions, where the categories share an axis on purpose.
    """
    emis = AnnualTechnologyEmission
    if emis is None or emis.empty or "EMISSION" not in emis.columns:
        return None
    d = emis[(emis.EMISSION == "N2O_MAN")
             & emis.TECHNOLOGY.isin(_LVS_PROD_TECH)].copy()
    if d.empty:
        return None
    d["Animal"] = d.TECHNOLOGY.map(_LVS_PROD_TECH).map(_PATHWAY_LABELS)
    fig = _ag_stack(_ag_pivot(d, "Animal"))

    return _ag_layout(fig,
                      f"Livestock N2O, manure management{_ag_sfx(scenario)}",
                      _EMISSION_UNIT, "Animal")


def plot_livestock_ch4(AnnualTechnologyEmission: pd.DataFrame,
                       scenario: str = None):
    """Methane per animal type, split into enteric fermentation and manure.

    Two panels on a shared y-axis rather than one stack of ten series: the
    split is the analytically interesting part. Enteric fermentation dominates
    ruminants and manure dominates swine, and summing them hides that.
    """
    emis = AnnualTechnologyEmission
    if emis is None or emis.empty or "EMISSION" not in emis.columns:
        return None

    panels = [("CH4_FER", "Enteric fermentation"),
              ("CH4_MAN", "Manure management")]
    frames = {}
    for code, _title in panels:
        d = emis[(emis.EMISSION == code)
                 & emis.TECHNOLOGY.isin(_LVS_PROD_TECH)].copy()
        if d.empty:
            continue
        d["Animal"] = d.TECHNOLOGY.map(_LVS_PROD_TECH).map(_PATHWAY_LABELS)
        frames[code] = _ag_pivot(d, "Animal")
    if not frames:
        return None

    fig = make_subplots(rows=1, cols=2, shared_yaxes=True,
                        subplot_titles=[t for _c, t in panels])
    for col, (code, _title) in enumerate(panels, start=1):
        pivot = frames.get(code)
        if pivot is None:
            continue
        for name in pivot.columns:
            fig.add_trace(go.Scatter(
                x=pivot.index, y=pivot[name], name=str(name),
                stackgroup=f"s{col}", mode="lines",
                legendgroup=str(name), showlegend=(col == 1),
                line=dict(color=palette.color(name)),
                fillcolor=palette.color(name)), row=1, col=col)

    fig.update_xaxes(title_text="Year", row=1, col=1)
    fig.update_xaxes(title_text="Year", row=1, col=2)
    fig.update_yaxes(title_text=_EMISSION_UNIT, row=1, col=1)
    fig.update_layout(title=f"Livestock CH4 by source{_ag_sfx(scenario)}",
                      legend_title="Animal", template="plotly_white",
                      hovermode="x unified")
    return fig


# ------------------------------------------------------------------- soils
def plot_crop_soil_n2o(AnnualTechnologyEmissionByMode: pd.DataFrame,
                       scenario: str = None, sets_dir=None):
    """Agricultural soil N2O per crop.

    Input: AnnualTechnologyEmissionByMode, NOT AnnualTechnologyEmission. Soil
    N2O sits on the LNDAGR cluster technologies, where the mode is what
    distinguishes one crop regime from another; the mode-free frame has
    already summed every crop on a cluster into one number and cannot be
    split back apart.

    Direct and indirect are added together here - the split is the subject of
    plot_soil_n2o_split. Agrivoltaic modes fold into their parent crop.
    """
    emis = AnnualTechnologyEmissionByMode
    if emis is None or emis.empty or "MODE_OF_OPERATION" not in emis.columns:
        return None
    labels = mode_labels(sets_dir)
    if not labels:
        return None

    d = emis[emis.EMISSION.isin(_SOIL_N2O)].copy()
    if d.empty:
        return None
    d["Crop"] = (d.MODE_OF_OPERATION.astype(int).map(labels)
                 .map(lambda v: _crop_of_mode(v) if isinstance(v, str) else None))
    d = d[d.Crop.notna()]
    if d.empty:
        return None
    d["Crop"] = d.Crop.map(lambda c: model_structure.NamingConvention.get(c, c))

    pivot = _ag_pivot(d, "Crop")
    order = sorted(pivot.columns, key=lambda c: -pivot[c].sum())
    fig = _ag_stack(pivot, order)
    return _ag_layout(fig,
                      f"Agricultural soil N2O by crop{_ag_sfx(scenario)}",
                      _EMISSION_UNIT, "Crop")


def plot_soil_n2o_split(AnnualTechnologyEmission: pd.DataFrame,
                        scenario: str = None):
    """Direct vs indirect agricultural soil N2O, with the ratio.

    Input: AnnualTechnologyEmission.

    Both are emitted from the same crop-mode activity at fixed factors
    (N2O_DIR 2.16462335, N2O_IND 0.93916), so the ratio on the secondary axis
    should sit flat at 2.30 every year. A drift means the two are being driven
    by different activity, which would be a bug rather than a result - the
    same kind of sanity indicator as the irrigation-intensity trace in
    plot_Land.
    """
    emis = AnnualTechnologyEmission
    if emis is None or emis.empty or "EMISSION" not in emis.columns:
        return None
    d = emis[emis.EMISSION.isin(_SOIL_N2O)].copy()
    if d.empty:
        return None
    d["Source"] = d.EMISSION.map(_SOIL_N2O)
    pivot = _ag_pivot(d, "Source")

    fig = go.Figure()
    for name in ("Direct", "Indirect"):
        if name in pivot.columns:
            fig.add_trace(go.Bar(x=pivot.index, y=pivot[name], name=name,
                                 marker_color=palette.color(name)))
    if {"Direct", "Indirect"} <= set(pivot.columns):
        ratio = pivot["Direct"] / pivot["Indirect"].replace(0, np.nan)
        fig.add_trace(go.Scatter(x=pivot.index, y=ratio,
                                 name="Direct / indirect", mode="lines",
                                 yaxis="y2",
                                 line=dict(color="#444444", dash="dot")))
        fig.update_layout(yaxis2=dict(title="ratio", overlaying="y",
                                      side="right", rangemode="tozero"))
    fig.update_layout(barmode="stack")
    return _ag_layout(fig,
                      f"Agricultural soil N2O, direct vs indirect"
                      f"{_ag_sfx(scenario)}", _EMISSION_UNIT, "Source")


# -------------------------------------------------------------- ag totals
def plot_agriculture_emissions(AnnualTechnologyEmission: pd.DataFrame,
                               scenario: str = None):
    """Total agricultural emissions by IPCC source category, in CO2e.

    Input: AnnualTechnologyEmission. Categories are AGRICULTURE_CATEGORIES:
    enteric fermentation (CH4_FER), manure management (CH4_MAN + N2O_MAN) and
    agricultural soils (N2O_DIR + N2O_IND).

    Summing across gases is valid because every factor already carries its
    AR5 GWP100 - see the note at the head of this section. No conversion is
    applied here and none should be added: doing so counts the GWP twice. CO2
    is deliberately excluded, being an energy-system emission in this model
    rather than an agricultural one.
    """
    emis = AnnualTechnologyEmission
    if emis is None or emis.empty or "EMISSION" not in emis.columns:
        return None

    code_to_category = {code: cat
                        for cat, codes in AGRICULTURE_CATEGORIES.items()
                        for code in codes}
    d = emis[emis.EMISSION.isin(code_to_category)].copy()
    if d.empty:
        return None
    d["Category"] = d.EMISSION.map(code_to_category)

    pivot = _ag_pivot(d, "Category")
    fig = _ag_stack(pivot, [c for c in AGRICULTURE_CATEGORIES
                            if c in pivot.columns])
    fig.add_trace(go.Scatter(x=pivot.index, y=pivot.sum(axis=1),
                             name="Total agriculture", mode="lines",
                             line=dict(color="#222222", width=2)))
    return _ag_layout(fig,
                      f"Agricultural sector emissions{_ag_sfx(scenario)}",
                      _EMISSION_UNIT, "IPCC category")


# ---------------------------------------------------------------- one call
AGRICULTURE_FIGURES = ("agriculture_total", "livestock_ch4", "livestock_n2o",
                       "crop_soil_n2o", "soil_n2o_split")


def agriculture_emission_figures(result_pack, scenario: str = None,
                                 show: bool = True, sets_dir=None) -> dict:
    """Build every agricultural emission figure in one call.

    Notebook usage::

        from bcnexus.vis import plot_Climate as Cvis
        figs = Cvis.agriculture_emission_figures(result_pack, scene)

    Returns ``{name: figure}`` keyed by AGRICULTURE_FIGURES, omitting any
    whose input frame held no matching rows.

    crop_soil_n2o needs AnnualTechnologyEmissionByMode and ModeList.txt; if
    either is missing that one figure is skipped and the rest still build.
    """
    emis = result_pack.get_df("AnnualTechnologyEmission")
    bymode = result_pack.get_df("AnnualTechnologyEmissionByMode")

    figs = {
        "agriculture_total": plot_agriculture_emissions(emis, scenario),
        "livestock_ch4": plot_livestock_ch4(emis, scenario),
        "livestock_n2o": plot_livestock_n2o(emis, scenario),
        "crop_soil_n2o": plot_crop_soil_n2o(bymode, scenario, sets_dir),
        "soil_n2o_split": plot_soil_n2o_split(emis, scenario),
    }
    figs = {k: v for k, v in figs.items() if v is not None}

    missing = [k for k in AGRICULTURE_FIGURES if k not in figs]
    if missing:
        print(f"no rows for: {', '.join(missing)} (checked "
              f"AnnualTechnologyEmission, AnnualTechnologyEmissionByMode)")

    if show:
        for fig in figs.values():
            fig.show()

    return figs
