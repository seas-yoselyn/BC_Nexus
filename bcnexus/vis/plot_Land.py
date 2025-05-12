import pandas as pd
from bcnexus import constants 
# import plotly.express as px
import plotly.graph_objects as go


def plot_landuse_for_clusters(data:pd.DataFrame,
                              scenario:str=None):
    
    title_suffix = f" [{scenario}]" if scenario else ""
    data = data[(data['FUEL'] == "LND4PWR")]
    # Grouping data for better stacking
    pivot_df = data.pivot_table(index='YEAR', columns='TECHNOLOGY', values='VALUE', aggfunc='sum', fill_value=0)

    # Create figure
    fig = go.Figure()

    # Add traces for each technology
    for tech in pivot_df.columns:
        fig.add_trace(go.Bar(
            x=pivot_df.index,
            y=pivot_df[tech],
            name=constants.legend_labels[tech]
        ))

    # Update layout
    fig.update_layout(
        barmode='stack',
        title=f'Landuse Technologies {title_suffix}',
        xaxis_title='Year',
        yaxis_title='Thousand Square Km',
        legend_title='Land Clusters'
    )
    
    return fig
