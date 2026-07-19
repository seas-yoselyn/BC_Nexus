import pandas as pd
from bcnexus import constants
# import plotly.express as px
import plotly.graph_objects as go


# ---------------------------------------------------------------- labels
# Local fallbacks; constants.legend_labels wins when a key exists there.
_CROP_LABELS = {
    "ALF": "Alfalfa", "BAR": "Barley", "MAI": "Maize", "OAT": "Oats",
    "PEA": "Peas", "PTW": "Potatoes", "RAP": "Canola", "RYE": "Rye",
    "WHE": "Wheat", "OTH": "Other crops",
}
_LAND_CLASS_LABELS = {
    "AGR": "Agriculture", "FOR": "Forest", "GRS": "Grassland",
    "BAR": "Barren", "BLT": "Built-up", "WAT": "Water bodies",
}

# GAEZ input regimes used in mode/fuel suffixes.
_REGIMES = {"HI": "high-input irrigated", "II": "interm.-input irrigated",
            "HR": "high-input rainfed", "IR": "interm.-input rainfed",
            "LR": "low-input rainfed"}
_REGIME_RE = "|".join(_REGIMES)          # 'HI|II|HR|IR|LR'
_IRRIGATED = {"HI", "II"}

# Operation-mode ordering of the model (1-based; source: optn_mds list).
# Crops 1-50 = <CROP><REGIME>; 51-56 land covers; 57 storage discharge.
_MODE_CROPS = ["ALF", "BAR", "MAI", "OAT", "OTH", "PEA", "PTW", "RAP", "RYE", "WHE"]
_MODE_TAIL = ["Barren and sparsely vegetated land", "Forest land",
              "Grassland & woodland", "Built-up land", "Water bodies",
              "Other agricultural land", "Storage Discharging Mode"]

def get_mode_names(readable: bool = True) -> dict:
    """{mode_int: name} for the model's MODE_OF_OPERATION ordering.

    readable=True -> 'Barley (HR)'; False -> raw 'BARHR' codes.
    """
    names = {}
    i = 1
    for crop in _MODE_CROPS:
        for reg in ["HI", "II", "HR", "IR", "LR"]:
            names[i] = (f"{_CROP_LABELS.get(crop, crop)} ({reg})"
                        if readable else f"{crop}{reg}")
            i += 1
    for tail in _MODE_TAIL:
        names[i] = tail
        i += 1
    return names

def _label(key: str) -> str:
    return getattr(constants, "legend_labels", {}).get(key, key)


def _layout(fig, title, ytitle, legend_title=""):
    fig.update_layout(title=title, xaxis_title="Year", yaxis_title=ytitle,
                      legend_title=legend_title, template="plotly_white",
                      hovermode="x unified")
    return fig


# ---------------------------------------------------------------- existing
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


# ---------------------------------------------------------------- new plots
def plot_land_area_by_crop(prod: pd.DataFrame, scenario: str = None):
    """Stacked area of land occupied per crop (fuels L<crop><HI|HR>...).

    Shows what agricultural land is used FOR — the counterpart of the
    cluster plot, which shows where. Input: ProductionByTechnologyAnnual.
    """
    sfx = f" [{scenario}]" if scenario else ""
    d = prod[prod.FUEL.str.match(r"^L[A-Z]{3}(" + _REGIME_RE + r")")].copy()
    if d.empty:
        return None
    d["Crop"] = d.FUEL.str[1:4].map(_CROP_LABELS).fillna(d.FUEL.str[1:4])
    g = d.groupby(["YEAR", "Crop"], as_index=False).VALUE.sum()
    pivot = g.pivot(index="YEAR", columns="Crop", values="VALUE").fillna(0)
    fig = go.Figure()
    for crop in pivot.sum().sort_values(ascending=False).index:
        fig.add_trace(go.Scatter(x=pivot.index, y=pivot[crop], name=crop,
                                 stackgroup="one", mode="lines"))
    return _layout(fig, f"Cropland area by crop{sfx}", "Thousand Square Km", "Crop")


def plot_irrigated_vs_rainfed(prod: pd.DataFrame, scenario: str = None):
    """Irrigated (HI) vs rainfed (HR) cropland, plus irrigation intensity.

    The land-water coupling plot: irrigated-area expansion is what drives
    AGRWAT withdrawal. Secondary axis: BCM of agricultural water per
    thousand km2 of irrigated land (model-sanity indicator).
    Input: ProductionByTechnologyAnnual.
    """
    sfx = f" [{scenario}]" if scenario else ""
    d = prod[prod.FUEL.str.match(r"^L[A-Z]{3}(" + _REGIME_RE + r")")].copy()
    if d.empty:
        return None
    d["Regime"] = d.FUEL.str[4:6].map(lambda r: "Irrigated" if r in _IRRIGATED else "Rainfed")
    g = d.groupby(["YEAR", "Regime"], as_index=False).VALUE.sum()
    pivot = g.pivot(index="YEAR", columns="Regime", values="VALUE").fillna(0)

    fig = go.Figure()
    for reg in pivot.columns:
        fig.add_trace(go.Bar(x=pivot.index, y=pivot[reg], name=reg))
    fig.update_layout(barmode="stack")

    agrwat = prod[prod.FUEL.str.startswith("AGRWAT")]
    if not agrwat.empty and "Irrigated" in pivot.columns:
        w = agrwat.groupby("YEAR").VALUE.sum()
        intensity = (w / pivot["Irrigated"].replace(0, pd.NA)).dropna()
        fig.add_trace(go.Scatter(x=intensity.index, y=intensity.values,
                                 name="Irrigation intensity (BCM/kkm²)",
                                 mode="lines+markers", yaxis="y2",
                                 line=dict(dash="dot")))
        fig.update_layout(yaxis2=dict(title="BCM per 1000 km²",
                                      overlaying="y", side="right",
                                      showgrid=False))
    fig = _layout(fig, f"Irrigated vs rainfed cropland{sfx}",
                  "Thousand Square Km", "Regime")
    # horizontal legend above plot area — keeps it clear of the right axis
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                  xanchor="left", x=0, title=None),
                      margin=dict(r=80))
    return fig


def _delta_bars(d: pd.DataFrame, group_col: str, title: str, legend: str):
    """Shared: group->yearly sum->diff->diverging relative bars."""
    g = d.groupby(["YEAR", group_col]).VALUE.sum().unstack(fill_value=0)
    delta = g.diff().dropna(how="all")
    fig = go.Figure()
    for cls in delta.columns:
        if delta[cls].abs().sum() < 1e-9:
            continue  # skip static classes to keep the plot readable
        fig.add_trace(go.Bar(x=delta.index, y=delta[cls], name=cls))
    fig.update_layout(barmode="relative")
    fig.add_hline(y=0, line_width=1, line_color="grey")
    return _layout(fig, title, "Δ Thousand Square Km", legend)


def plot_landcover_change(cap: pd.DataFrame, scenario: str = None):
    """Year-over-year change in land COVER (supply layer): agricultural
    clusters, forest, grassland, barren, built-up, water bodies.

    Excludes crop-land techs (LND<crop><regime>) — those are the USE layer
    on top of the AGR clusters; stacking both double-counts hectares.
    Input: TotalCapacityAnnual.
    """
    sfx = f" [{scenario}]" if scenario else ""
    d = cap[cap.TECHNOLOGY.str.startswith("LND")].copy()
    # cover techs have NO regime suffix at [6:8] — this separates barren
    # LNDBARBC1 from barley LNDBARHIBC1 (code collision on 'BAR')
    d = d[d.TECHNOLOGY.str[3:6].isin(_LAND_CLASS_LABELS)
          & ~d.TECHNOLOGY.str[6:8].isin(_REGIMES)]
    if d.empty:
        return None
    d["Class"] = d.TECHNOLOGY.str[3:6].map(_LAND_CLASS_LABELS)
    return _delta_bars(d, "Class",
                       f"Land-cover change (year-over-year){sfx}", "Land cover")


def plot_cropland_change(cap: pd.DataFrame, scenario: str = None):
    """Year-over-year change in CROP-land (use layer): LND<crop><regime>
    technologies, labeled by crop. Complements plot_landcover_change —
    reallocation between crops within the agricultural clusters.
    Input: TotalCapacityAnnual.
    """
    sfx = f" [{scenario}]" if scenario else ""
    # regime suffix at [6:8] identifies crop-land techs — includes barley
    # (LNDBAR<regime>) despite its code colliding with barren land 'BAR'
    d = cap[cap.TECHNOLOGY.str.match(
        r"^LND[A-Z]{3}(" + _REGIME_RE + r")")].copy()
    if d.empty:
        return None
    d["Crop"] = d.TECHNOLOGY.str[3:6].map(_CROP_LABELS)\
                                     .fillna(d.TECHNOLOGY.str[3:6])
    return _delta_bars(d, "Crop",
                       f"Crop-land change (year-over-year){sfx}", "Crop")


def plot_landuse_change(cap: pd.DataFrame, scenario: str = None):
    """DEPRECATED: mixed cover and crop layers in one stack (double-counts
    hectares). Kept for backward compatibility; use plot_landcover_change
    and plot_cropland_change instead.
    """
    return plot_landcover_change(cap, scenario)


def plot_energy_land_footprint(prod: pd.DataFrame,
                               newcap: pd.DataFrame = None,
                               scenario: str = None):
    """Land occupied by the power system (fuel LND4PWR), optionally with
    new power capacity overlaid -> visual km2-per-GW of buildout.

    Inputs: ProductionByTechnologyAnnual (+ NewCapacity, optional).
    """
    sfx = f" [{scenario}]" if scenario else ""
    d = prod[prod.FUEL == "LND4PWR"]
    if d.empty:
        return None
    g = d.groupby("YEAR", as_index=False).VALUE.sum()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=g.YEAR, y=g.VALUE, name="Land for power"))
    if newcap is not None:
        nc = newcap[newcap.TECHNOLOGY.str.startswith("PWR") &
                    ~newcap.TECHNOLOGY.str.startswith("PWRTRN")]
        if not nc.empty:
            n = nc.groupby("YEAR", as_index=False).VALUE.sum()
            fig.add_trace(go.Scatter(x=n.YEAR, y=n.VALUE,
                                     name="New power capacity (GW)",
                                     mode="lines+markers", yaxis="y2"))
            fig.update_layout(yaxis2=dict(title="GW", overlaying="y",
                                          side="right", showgrid=False))
    return _layout(fig, f"Energy system land footprint{sfx}",
                   "Thousand Square Km")


def plot_cluster_crop_heatmap(bymode: pd.DataFrame,
                              year: int,
                              mode_names: dict = None,
                              scenario: str = None):
    """Heatmap: yield cluster (rows) x operation mode/crop (cols) for one year.

    Reveals whether high-value crops sit on high-yield clusters, and when
    the optimizer starts using marginal land.
    Input: TotalAnnualTechnologyActivityByMode.
    mode_names: optional {mode_int: 'Crop/landcover name'} from the model's
    operation-modes list; falls back to 'M<idx>'.
    """
    sfx = f" [{scenario}]" if scenario else ""
    d = bymode[bymode.TECHNOLOGY.str.match(r"^LNDAGR.*C\d+$") &
               (bymode.YEAR == year)].copy()
    if d.empty:
        return None
    d["Cluster"] = d.TECHNOLOGY.str.extract(r"(C\d+)$")
    d["Mode"] = d.MODE_OF_OPERATION.map(mode_names or get_mode_names())\
                 .fillna("M" + d.MODE_OF_OPERATION.astype(str))
    g = d.pivot_table(index="Cluster", columns="Mode", values="VALUE",
                      aggfunc="sum", fill_value=0)
    g = g.loc[:, g.sum() > 0]
    fig = go.Figure(go.Heatmap(z=g.values, x=list(g.columns),
                               y=list(g.index), colorscale="YlGn",
                               colorbar=dict(title="kkm²")))
    fig.update_layout(title=f"Cluster × crop allocation, {year}{sfx}",
                      template="plotly_white")
    return fig


def plot_effective_yield(prod: pd.DataFrame, scenario: str = None):
    """Effective yield per crop: CRP production / crop land area (Mt per kkm²).

    Drift means the model is shifting between yield clusters; compare
    against GAEZ assumptions. Input: ProductionByTechnologyAnnual.
    """
    sfx = f" [{scenario}]" if scenario else ""
    crp = prod[prod.FUEL.str.startswith("CRP")].copy()
    lnd = prod[prod.FUEL.str.match(r"^L[A-Z]{3}(" + _REGIME_RE + r")")].copy()
    if crp.empty or lnd.empty:
        return None
    crp["Crop"] = crp.FUEL.str[3:6]
    lnd["Crop"] = lnd.FUEL.str[1:4]
    p = crp.groupby(["YEAR", "Crop"]).VALUE.sum()
    a = lnd.groupby(["YEAR", "Crop"]).VALUE.sum()
    y = (p / a).dropna().reset_index(name="Yield")
    y["Crop"] = y.Crop.map(_CROP_LABELS).fillna(y.Crop)
    fig = go.Figure()
    for crop, dd in y.groupby("Crop"):
        fig.add_trace(go.Scatter(x=dd.YEAR, y=dd.Yield, name=crop,
                                 mode="lines+markers"))
    return _layout(fig, f"Effective yield by crop{sfx}", "Mt per 1000 km²", "Crop")


def plot_forest_trajectory(cap: pd.DataFrame, scenario: str = None):
    """Forest area over time with net-change annotation (carbon-stock proxy)."""
    sfx = f" [{scenario}]" if scenario else ""
    d = cap[cap.TECHNOLOGY.str.startswith("LNDFOR")]
    if d.empty:
        return None
    g = d.groupby("YEAR", as_index=False).VALUE.sum()
    fig = go.Figure(go.Scatter(x=g.YEAR, y=g.VALUE, mode="lines+markers",
                               fill="tozeroy", name="Forest"))
    net = g.VALUE.iloc[-1] - g.VALUE.iloc[0]
    fig.add_annotation(x=g.YEAR.iloc[-1], y=g.VALUE.iloc[-1],
                       text=f"net {net:+.2f} kkm²", showarrow=True, arrowhead=2)
    return _layout(fig, f"Forest land trajectory{sfx}", "Thousand Square Km")
