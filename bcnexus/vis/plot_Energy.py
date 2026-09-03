"""
Energy plots for the BC Nexus CLEWs model.

Mirrors the call convention of bcnexus.vis.plot_Land: every function takes a
results dataframe and the scenario name, shows the figure, and returns it.

    import bcnexus.vis.plot_Energy as Evis
    Evis.plot_power_generation_annual(result_pack.get_df('ProductionByTechnologyAnnual'), scene)

Generation is reported in PJ on the left axis and GWh on the right axis. Both
axes describe the same data, so no unit conversion happens on the values
themselves and the OSeMOSYS parameter tables stay traceable.
"""

import re
import pandas as pd
import plotly.express as px

# Busbar and delivered electricity carriers, from model_structure.NamingConvention
ELEC_BUS = 'ELCB01'
ELEC_DEL = 'ELCB02'

# Unit conversion, derived from the SI definitions so the ratio stays exact.
# 1 PJ = 1e15 J, 1 GWh = 3.6e12 J.
PJ_TO_GWH = 1e15 / 3.6e12  # 277.7778

# Reference line for BC annual electricity generation, in GWh. Display only,
# never used in a calculation. Replace with the value you cite in the thesis.
BC_GENERATION_GWH = 70_000

# Timeslice geometry. The run's clustering_attributes decide this, so the
# labels are derived from the results themselves; these are only the fallbacks
# used when the slice count does not divide by the cluster count. Pin them for
# a session with set_geometry(hour_grouping=..., n_clusters=...).
N_CLUSTERS = 4
HOUR_GROUPING = 4
BLOCKS_PER_DAY = 24 // HOUR_GROUPING


def set_geometry(hour_grouping=None, n_clusters=None):
    """Pin the timeslice geometry to the clustering_attributes of the run.

        Evis.set_geometry(hour_grouping=hg.value, n_clusters=nc.value)

    Only needed when a result set cannot be read back unambiguously; the plots
    infer the geometry from the slice count first.
    """
    global HOUR_GROUPING, BLOCKS_PER_DAY, N_CLUSTERS
    if hour_grouping:
        HOUR_GROUPING = int(hour_grouping)
        BLOCKS_PER_DAY = max(1, 24 // HOUR_GROUPING)
    if n_clusters:
        N_CLUSTERS = int(n_clusters)
    return {'hour_grouping': HOUR_GROUPING, 'n_clusters': N_CLUSTERS,
            'blocks_per_day': BLOCKS_PER_DAY}


def slice_geometry(timeslices, n_clusters=None):
    """(n_clusters, blocks_per_day, hour_grouping) implied by a result set.

    A run built with hour_grouping=4 and n_clusters=4 carries 24 timeslices as
    four representative days of six blocks. Reading that back from the slice
    count keeps the labels right when the clustering changes, which a module
    level constant cannot do.
    """
    n = len(timeslices) if hasattr(timeslices, '__len__') else int(timeslices)
    clusters = int(n_clusters or N_CLUSTERS)
    if clusters < 1 or n % clusters:
        clusters = N_CLUSTERS if (N_CLUSTERS and n % N_CLUSTERS == 0) else 1
    blocks = max(1, n // max(1, clusters))
    return clusters, blocks, max(1, 24 // blocks)


def slice_labeller(timeslices, n_clusters=None):
    """Build a ts -> 'D2 12h' labeller for the geometry of these results.

    Positions come from the sorted slice ids present, so a result set whose
    TIMESLICE values are not a contiguous 1..N still labels correctly.
    """
    slices = sorted({int(t) for t in timeslices})
    _, blocks, hg = slice_geometry(slices, n_clusters)
    pos = {ts: i for i, ts in enumerate(slices)}

    def label(ts):
        i = pos.get(int(ts))
        if i is None:
            return str(ts)
        return f'D{i // blocks + 1} {(i % blocks) * hg:02d}h'

    return label


def _slice_label(ts):
    """Label one timeslice from the module level geometry.

    Prefer slice_labeller, which derives the geometry from the result set.
    """
    ts = int(ts)
    return (f'D{(ts - 1) // BLOCKS_PER_DAY + 1} '
            f'{((ts - 1) % BLOCKS_PER_DAY) * HOUR_GROUPING:02d}h')


PWR_LABELS = {
    'PWRHYDB': 'Hydro',
    'PWRWNDB': 'Wind',
    'PWRSOLB': 'Solar',
    'PWRBIOB': 'Biomass',
    'PWRNGSB': 'Natural gas',
    'PWRGEOB': 'Geothermal',
    'PWRURNB': 'Nuclear',
    'PWRBSWB': 'Biofuel (switchgrass)',
    'PWRBCWB': 'Biofuel (clearwood)',
}

SOURCE_ORDER = [
    'Hydro', 'Wind', 'Solar', 'Agrivoltaic', 'Biomass',
    'Biofuel (switchgrass)', 'Biofuel (clearwood)', 'Geothermal',
    'Nuclear', 'Natural gas', 'Imports',
]

# Demand side sector codes, from model_structure.EndUseFuels
SECTOR_LABELS = {
    'RES': 'Residential',
    'COM': 'Commercial',
    'IND': 'Industry',
    'TRA': 'Transport',
    'AGR': 'Agriculture',
}

# Carrier codes as they appear inside end use fuel names, e.g. RESNGSB02
FUEL_LABELS = {
    'ELC': 'Electricity',
    'NGS': 'Natural gas',
    'DSL': 'Diesel',
    'GSL': 'Gasoline',
    'HFO': 'Heavy fuel oil',
    'JFL': 'Jet fuel',
    'LPG': 'LPG',
    'RPP': 'Refined petroleum',
    'BIO': 'Biomass',
    'HDG': 'Hydrogen',
}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _source(tech):
    """Map a busbar producer to a display label.

    Power technologies carry vintage or unit numbering (PWRWNDB16, PWRSOLB01),
    so the trailing digits come off before the lookup. Without this every
    vintage becomes its own legend entry.
    """
    if tech.startswith('LNDAGR'):
        return 'Agrivoltaic'
    if tech.startswith(('IMP', 'MIN')):
        return 'Imports'
    base = re.sub(r'\d+$', '', tech)
    return PWR_LABELS.get(base, base)


def _order(sources):
    known = [s for s in SOURCE_ORDER if s in set(sources)]
    return known + [s for s in dict.fromkeys(sources) if s not in known]


def _as_frame(results, variable='UseByTechnology'):
    """Accept a dataframe, a result pack, or a dict of dataframes.

    bcnexus.plots passes its loaded results in more than one shape depending on
    the entry point, so this resolves all three instead of failing on the type.
    """
    if isinstance(results, pd.DataFrame):
        return results
    if hasattr(results, 'get_df'):
        return results.get_df(variable)
    if isinstance(results, dict):
        for key in (variable, variable.replace('Annual', ''), 'ProductionByTechnologyAnnual'):
            if key in results:
                return results[key]
        raise KeyError(f'{variable} not present in the results mapping.')
    raise TypeError(f'Cannot read energy results from {type(results).__name__}.')


def _collapse_timeslice(df):
    """Sum a timeslice level result to annual totals.

    UseByTechnology and ProductionByTechnology carry a TIMESLICE column; their
    Annual counterparts do not. This accepts either shape.
    """
    if 'TIMESLICE' not in df.columns:
        return df
    keys = [c for c in ('REGION', 'TECHNOLOGY', 'FUEL', 'YEAR') if c in df.columns]
    return df.groupby(keys, as_index=False)['VALUE'].sum()


def _split_end_use(fuel):
    """Return (sector, carrier) for an end use fuel code such as RESNGSB02."""
    sector = SECTOR_LABELS.get(fuel[:3])
    carrier = FUEL_LABELS.get(fuel[3:6], fuel[3:6])
    return sector, carrier


def generation_by_source(df):
    """Annual busbar generation by source, in PJ and GWh.

    Filtering on FUEL isolates the electricity output of the LNDAGR cluster
    technologies from their crop output, so agrivoltaic generation appears
    without pulling crop rows into the energy balance.
    """
    gen = df[df['FUEL'] == ELEC_BUS].copy()
    gen['Source'] = gen['TECHNOLOGY'].map(_source)
    out = gen.groupby(['YEAR', 'Source'], as_index=False)['VALUE'].sum()
    out = out.rename(columns={'VALUE': 'PJ'})
    out['GWh'] = out['PJ'] * PJ_TO_GWH
    return out


def consumption_by_sector_fuel(df):
    """Annual final energy consumption by sector and carrier, in PJ.

    Reads the fuel side of the demand technologies. Rows whose FUEL code does
    not resolve to a known sector prefix drop out, which removes upstream and
    conversion flows from the final energy total.
    """
    use = _collapse_timeslice(df).copy()
    parsed = use['FUEL'].astype(str).map(_split_end_use)
    use['Sector'] = [p[0] for p in parsed]
    use['Carrier'] = [p[1] for p in parsed]
    use = use[use['Sector'].notna()]
    out = use.groupby(['YEAR', 'Sector', 'Carrier'], as_index=False)['VALUE'].sum()
    return out.rename(columns={'VALUE': 'PJ'})


def _unit_column(unit):
    """Validate the requested unit and return the dataframe column to plot.

    bcnexus.plots passes the unit as a lowercase string ('gwh'), so the match
    is case insensitive and returns the dataframe column spelling.
    """
    key = str(unit).strip().lower()
    if key not in ('pj', 'gwh'):
        raise ValueError("unit must be 'PJ' or 'GWh'")
    return 'PJ' if key == 'pj' else 'GWh'


# --------------------------------------------------------------------------- #
# plots
# --------------------------------------------------------------------------- #

def plot_power_generation_annual(df, scene, unit='GWh', show_reference=True, show=True):
    """Stacked annual generation by source.

    df: result_pack.get_df('ProductionByTechnologyAnnual')
    unit: 'PJ' or 'GWh'. Call twice to produce both figures.
    """
    col = _unit_column(unit)
    gen = generation_by_source(df)
    if gen.empty:
        raise ValueError(f'No {ELEC_BUS} production found in the results.')

    fig = px.area(gen, x='YEAR', y=col, color='Source',
                  category_orders={'Source': _order(gen['Source'])},
                  title=f'Annual electricity generation by source, {scene}',
                  labels={col: f'Generation ({col})', 'YEAR': 'Year'})

    if show_reference:
        ref = BC_GENERATION_GWH if col == 'GWh' else BC_GENERATION_GWH / PJ_TO_GWH
        fig.add_hline(y=ref, line_dash='dash', line_color='grey', line_width=1,
                      annotation_text=f'BC generation ~{BC_GENERATION_GWH:,} GWh',
                      annotation_position='top left')

    fig.update_layout(legend=dict(title=''), hovermode='x unified')
    if show:
        fig.show()
    return fig


def plot_generation_mix_share(df, scene, show=True):
    """Generation mix as a share of busbar output."""
    gen = generation_by_source(df)
    pivot = gen.pivot(index='YEAR', columns='Source', values='PJ').fillna(0)
    share = (pivot.div(pivot.sum(axis=1), axis=0) * 100).reset_index()
    share = share.melt(id_vars='YEAR', var_name='Source', value_name='Share')

    fig = px.area(share, x='YEAR', y='Share', color='Source',
                  category_orders={'Source': _order(share['Source'])},
                  title=f'Generation mix, share of busbar output, {scene}',
                  labels={'Share': 'Share (%)', 'YEAR': 'Year'})
    fig.update_yaxes(range=[0, 100])
    fig.update_layout(legend=dict(title=''), hovermode='x unified')
    if show:
        fig.show()
    return fig


def plot_agrivoltaic_generation(df, scene, unit='GWh', show=True):
    """Agrivoltaic generation alone, on its own axis."""
    col = _unit_column(unit)
    gen = generation_by_source(df)
    agv = gen[gen['Source'] == 'Agrivoltaic']
    if agv.empty:
        print('No agrivoltaic generation in this run.')
        return None

    fig = px.bar(agv, x='YEAR', y=col,
                 title=f'Agrivoltaic electricity generation, {scene}',
                 labels={col: f'Generation ({col})', 'YEAR': 'Year'})
    if show:
        fig.show()
    return fig


def plot_capacity_annual(df_capacity, scene, show=True):
    """Installed power capacity by source, in GW.

    df_capacity: result_pack.get_df('TotalCapacityAnnual')

    Capacity on the LNDAGR technologies carries land units (1000 km2), so this
    figure covers the power sector only. Report agrivoltaic deployment as land
    area in the land figures and as energy in plot_agrivoltaic_generation.
    """
    cap = df_capacity[df_capacity['TECHNOLOGY'].str.startswith('PWR')].copy()
    cap = cap[~cap['TECHNOLOGY'].str.startswith('PWRTRN')]
    cap['Source'] = cap['TECHNOLOGY'].map(_source)
    cap = cap.groupby(['YEAR', 'Source'], as_index=False)['VALUE'].sum()

    fig = px.area(cap, x='YEAR', y='VALUE', color='Source',
                  category_orders={'Source': _order(cap['Source'])},
                  title=f'Installed power capacity by source, {scene}',
                  labels={'VALUE': 'Capacity (GW)', 'YEAR': 'Year'})
    fig.update_layout(legend=dict(title=''), hovermode='x unified')
    if show:
        fig.show()
    return fig


def plot_generation_by_timeslice(df_ts, scene, years=(2021, 2035, 2050),
                                 n_clusters=None, show=True):
    """Generation by timeslice for selected years.

    df_ts: result_pack.get_df('ProductionByTechnology')
    n_clusters: the run's clustering n_clusters. None infers the geometry from
    the number of slices in the result set.

    Agrivoltaic output concentrates in the summer daytime slices, so this is
    the figure that shows whether the contribution lands when BC needs it.
    """
    elec = df_ts[df_ts['FUEL'] == ELEC_BUS]
    ts = elec[elec['YEAR'].isin(years)].copy()
    if ts.empty:
        print('No timeslice level electricity production for the selected years.')
        return None
    ts['Source'] = ts['TECHNOLOGY'].map(_source)
    ts = ts.groupby(['YEAR', 'TIMESLICE', 'Source'], as_index=False)['VALUE'].sum()
    # geometry from every slice in the result set, not only the plotted years
    labeller = slice_labeller(elec['TIMESLICE'].unique(), n_clusters)
    ts['Label'] = ts['TIMESLICE'].map(labeller)
    slice_order = [labeller(i) for i in sorted(ts['TIMESLICE'].unique())]

    fig = px.bar(ts, x='Label', y='VALUE', color='Source', facet_row='YEAR',
                 category_orders={'Source': _order(ts['Source']),
                                  'Label': slice_order},
                 title=f'Generation by timeslice, {scene}',
                 labels={'VALUE': 'Generation (PJ)', 'Label': 'Timeslice'})
    fig.update_xaxes(tickangle=45)
    fig.for_each_annotation(lambda a: a.update(text=a.text.split('=')[-1]))
    if show:
        fig.show()
    return fig


def plot_combined_stacked_energy_consumption(df, unit='PJ', scene=None, show=True):
    """Final energy consumption, returned as two figures.

    df: result_pack.get_df('UseByTechnology'), timeslice level or annual.
    unit: 'PJ' or 'gwh', case insensitive.

    Returns (sectoral, by_fuel). The first stacks carriers inside one facet per
    sector, the second stacks carriers across the whole nexus. The two figure
    return matches how bcnexus.plots unpacks this call.
    """
    col = _unit_column(unit)
    use = consumption_by_sector_fuel(_as_frame(df, 'UseByTechnology'))
    if use.empty:
        print('No final energy consumption resolved from the results.')
        return None, None

    use['GWh'] = use['PJ'] * PJ_TO_GWH
    suffix = f', {scene}' if scene else ''
    axis = {col: f'Consumption ({col})', 'YEAR': 'Year'}

    sectoral = px.area(use, x='YEAR', y=col, color='Carrier', facet_col='Sector',
                       facet_col_wrap=2,
                       title=f'Final energy consumption by sector{suffix}',
                       labels=axis)
    sectoral.for_each_annotation(lambda a: a.update(text=a.text.split('=')[-1]))
    sectoral.update_layout(legend=dict(title=''), hovermode='x unified')

    agg = use.groupby(['YEAR', 'Carrier'], as_index=False)[['PJ', 'GWh']].sum()
    by_fuel = px.area(agg, x='YEAR', y=col, color='Carrier',
                      title=f'Nexus fuel consumption{suffix}', labels=axis)
    by_fuel.update_layout(legend=dict(title=''), hovermode='x unified')

    if show:
        sectoral.show()
        by_fuel.show()
    return sectoral, by_fuel


def get_annual_generation_plot(df, scene=None, timeslices=None, unit='PJ', show=True):
    """Annual generation by source, from a timeslice level production result.

    df: result_pack.get_df('ProductionByTechnology')
    timeslices: accepted for call compatibility with bcnexus.plots. Summing
    over TIMESLICE already gives the annual total, so the argument only checks
    the result against the slice count the run was built with.
    """
    col = _unit_column(unit)
    frame = _as_frame(df, 'ProductionByTechnology')
    gen = generation_by_source(_collapse_timeslice(frame))
    if gen.empty:
        print(f'No {ELEC_BUS} production found in the results.')
        return None

    if timeslices is not None and 'TIMESLICE' in frame.columns:
        found = frame['TIMESLICE'].nunique()
        expected = len(timeslices) if hasattr(timeslices, '__len__') else int(timeslices)
        if found != expected:
            print(f'[!] {found} timeslices in the results, {expected} expected.')

    suffix = f', {scene}' if scene else ''
    fig = px.area(gen, x='YEAR', y=col, color='Source',
                  category_orders={'Source': _order(gen['Source'])},
                  title=f'Annual electricity generation by source{suffix}',
                  labels={col: f'Generation ({col})', 'YEAR': 'Year'})
    fig.update_layout(legend=dict(title=''), hovermode='x unified')
    if show:
        fig.show()
    return fig


def get_capacity_plot(df, scene=None, investment=False, show=True):
    """Power capacity by source, in GW.

    df: result_pack.get_df('NewCapacity') when investment is True, or
    result_pack.get_df('TotalCapacityAnnual') when it is False.

    Land tier technologies carry capacity in 1000 km2, so they stay out of this
    figure. Report agrivoltaic deployment as area in the land figures.
    """
    cap = _as_frame(df, 'NewCapacity' if investment else 'TotalCapacityAnnual').copy()
    cap = cap[cap['TECHNOLOGY'].str.startswith('PWR')]
    cap = cap[~cap['TECHNOLOGY'].str.startswith('PWRTRN')]
    if cap.empty:
        print('No power sector capacity in the results.')
        return None
    cap['Source'] = cap['TECHNOLOGY'].map(_source)
    cap = cap.groupby(['YEAR', 'Source'], as_index=False)['VALUE'].sum()

    suffix = f', {scene}' if scene else ''
    label = 'Capacity investment' if investment else 'Installed capacity'
    plot = px.bar if investment else px.area
    fig = plot(cap, x='YEAR', y='VALUE', color='Source',
               category_orders={'Source': _order(cap['Source'])},
               title=f'{label} by source{suffix}',
               labels={'VALUE': f'{label} (GW)', 'YEAR': 'Year'})
    fig.update_layout(legend=dict(title=''), hovermode='x unified')
    if show:
        fig.show()
    return fig


def get_generation_timeseries_plot(df, timeslices=None, scene=None, years=None,
                                   n_clusters=None, show=True):
    """Generation by timeslice, from a timeslice level production result.

    This is the entry point bcnexus.plots.get_plots calls, positionally, as
    (RateOfProductionByTechnology, timeslices, scenario). It is a thin wrapper
    over plot_generation_by_timeslice so both call conventions resolve to one
    implementation.

    timeslices: the run's slice list or count. Used to infer the label
    geometry and to warn when the results carry a different slice count.
    years: None picks the first, middle and last year in the results, so the
    figure does not depend on a hard coded horizon.
    """
    frame = _as_frame(df, 'ProductionByTechnology')
    if frame is None or 'TIMESLICE' not in getattr(frame, 'columns', []):
        print('No timeslice level production available; skipping the '
              'generation timeseries plot.')
        return None

    if timeslices is not None:
        found = frame['TIMESLICE'].nunique()
        expected = (len(timeslices) if hasattr(timeslices, '__len__')
                    else int(timeslices))
        if found != expected:
            print(f'[!] {found} timeslices in the results, {expected} expected.')

    if years is None:
        yrs = sorted(frame['YEAR'].unique())
        if not yrs:
            print('No years in the timeslice production result.')
            return None
        years = tuple(dict.fromkeys([yrs[0], yrs[len(yrs) // 2], yrs[-1]]))

    return plot_generation_by_timeslice(frame, scene, years=years,
                                        n_clusters=n_clusters, show=show)


# --------------------------------------------------------------------------- #
# tables
# --------------------------------------------------------------------------- #

def generation_table(df, years=(2021, 2030, 2040, 2050), digits=2):
    """Generation by source in PJ and GWh for the reporting years."""
    gen = generation_by_source(df)
    pj = gen.pivot(index='YEAR', columns='Source', values='PJ').fillna(0)
    years = [y for y in years if y in pj.index]
    table = pd.concat({'PJ': pj.loc[years].round(digits),
                       'GWh': (pj.loc[years] * PJ_TO_GWH).round(0)}, axis=1)
    return table


def agrivoltaic_table(df, years=None, digits=2):
    """Agrivoltaic generation and its share of total busbar output."""
    gen = generation_by_source(df)
    pj = gen.pivot(index='YEAR', columns='Source', values='PJ').fillna(0)
    if 'Agrivoltaic' not in pj.columns:
        print('No agrivoltaic generation in this run.')
        return None
    total = pj.sum(axis=1)
    table = pd.DataFrame({
        'AGV (PJ)': pj['Agrivoltaic'],
        'AGV (GWh)': pj['Agrivoltaic'] * PJ_TO_GWH,
        'Total (PJ)': total,
        'Total (GWh)': total * PJ_TO_GWH,
        'AGV share %': 100 * pj['Agrivoltaic'] / total,
    })
    if years is not None:
        table = table.loc[[y for y in years if y in table.index]]
    return table.round(digits)


def consumption_table(df, years=(2021, 2030, 2040, 2050), digits=2):
    """Final energy consumption by sector and carrier, in PJ."""
    use = consumption_by_sector_fuel(_as_frame(df, 'UseByTechnology'))
    pivot = use.pivot_table(index='YEAR', columns=['Sector', 'Carrier'],
                            values='PJ', aggfunc='sum').fillna(0)
    years = [y for y in years if y in pivot.index]
    return pivot.loc[years].round(digits)