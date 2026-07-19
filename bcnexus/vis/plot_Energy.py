from pathlib import Path
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from bcnexus.clews import model_structure
from bcnexus import constants as bcnexus_const
from bcnexus import utils
from bcnexus.vis import palette
# bcnexus_const.units_mapping
end_use_fuels_set = (
    set(value for values in model_structure.EndUseFuels.values() for value in values) |
    set(model_structure.ImportFuels) |
    set(model_structure.ExportFuels) |
    set(model_structure.DomesticMining) |
    set(model_structure.DomesticRenewables)
)


def plot_energy_consumption_by_sector(use_by_tech: pd.DataFrame, 
                                      plot_unit:str,
                                      scenario:str=None):
    title_suffix = f" [{scenario}]" if scenario else ""
    # Extract configuration settings
    sectors = bcnexus_const.sector_mapping.get('power')  # noqa: F841
    
    # Filter and process data
    filtered_tech = (
        use_by_tech.loc[use_by_tech['TECHNOLOGY'].str.startswith('DEM'), ['YEAR', 'TECHNOLOGY', 'VALUE']]
        .assign(SECTOR=lambda df: df['TECHNOLOGY'].str[3:6])
        .query("SECTOR in @sectors")
        .groupby(['YEAR', 'SECTOR'], as_index=False)
        .sum()
        .assign(SECTOR_name=lambda df: df['SECTOR'].map(bcnexus_const.legend_labels).fillna(df['SECTOR']))
    )

    # Create bar traces
    traces = []
    for sector, sector_data in filtered_tech.groupby('SECTOR_name'):
        traces.append(go.Bar(
            x=sector_data['YEAR'],
            y=sector_data['VALUE'],
            name=sector,
            marker=dict(color=bcnexus_const.colors_name_mapping.get(sector, 'rgba(0, 0, 0, 0.5)'))
        ))

    # Create figure with stacked bars
    fig = go.Figure(data=traces)
    
    # Update layout
    fig.update_layout(
        title='Energy Consumption by Sector ' + title_suffix,
        barmode='stack',
        yaxis_title=plot_unit,
        legend_title_text=None,
         legend=dict(
            orientation="h",  # Horizontal alignment
            yanchor="bottom",
            y=1.15,  # Position above the plots
            xanchor="center",
            x=0.8,  # Center the legend horizontally
            traceorder="normal",  # To keep the order of the legend consistent
        ),
    )

    return fig

def plot_consumption_by_fuel(usebytech: pd.DataFrame, 
                             plot_unit: str,
                             scenario: str = None):
    title_suffix = f" [{scenario}]" if scenario else ""

    # Filter and group data
    filtered_usebytech1 = (
        usebytech[usebytech['FUEL'].isin(end_use_fuels_set)]
        .groupby(['YEAR', 'FUEL'], as_index=False)
        .agg({'VALUE': 'sum'})
    )

    # Map fuel names
    filtered_usebytech1['FUEL_name'] = filtered_usebytech1['FUEL'].map(bcnexus_const.legend_labels)

    # Create bar traces for each fuel
    traces = []
    for fuel, fuel_data in filtered_usebytech1.groupby('FUEL_name'):
        traces.append(go.Bar(
            x=fuel_data['YEAR'],
            y=fuel_data['VALUE'],
            name=fuel,
            marker=dict(color=bcnexus_const.colors_name_mapping.get(fuel, 'rgba(0, 0, 0, 0.5)'))
        ))

    # Create figure with stacked bars
    fig = go.Figure(data=traces)

    # Update layout
    fig.update_layout(
        title='Energy Consumption by Fuel' + title_suffix,
        barmode='stack',
        yaxis_title=plot_unit,
        margin=dict(r=150),  # extra room for right legend
        legend=dict(
            orientation="v",           # vertical legend
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.05,                   # place it just outside the plot
            font=dict(size=12),       # smaller font for better fit
            traceorder="normal",
        ),
    )

    return fig



def plot_combined_stacked_energy_consumption(UseByTechnology: pd.DataFrame,
                                             plot_unit:str='gwh',
                                             scenario:str=None,
                                             timeslices:int=None):


    df=UseByTechnology
    
    if 'gwh' in plot_unit.lower():
        consumption_plot_unit=bcnexus_const.units_mapping['consumption_gwh']
        df['VALUE'] = df['VALUE'] * utils.get_PJ_to_GWh_conversion_factor(timeslices) # Convert PJ to GWh
    else:
        consumption_plot_unit=bcnexus_const.units_mapping['consumption_pj']
    # Plot 1: Energy Consumption by Sector (Stacked Bar chart)
    fig_sector = plot_energy_consumption_by_sector(df, consumption_plot_unit,scenario)

    # Plot 2: Energy Consumption by Fuel (Stacked Bar chart)
    fig_fuel = plot_consumption_by_fuel(df,consumption_plot_unit,scenario)

    return fig_sector,fig_fuel

def get_annual_generation_plot(ProductionByTechnology:pd.DataFrame,
                        scenario:str,
                        timeslices:int):
    generation_plot_unit = bcnexus_const.units_mapping['generation_gwh']
    df=utils.get_labels(ProductionByTechnology)
    
    # Group by YEAR, sector, and sector_label, summing the VALUE column
    grouped_data = df.groupby(['YEAR', 'end_use_fuel', 'end_use_fuel_label'], as_index=False)['VALUE'].sum()
    
    if 'gwh' in generation_plot_unit.lower():
        grouped_data['VALUE'] = grouped_data['VALUE'] * utils.get_PJ_to_GWh_conversion_factor()  # Convert PJ to GWh
    
    # Create a stacked bar plot
    Nexus_yearly_energy_fig = px.bar(
        grouped_data, 
        x='YEAR', 
        y='VALUE', 
        color='end_use_fuel_label', 
        labels={'VALUE': f'Energy Generation ({generation_plot_unit})', 'YEAR': 'Year', 'end_use_fuel_label': 'Fuel'},
        color_discrete_map=bcnexus_const.custom_colors
    )
    
    Nexus_yearly_energy_fig.update_xaxes(title_text='Year')
    Nexus_yearly_energy_fig.update_yaxes(title_text=generation_plot_unit)
    Nexus_yearly_energy_fig.update_layout(title_text=f'Power Generation from Fuels [{scenario}]')
    Nexus_yearly_energy_fig.update_layout(xaxis=dict(tickmode='linear'))
    return Nexus_yearly_energy_fig



def get_capacity_plot(capacity: pd.DataFrame, 
                      scenario: str,
                      investment:bool):
    df = utils.get_labels(capacity)
    plot_prefix="Invested" if investment else "Total"
    # Assign power_techs and filter
    df.loc[:, 'power_techs'] = df['TECHNOLOGY'].apply(
        lambda x: x[:6] if x[:6] in bcnexus_const.technologies['capacity'] else None
    )
    df.loc[:, 'power_techs_labels'] = df['power_techs'].map(bcnexus_const.legend_labels)
    df = df.loc[df['power_techs_labels'].notna()]

    # Group data
    grouped_data = df.groupby(['YEAR', 'power_techs', 'power_techs_labels'], as_index=False)['VALUE'].sum()

    # Build a dict to map techs to labels
    tech_to_label = dict(zip(grouped_data['power_techs'], grouped_data['power_techs_labels']))

    # Plot using internal tech codes for color
    fig = px.bar(
        grouped_data,
        x='YEAR',
        y='VALUE',
        color='power_techs',
        labels={'VALUE': bcnexus_const.units_mapping['capacity'], 'YEAR': 'Year'},
        color_discrete_map=bcnexus_const.custom_colors
    )

    # Manually update legend names
    fig.for_each_trace(
        lambda t: t.update(name=tech_to_label.get(t.name, t.name),
                           legendgroup=tech_to_label.get(t.name, t.name),
                           hovertemplate=t.hovertemplate.replace(t.name, tech_to_label.get(t.name, t.name)))
    )

    # Layout tweaks
    fig.update_layout(
        title_text=f'{plot_prefix} Capacity [{scenario}]',
        yaxis_title=bcnexus_const.units_mapping['capacity'],
        xaxis_title='Year',
        legend_title_text='Power technology'
    )
    fig.update_layout(xaxis=dict(tickmode='linear'))
    return fig

def get_generation_timeseries_plot(RateOfProductionByTechnology: pd.DataFrame,
                                   timeslices: int,
                                   scenario: str):
    df = utils.get_labels(RateOfProductionByTechnology)

    # Assign power_techs and filter
    df.loc[:, 'power_techs'] = df['TECHNOLOGY'].apply(
        lambda x: x[:6] if x[:6] in bcnexus_const.technologies['energy'] else None
    )
    df.loc[:, 'power_techs_labels'] = df['power_techs'].map(bcnexus_const.legend_labels)
    df = df.loc[df['power_techs_labels'].notna()]
    max_timeslice_digits = len(str(timeslices - 1))
    df = df.copy()
    df.loc[:, 'SEQUENTIAL_TIMESLICE'] = (
        df['YEAR'].astype(str) + 
        df['TIMESLICE'].astype(str).str.zfill(max_timeslice_digits)
    ).astype(int)
        
    df.loc[:, 'SEQUENTIAL_TS_LABEL'] = df['SEQUENTIAL_TIMESLICE'].astype(str).apply(lambda x: f"{x[:4]} {x[4:]}")
    
    df = df.sort_values(by='SEQUENTIAL_TIMESLICE')
    df['VALUE_MW'] = df['VALUE'] * utils.get_PJ_to_GWh_conversion_factor()  # MW = PJ × 1E9 / seconds in timeslice

    # Create a stacked area plot for each technology
    Nexus_timeslice_activity_fig = px.area(
        df,
        x='SEQUENTIAL_TS_LABEL',
        y='VALUE_MW',  # MW
        color='power_techs_labels',
        title=f"BCNexus Power Generation [{scenario}]",
        labels={'SEQUENTIAL_TS_LABEL': 'Representative Timeslice (Year_TS)', 'VALUE_MW': 'Activity (MW)'},
        color_discrete_map=bcnexus_const.custom_colors  # Use custom colors if defined
    )

    # Update layout for better visualization
    Nexus_timeslice_activity_fig.update_layout(
        xaxis=dict(tickangle=-90),
        yaxis_title="Activity (MW)",
        legend_title="Technology",
        title_x=0.5,
        template="plotly_white",
        annotations=[
            dict(
                x=1.1,
                y=1.2,
                xref="paper",
                yref="paper",
                text=f"{timeslices} timeslices",
                showarrow=False,
                font=dict(size=12, color="black"),
                align="center",
                bgcolor="lightgrey",
                bordercolor="grey",
                borderwidth=0.2
            )
        ]
    )
    
    return Nexus_timeslice_activity_fig

def get_annual_power_generation_plot(ProductionByTechnologyAnnual: pd.DataFrame,scenario: str, timeslices: int):
    df = utils.add_power_tech_labels(ProductionByTechnologyAnnual,'energy')
    df = df[df['power_techs_labels'].notna()]  # Filter rows where 'power_techs_labels' is not NaN
    df = df.copy()  # Ensure we are working with a copy
    df.loc[:, 'VALUE_GWh'] = df['VALUE'] * utils.get_PJ_to_GWh_conversion_factor()

    # Group data
    elc_df = df[df['FUEL'] == 'ELCB01']
    grouped_data = elc_df.groupby(
        ['YEAR', 'power_techs', 'power_techs_labels'], as_index=False
    )['VALUE'].sum()
    grouped_data['VALUE_GWh'] = grouped_data['VALUE'] * utils.get_PJ_to_GWh_conversion_factor()  # no timeslices arg


    # Build a dict to map techs to labels
    tech_to_label = dict(zip(grouped_data['power_techs'], grouped_data['power_techs_labels']))

    # Plot using internal tech codes for color
    fig = px.bar(
        grouped_data,
        x='YEAR',
        y='VALUE_GWh',
        color='power_techs',
        opacity=0.8,
        labels={'VALUE_GWh': bcnexus_const.units_mapping['generation_gwh'], 'YEAR': 'Year'},
        color_discrete_map=bcnexus_const.custom_colors
    )

    # Manually update legend names
    fig.for_each_trace(
        lambda t: t.update(name=tech_to_label.get(t.name, t.name),
                           legendgroup=tech_to_label.get(t.name, t.name),
                           hovertemplate=t.hovertemplate.replace(t.name, tech_to_label.get(t.name, t.name)))
    )

    # Layout tweaks
    fig.update_layout(
        title_text=f'Annual Power Generation[{scenario}]',
        yaxis_title=bcnexus_const.units_mapping['generation_gwh'],
        xaxis_title='Year',
        legend_title_text='Power technology'
    )
    fig.update_layout(xaxis=dict(tickmode='linear'))

    return fig

def get_capital_investments(CapitalInvestment: pd.DataFrame, 
                      scenario: str):
    df = utils.add_power_tech_labels(CapitalInvestment,'capacity')
    df = df[df['power_techs_labels'].notna()]  # Filter rows where 'power_techs_labels' is not NaN

    # Group data
    grouped_data = df.groupby(['YEAR', 'power_techs', 'power_techs_labels'], as_index=False)['VALUE'].sum()

    # Build a dict to map techs to labels
    tech_to_label = dict(zip(grouped_data['power_techs'], grouped_data['power_techs_labels']))

    # Plot using internal tech codes for color
    fig = px.bar(
        grouped_data,
        x='YEAR',
        y='VALUE',
        color='power_techs',
        opacity=0.8,
        labels={'VALUE': bcnexus_const.units_mapping['capital_investment'], 'YEAR': 'Year'},
        color_discrete_map=bcnexus_const.custom_colors
    )

    # Manually update legend names
    fig.for_each_trace(
        lambda t: t.update(name=tech_to_label.get(t.name, t.name),
                           legendgroup=tech_to_label.get(t.name, t.name),
                           hovertemplate=t.hovertemplate.replace(t.name, tech_to_label.get(t.name, t.name)))
    )

    # Layout tweaks
    fig.update_layout(
        title_text=f'Capital Investments in Power Capacity Expansion [{scenario}]',
        # yaxis_title=bcnexus_const.units_mapping['capital_investment'],
        # xaxis_title='Year',
        legend_title_text='Power technology'
    )
    fig.update_layout(xaxis=dict(tickmode='linear'))
    return fig

# ---------------------------------------------------------------- new plots
def plot_system_cost_breakdown(CapitalInvestment: pd.DataFrame = None,
                               AnnualFixedOperatingCost: pd.DataFrame = None,
                               AnnualVariableOperatingCost: pd.DataFrame = None,
                               DiscountedTechnologyEmissionsPenalty: pd.DataFrame = None,
                               scenario: str = None):
    """Total system cost by component per year (M$) — 'what does this
    scenario cost' in one stack. Pass whichever result CSVs exist; missing
    components are skipped. NOTE: capex/O&M here are undiscounted annual
    flows while the emissions penalty is discounted — label reflects mix;
    for strict comparability use the Discounted* result set throughout.
    """
    sfx = f" [{scenario}]" if scenario else ""
    parts = {"Capital investment": CapitalInvestment,
             "Fixed O&M": AnnualFixedOperatingCost,
             "Variable O&M": AnnualVariableOperatingCost,
             "Emissions penalty (disc.)": DiscountedTechnologyEmissionsPenalty}
    rows = []
    for label, df in parts.items():
        if df is not None and not df.empty:
            g = df.groupby("YEAR", as_index=False).VALUE.sum()
            g["Component"] = label
            rows.append(g)
    if not rows:
        return None
    d = pd.concat(rows)
    fig = px.bar(d, x="YEAR", y="VALUE", color="Component",
                 color_discrete_map=palette.map_for(d.Component),
                 title=f"System cost by component{sfx}")
    fig.update_layout(yaxis_title="M$", xaxis_title="Year", barmode="stack",
                      template="plotly_white", hovermode="x unified")
    return fig


def plot_fossil_imports(ProductionByTechnologyAnnual: pd.DataFrame,
                        scenario: str = None):
    """Imported fuel supply over time (IMP* technologies, PJ) — the
    energy-security / import phase-out view."""
    sfx = f" [{scenario}]" if scenario else ""
    d = ProductionByTechnologyAnnual[
        ProductionByTechnologyAnnual.TECHNOLOGY.str.startswith("IMP")].copy()
    if d.empty:
        return None
    d["Fuel"] = d.TECHNOLOGY.str[3:6]
    g = d.groupby(["YEAR", "Fuel"], as_index=False).VALUE.sum()
    fig = px.area(g, x="YEAR", y="VALUE", color="Fuel",
                  color_discrete_map=palette.map_for(g.Fuel),
                  title=f"Imported fuel supply{sfx}")
    fig.update_layout(yaxis_title="PJ", xaxis_title="Year",
                      template="plotly_white", hovermode="x unified")
    return fig


def plot_nexus_sankey(ProductionByTechnologyAnnual: pd.DataFrame,
                      UseByTechnology: pd.DataFrame,
                      year: int,
                      scenario: str = None,
                      min_flow: float = 0.5):
    """Cross-dimension nexus flows for one year (Sankey).

    Aggregated links actually present in the model:
      Land clusters -> crops (kkm2-weighted, via CRP production of LND techs)
      Water sources -> agriculture / public / power (BCM)
      Biomass       -> industry / residential / commercial / power (PJ)
      Electricity   -> end-use sectors (PJ)
    Units differ per subsystem — treat widths as within-subsystem only.
    min_flow filters clutter (in each subsystem's native unit).
    """
    sfx = f" [{scenario}]" if scenario else ""
    prod = ProductionByTechnologyAnnual[
        ProductionByTechnologyAnnual.YEAR == year]
    use = UseByTechnology[UseByTechnology.YEAR == year]

    links = []  # (source, target, value)

    # land -> crops
    crp = prod[prod.FUEL.str.startswith("CRP") &
               prod.TECHNOLOGY.str.startswith("LND")]
    for f, v in crp.groupby("FUEL").VALUE.sum().items():
        links.append(("Agricultural land", f"Crop: {f[3:6]}", v))

    # water -> purposes
    for pref, tgt in [("AGRWAT", "Agriculture"), ("PUBWAT", "Public supply"),
                      ("PWRWAT", "Power")]:
        v = prod[prod.FUEL.str.startswith(pref)].VALUE.sum()
        if v > 0:
            links.append(("Water", tgt, v))

    # biomass -> sectors (who uses fuel BIO)
    bio = use[use.FUEL == "BIO"]
    smap = {"DEMIND": "Industry", "DEMRES": "Residential",
            "DEMCOM": "Commercial", "PWR": "Power"}
    for t, v in bio.groupby("TECHNOLOGY").VALUE.sum().items():
        for pref, tgt in smap.items():
            if t.startswith(pref):
                links.append(("Biomass", tgt, v))
                break

    # electricity -> sectors
    elc = prod[prod.FUEL.str.match(r"^(RES|COM|IND|TRA)ELC")]
    for f, v in elc.groupby("FUEL").VALUE.sum().items():
        sector = {"RES": "Residential", "COM": "Commercial",
                  "IND": "Industry", "TRA": "Transport"}[f[:3]]
        links.append(("Electricity", sector, v))

    links = [(s, t, v) for s, t, v in links if v >= min_flow]
    if not links:
        return None
    nodes = sorted({s for s, _, _ in links} | {t for _, t, _ in links})
    idx = {n: i for i, n in enumerate(nodes)}
    fig = go.Figure(go.Sankey(
        node=dict(label=nodes, pad=18, thickness=14),
        link=dict(source=[idx[s] for s, _, _ in links],
                  target=[idx[t] for _, t, _ in links],
                  value=[v for _, _, v in links])))
    fig.update_layout(title=f"Nexus flows, {year}{sfx} "
                            "(widths comparable within subsystem only)",
                      template="plotly_white")
    return fig


def _nexus_links(prod_y: pd.DataFrame, use_y: pd.DataFrame) -> list:
    """Cross-dimension flows for ONE year -> [(source, target, value), ...]."""
    links = []
    # land -> crops
    crp = prod_y[prod_y.FUEL.str.startswith("CRP") &
                 prod_y.TECHNOLOGY.str.startswith("LND")]
    for f, v in crp.groupby("FUEL").VALUE.sum().items():
        links.append(("Agricultural land", f"Crop: {f[3:6]}", v))
    # water -> purposes
    for pref, tgt in [("AGRWAT", "Agriculture"), ("PUBWAT", "Public supply"),
                      ("PWRWAT", "Power")]:
        v = prod_y[prod_y.FUEL.str.startswith(pref)].VALUE.sum()
        if v > 0:
            links.append(("Water", tgt, v))
    # biomass -> sectors
    smap = {"DEMIND": "Industry", "DEMRES": "Residential",
            "DEMCOM": "Commercial", "PWR": "Power"}
    bio = use_y[use_y.FUEL == "BIO"]
    for t, v in bio.groupby("TECHNOLOGY").VALUE.sum().items():
        for pref, tgt in smap.items():
            if t.startswith(pref):
                links.append(("Biomass", tgt, v))
                break
    # electricity -> sectors
    elc = prod_y[prod_y.FUEL.str.match(r"^(RES|COM|IND|TRA)ELC")]
    for f, v in elc.groupby("FUEL").VALUE.sum().items():
        sector = {"RES": "Residential", "COM": "Commercial",
                  "IND": "Industry", "TRA": "Transport"}[f[:3]]
        links.append(("Electricity", sector, v))
    return links


def plot_nexus_sankey_slider(ProductionByTechnologyAnnual: pd.DataFrame,
                             UseByTechnology: pd.DataFrame,
                             years: list = None,
                             scenario: str = None,
                             min_flow: float = 0.5,
                             step: int = 1):
    """Nexus Sankey with a YEAR SLIDER (one trace per year, visibility toggled).

    Node positions/indices are shared across years (union of all links), so
    dragging the slider shows genuine flow evolution rather than a relabelled
    diagram. Units differ per subsystem (kkm2 / BCM / PJ) — widths are
    comparable within a subsystem only.

    Args:
        years: subset of years to include (default: all in the results).
        min_flow: hide links below this value (in each subsystem's own unit).
        step: use every n-th year, e.g. step=5 for 2025, 2030, ...
    """
    sfx = f" [{scenario}]" if scenario else ""
    all_years = sorted(ProductionByTechnologyAnnual.YEAR.unique())
    years = [int(y) for y in (years or all_years)][::max(int(step), 1)]
    if not years:
        return None

    per_year = {}
    for y in years:
        links = [(s, t, v) for s, t, v in
                 _nexus_links(ProductionByTechnologyAnnual[
                                  ProductionByTechnologyAnnual.YEAR == y],
                              UseByTechnology[UseByTechnology.YEAR == y])
                 if v >= min_flow]
        if links:
            per_year[y] = links
    if not per_year:
        return None

    # shared node index across all years
    nodes = sorted({n for links in per_year.values()
                    for s, t, _ in links for n in (s, t)})
    idx = {n: i for i, n in enumerate(nodes)}
    node_colors = [palette.color(n.replace("Crop: ", "")) for n in nodes]

    fig = go.Figure()
    for i, (y, links) in enumerate(per_year.items()):
        fig.add_trace(go.Sankey(
            visible=(i == 0),
            name=str(y),
            node=dict(label=nodes, pad=18, thickness=14, color=node_colors,
                      line=dict(width=0)),
            link=dict(source=[idx[s] for s, _, _ in links],
                      target=[idx[t] for _, t, _ in links],
                      value=[v for _, _, v in links],
                      color=["rgba(140,160,180,.35)"] * len(links))))

    steps = []
    for i, y in enumerate(per_year):
        vis = [j == i for j in range(len(per_year))]
        steps.append(dict(method="update", label=str(y),
                          args=[{"visible": vis},
                                {"title": f"Nexus flows, {y}{sfx}"}]))
    fig.update_layout(
        title=f"Nexus flows, {list(per_year)[0]}{sfx}",
        template="plotly_white",
        sliders=[dict(active=0, currentvalue={"prefix": "Year: ",
                                              "font": {"size": 14}},
                      pad={"t": 40, "b": 10}, steps=steps)],
        margin=dict(t=60, b=90, l=20, r=20),
        annotations=[dict(x=0, y=-0.16, xref="paper", yref="paper",
                          showarrow=False, font=dict(size=11, color="grey"),
                          text="Widths comparable within a subsystem only "
                               "(land kkm², water BCM, energy PJ).")])
    return fig
