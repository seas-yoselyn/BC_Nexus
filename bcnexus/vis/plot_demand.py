"""
DEPRECATED — superseded by `bcnexus.vis.plot_Inputs`.

The per-sector / end-use-fuel design that lived here now works directly from
the otoole input CSVs and the shared palette:

    plot_Inputs.plot_demand_sector_panels(input_dir)   # was create_demand_plots
    plot_Inputs.plot_demand_by_sector(input_dir)       # was create_demand_plot_simplified
    plot_Inputs.plot_demand_for_sector(input_dir, 'IND')
    plot_Inputs.plot_fuel_across_sectors(input_dir, 'BIO')
    plot_Inputs.plot_land_for_power(input_dir)         # was plot_land_for_power_demand

The functions below remain so existing notebooks keep running; new work should
call plot_Inputs. `create_demand_plots` still accepts the pre-processed frame
(sector / end_use_fuel columns) via plot_Inputs' `data=` argument.
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
from  pathlib import Path
from bcnexus import constants as bcnexus_const
from bcnexus.clews import model_structure as bcnexus_structure

def create_demand_plot_simplified(df):
    fig = px.area(
        df,
        x="year",
        y=["Commercial", "Industrial", "Residential", "Transportation"],
        title="Sectoral Demand (Canada Energy Future 2023)",
        labels={"value": "Demand", "year": "Year"},
        color_discrete_map={
            "Commercial": "blue",
            "Industrial": "green",
            "Residential": "orange",
            "Transportation": "red"
        }
    )
    fig.update_layout(
        barmode='stack',
        xaxis_title="Year",
        yaxis_title=" Demand (Pj)",
        legend_title="Sector"
    )
   
    return fig



def create_demand_plots(scenario,
                        data,
                        plot_save_to:str|Path=None):
    
    df = data[data['end_use_fuel'].notna()]
    # Filter sectors to exclude "Total"
    sectors = [sector for sector in df['sector'].unique() if 'total' not in sector.lower()] 

    # Find sector with the most unique variables
    max_variable_sector = max(sectors, key=lambda sec: df[df['sector'] == sec]['end_use_fuel'].nunique())
    variables_list = list(df[df['sector'] == max_variable_sector]['end_use_fuel'].unique())

    # Remove "Total End-use" and ensure "RPP" is present
    variables_list = [var for var in variables_list if var.lower() != "total end-use"]
    if "RPP" not in variables_list:
        variables_list.append("RPP")

    # Assign consistent colors for variables
    variable_colors =bcnexus_const.custom_colors
    # Combined stacked area chart for all sectors
    fig_combined = go.Figure()
    for sector in sectors:
        sector_data = df[df['sector'] == sector]
        aggregated_data = sector_data.groupby('YEAR')['VALUE'].sum().reset_index()
        fig_combined.add_trace(
            go.Scatter(
                x=aggregated_data['YEAR'],
                y=aggregated_data['VALUE'],
                mode='lines',
                name=bcnexus_structure.NamingConvention.get(sector,sector),
                stackgroup='one',
                legendgroup=sector,
            )
        )

    fig_combined.update_layout(
        title=f"Sectoral Energy Demand [{scenario}]",
        height=500,
        width=1400,
        showlegend=True,
    )
    fig_combined.update_xaxes(title_text='Year')
    fig_combined.update_yaxes(title_text='Pj')

    # Create subplots for stacked bar charts
    cols = 2
    rows = -(-len(sectors) // cols)  # Ceiling division

    fig_subplots = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=[bcnexus_structure.NamingConvention.get(sector,sector) for sector in sectors],
        shared_xaxes=False,
        vertical_spacing=0.2,
        horizontal_spacing=0.1,
    )

    legend_shown = set()  # Keep track of shown legends

    # Add stacked bar plots for each sector
    for index, sector in enumerate(sectors):
        row = (index // cols) + 1
        col = (index % cols) + 1
        sector_data = df[df['sector'] == sector]

        for variable in variables_list:
            variable_data = sector_data[sector_data['end_use_fuel'] == variable]
            if not variable_data.empty:
                show_legend_flag = variable not in legend_shown
                fig_subplots.add_trace(
                    go.Bar(
                        x=variable_data['YEAR'],
                        y=variable_data['VALUE'],
                        name=bcnexus_structure.NamingConvention.get(variable, variable).replace('Electricity from transmission', 'Electricity'),
                        marker=dict(color=variable_colors[variable]),
                        legendgroup=variable,
                        showlegend=show_legend_flag,
                    ),
                    row=row,
                    col=col,
                )
                if show_legend_flag:
                    legend_shown.add(variable)
                # Update layout for subplots
                # fig_subplots.update_xaxes(title_text='Year')
                fig_subplots.update_yaxes(title_text='Pj')

    fig_subplots.update_layout(
        title=f"End-use Fuel Demand [{scenario}]",
        height=300 * rows,
        width=1300,
        barmode='stack',
        xaxis_title="Year",
        yaxis_title="Demand (Pj)",
    )
    plot_save_to = Path(plot_save_to) if plot_save_to else Path("vis/bccm")
    plot_save_to.mkdir(parents=True, exist_ok=True)
    fig_combined.write_html(plot_save_to/f"Total_Demand_{scenario}.html")
    fig_subplots.write_html(plot_save_to/f"Sectoral_demand_{scenario}.html")
    return fig_combined, fig_subplots


def plot_land_for_power_demand(scenario: str,
                               total_annual_demand_scenario: pd.DataFrame,
                               actual_land_BC: float = 944.7):
    import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
from  pathlib import Path
from bcnexus import constants as bcnexus_const
from bcnexus.clews import model_structure as bcnexus_structure

def create_demand_plot_simplified(df):
    fig = px.area(
        df,
        x="year",
        y=["Commercial", "Industrial", "Residential", "Transportation"],
        title="Sectoral Demand (Canada Energy Future 2023)",
        labels={"value": "Demand", "year": "Year"},
        color_discrete_map={
            "Commercial": "blue",
            "Industrial": "green",
            "Residential": "orange",
            "Transportation": "red"
        }
    )
    fig.update_layout(
        barmode='stack',
        xaxis_title="Year",
        yaxis_title=" Demand (Pj)",
        legend_title="Sector"
    )
   
    return fig



def create_demand_plots(scenario,
                        data,
                        plot_save_to:str|Path=None):
    
    df = data[data['end_use_fuel'].notna()]
    # Filter sectors to exclude "Total"
    sectors = [sector for sector in df['sector'].unique() if 'total' not in sector.lower()] 

    # Find sector with the most unique variables
    max_variable_sector = max(sectors, key=lambda sec: df[df['sector'] == sec]['end_use_fuel'].nunique())
    variables_list = list(df[df['sector'] == max_variable_sector]['end_use_fuel'].unique())

    # Remove "Total End-use" and ensure "RPP" is present
    variables_list = [var for var in variables_list if var.lower() != "total end-use"]
    if "RPP" not in variables_list:
        variables_list.append("RPP")

    # Assign consistent colors for variables
    variable_colors =bcnexus_const.custom_colors
    # Combined stacked area chart for all sectors
    fig_combined = go.Figure()
    for sector in sectors:
        sector_data = df[df['sector'] == sector]
        aggregated_data = sector_data.groupby('YEAR')['VALUE'].sum().reset_index()
        fig_combined.add_trace(
            go.Scatter(
                x=aggregated_data['YEAR'],
                y=aggregated_data['VALUE'],
                mode='lines',
                name=bcnexus_structure.NamingConvention.get(sector,sector),
                stackgroup='one',
                legendgroup=sector,
            )
        )

    fig_combined.update_layout(
        title=f"Sectoral Energy Demand [{scenario}]",
        height=500,
        width=1400,
        showlegend=True,
    )
    fig_combined.update_xaxes(title_text='Year')
    fig_combined.update_yaxes(title_text='Pj')

    # Create subplots for stacked bar charts
    cols = 2
    rows = -(-len(sectors) // cols)  # Ceiling division

    fig_subplots = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=[bcnexus_structure.NamingConvention.get(sector,sector) for sector in sectors],
        shared_xaxes=False,
        vertical_spacing=0.2,
        horizontal_spacing=0.1,
    )

    legend_shown = set()  # Keep track of shown legends

    # Add stacked bar plots for each sector
    for index, sector in enumerate(sectors):
        row = (index // cols) + 1
        col = (index % cols) + 1
        sector_data = df[df['sector'] == sector]

        for variable in variables_list:
            variable_data = sector_data[sector_data['end_use_fuel'] == variable]
            if not variable_data.empty:
                show_legend_flag = variable not in legend_shown
                fig_subplots.add_trace(
                    go.Bar(
                        x=variable_data['YEAR'],
                        y=variable_data['VALUE'],
                        name=bcnexus_structure.NamingConvention.get(variable, variable).replace('Electricity from transmission', 'Electricity'),
                        marker=dict(color=variable_colors[variable]),
                        legendgroup=variable,
                        showlegend=show_legend_flag,
                    ),
                    row=row,
                    col=col,
                )
                if show_legend_flag:
                    legend_shown.add(variable)
                # Update layout for subplots
                # fig_subplots.update_xaxes(title_text='Year')
                fig_subplots.update_yaxes(title_text='Pj')

    fig_subplots.update_layout(
        title=f"End-use Fuel Demand [{scenario}]",
        height=300 * rows,
        width=1300,
        barmode='stack',
        xaxis_title="Year",
        yaxis_title="Demand (Pj)",
    )
    plot_save_to = Path(plot_save_to) if plot_save_to else Path("vis/bccm")
    plot_save_to.mkdir(parents=True, exist_ok=True)
    fig_combined.write_html(plot_save_to/f"Total_Demand_{scenario}.html")
    fig_subplots.write_html(plot_save_to/f"Sectoral_demand_{scenario}.html")
    return fig_combined, fig_subplots


def plot_land_for_power_demand(scenario: str,
                               total_annual_demand_scenario: pd.DataFrame,
                               actual_land_BC: float = 944.7):
    """
    Plot land-use demand for power resources.
    Args:
        total_annual_demand_scenario (pd.DataFrame): DataFrame containing land-use demand data.
        actual_land_BC (float): Actual land area of British Columbia in thousand square kilometers.
    """
    land_demand_for_power_resources = total_annual_demand_scenario[total_annual_demand_scenario['FUEL'] == 'LND4PWR'].copy()

    # Add a new column for the percentage of actual land
    land_demand_for_power_resources['%_actual_land'] = land_demand_for_power_resources['VALUE'] / actual_land_BC * 100

    fig = px.line(
        land_demand_for_power_resources,
        x='YEAR',
        y='VALUE',
        color='sector',
        title=f'Land-use Demand for Power Resource build-up [{scenario}]',
        labels={'VALUE': 'Thousand Sq. Km', 'YEAR': 'Year'},
    )

    # Remove legend
    fig.update_layout(showlegend=False)

    # Add a text annotation about BC land area
    fig.add_annotation(
        x=2022,
        y=land_demand_for_power_resources['VALUE'].max(),
        text=f"BC Land Area: {actual_land_BC} Thousand Sq Km",
        showarrow=False,
        font=dict(size=12, color="black"),
        align="left",
    )

    fig.write_html(f'vis/bccm/land_demand_for_power_resources_{scenario}.html', include_plotlyjs='cdn')
    return fig


""" replaced wth updated version
def create_demand_plots(df):
    # Filter sectors to exclude "Total"
    sectors = [sector for sector in df['sector'].unique() if 'total' not in sector.lower()]

    # Find the sector with the most variables
    max_variable_sector = max(sectors, key=lambda sector: len(
        [variable for variable in df[df['sector'] == sector]['variable'].unique() if 'total' not in variable.lower()]
    ))
    max_variable_list = [variable for variable in df[df['sector'] == max_variable_sector]['variable'].unique() if 'total' not in variable.lower()]
    if 'RPP' not in max_variable_list:
        max_variable_list.append('RPP')
    
    # Define consistent color palette for variables
    palette = px.colors.qualitative.Plotly
    variable_colors = {
        variable: palette[i % len(palette)] for i, variable in enumerate(max_variable_list)
    }

    # Combined stacked area chart for all sectors
    fig_combined = go.Figure()
    for sector in sectors:
        sector_data = df[df['sector'] == sector]
        # Aggregate data by year and sum across all variables for the sector
        aggregated_data = sector_data.groupby('year')['value'].sum().reset_index()
        fig_combined.add_trace(
            go.Scatter(
                x=aggregated_data['year'],
                y=aggregated_data['value'],
                mode='lines',
                name=sector,
                stackgroup='one',  # This enables stacking for the area plot
                line=dict(color=px.colors.qualitative.Dark24[sectors.index(sector) % len(px.colors.qualitative.Dark24)]),
                legendgroup=sector,  # Group legend by sector
            )
        )

    # Update layout for the combined plot
    fig_combined.update_layout(
        title="Sectoral Demands (Canada Energy Future 2023)",
        height=500,
        width=1200,
        showlegend=True,
    )
    fig_combined.update_xaxes(title_text='Year')
    fig_combined.update_yaxes(title_text='Pj')
    
    # Define grid size for subplots
    cols = 2
    rows = -(-len(sectors) // cols)  # Ceiling division for grid rows

    # Create subplots for stacked bar charts
    fig_subplots = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=sectors,
        shared_xaxes=False,
        vertical_spacing=0.2,
        horizontal_spacing=0.1,
    )

    # Add stacked bar plots for each sector
    for index, sector in enumerate(sectors):
        row = (index // cols) + 1
        col = (index % cols) + 1

        # Filter data for the current sector
        sector_data = df[df['sector'] == sector]

        # Ensure all variables in max_variable_list are present
        for variable in max_variable_list:
            variable_data = sector_data[sector_data['variable'] == variable]
            fig_subplots.add_trace(
                go.Bar(
                    x=sorted(sector_data['year'].unique()),  # Sort years for consistency
                    y=variable_data['value'].values if not variable_data.empty else [0] * len(sector_data['year'].unique()),
                    name=variable,  # Variable legend
                    marker=dict(color=variable_colors[variable]),
                    legendgroup=variable,  # Group legend by variable
                    showlegend=(index == 0),  # Show legend only in the first row of subplots
                ),
                row=row,
                col=col,
            )

    # Update layout for subplots
    fig_subplots.update_layout(
        title="End-use Fuel Demand (By Sector)",
        height=300 * rows,
        width=1100,
        barmode='stack',  # Enable stacking for bar charts
    )

    return fig_combined, fig_subplots
"""