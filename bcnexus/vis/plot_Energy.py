from pathlib import Path
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from bcnexus.clews import model_structure
from bcnexus import constants as bcnexus_const
from bcnexus import utils
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
                                             scenario:str=None):


    df=UseByTechnology
    
    if 'gwh' in plot_unit.lower():
        consumption_plot_unit=bcnexus_const.units_mapping['consumption_gwh']
        df['VALUE'] = df['VALUE'] * utils.get_PJ_to_GWh_conversion_factor() # Convert PJ to GWh
    else:
        consumption_plot_unit=bcnexus_const.units_mapping['consumption_pj']
    # Plot 1: Energy Consumption by Sector (Stacked Bar chart)
    fig_sector = plot_energy_consumption_by_sector(df, consumption_plot_unit,scenario)

    # Plot 2: Energy Consumption by Fuel (Stacked Bar chart)
    fig_fuel = plot_consumption_by_fuel(df,consumption_plot_unit,scenario)

    return fig_sector,fig_fuel

def get_annual_generation_plot(ProductionByTechnology:pd.DataFrame,
                        scenario:str):
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

def get_generation_timeseries_plot(RateOfUseByTechnology,
                                   timeslices: int,
                                   scenario: str):
    df = utils.get_labels(RateOfUseByTechnology)

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
    df['VALUE_MW'] = df['VALUE'] * utils.get_PJ_to_GWh_conversion_factor(timeslices)  # MW = PJ × 1E9 / seconds in timeslice

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

def get_annual_power_generation_plot(ProductionByTechnologyAnnual: pd.DataFrame, 
                      scenario: str):
    df = utils.add_power_tech_labels(ProductionByTechnologyAnnual,'energy')
    df = df[df['power_techs_labels'].notna()]  # Filter rows where 'power_techs_labels' is not NaN
    df = df.copy()  # Ensure we are working with a copy
    df.loc[:, 'VALUE_GWh'] = df['VALUE'] * utils.get_PJ_to_GWh_conversion_factor()

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