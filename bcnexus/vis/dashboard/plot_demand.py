import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

def create_demand_plots(df):
    # Filter sectors to exclude "Total"
    sectors = [sector for sector in df['sector'].unique() if 'total' not in sector.lower()]

    # Define color palette
    palette = px.colors.qualitative.Vivid  # Vibrant colors
    sector_colors = {
        sector: px.colors.qualitative.Dark24[i % len(px.colors.qualitative.Dark24)] for i, sector in enumerate(sectors)
    }
    variable_colors = {
        variable: palette[i % len(palette)] for i, variable in enumerate(df['variable'].unique())
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
            line=dict(color=sector_colors[sector]),
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

        sector_data = df[df['sector'] == sector]

        for variable in sector_data['variable'].unique():
            variable_data = sector_data[sector_data['variable'] == variable]
            fig_subplots.add_trace(
                go.Bar(
                    x=variable_data['year'],
                    y=variable_data['value'],
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