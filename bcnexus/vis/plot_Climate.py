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