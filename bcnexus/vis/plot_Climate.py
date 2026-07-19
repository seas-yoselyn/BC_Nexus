from bcnexus import constants as bcnexus_const
from bcnexus.clews import model_structure
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
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