from pathlib import Path
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from bcnexus.clews import model_structure
from bcnexus import constants as bcnexus_const
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
                                      dash_cfg: dict,
                                      scenario:str=None):
    title_suffix = f" [{scenario}]" if scenario else ""
    # Extract configuration settings
    sectors = bcnexus_const.sector_mapping.get('power')
    
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
                             plot_unit:str,
                             scenario:str=None):
    title_suffix = f" [{scenario}]" if scenario else ""

    # Filter and group data
    filtered_usebytech1 = (usebytech[usebytech['FUEL'].isin(end_use_fuels_set)]
                           .groupby(['YEAR', 'FUEL'], as_index=False)
                           .agg({'VALUE': 'sum'}))

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
        title='Energy Consumption by Fuel'+ title_suffix,
        barmode='stack',
        yaxis_title=plot_unit,
        legend_title_text=None,
        legend=dict(
            orientation="h",  # Horizontal alignment
            yanchor="bottom",
            y=1.05,  # Position above the plots
            xanchor="center",
            x=0.55,  # Center the legend horizontally
            traceorder="normal",  # To keep the order of the legend consistent
        ),
    )

    return fig


def plot_combined_stacked_energy_consumption(use_by_tech: pd.DataFrame,
                                             plot_unit:str,
                                             scenario:str=None):

    # Plot 1: Energy Consumption by Sector (Stacked Bar chart)
    fig_sector = plot_energy_consumption_by_sector(use_by_tech, plot_unit,scenario)

    # Plot 2: Energy Consumption by Fuel (Stacked Bar chart)
    fig_fuel = plot_consumption_by_fuel(use_by_tech,plot_unit,scenario)

    return fig_sector,fig_fuel
