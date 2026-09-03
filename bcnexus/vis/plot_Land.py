"""Land use figures for the BC Nexus CLEWs model.

Every figure is a single call from the notebook and returns a plotly figure,
or None when the input frame holds no matching rows.
"""

import re
from functools import lru_cache
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from bcnexus import constants
from bcnexus.vis import palette


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

# ---------------------------------------------------------------- land tiers
SETS_DIR = "data/clews_data/SETs"
REGION_LAND = "BC1"
LAND_POOL = f"L{REGION_LAND}"
LAND_SUPPLY_TECH = f"MINLND{REGION_LAND}"
ELEC_FUEL = "ELCB01"
PWR_LAND_FUEL = "LND4PWR"

# 1000 km2, Statistics Canada Table 17-10-0009-01
BC_TOTAL_AREA = 925.186

_AREA_UNIT = "Thousand Square Km"
_TOL = 1e-6                       # barrier residue cut

_PWR_LABELS = {
    "PWRNGSB": "Natural gas", "PWRBIOB": "Biomass", "PWRHYDB": "Hydro",
    "PWRWNDB": "Wind", "PWRSOLB": "Solar", "PWRGEOB": "Geothermal",
    "PWRURNB": "Nuclear", "PWRBSWB": "Switchgrass", "PWRBCWB": "Clearwood",
}


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


def _stacked_area(pivot: pd.DataFrame, order=None):
    """Stacked area over a YEAR-indexed pivot, colored from the palette."""
    fig = go.Figure()
    cols = order or pivot.sum().sort_values(ascending=False).index
    for col in cols:
        if col not in pivot.columns:
            continue
        fig.add_trace(go.Scatter(x=pivot.index, y=pivot[col], name=str(col),
                                 stackgroup="one", mode="lines",
                                 line=dict(color=palette.color(col)),
                                 fillcolor=palette.color(col)))
    return fig


# ---------------------------------------------------------------- existing
def plot_landuse_for_clusters(data: pd.DataFrame,
                              scenario: str = None):

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
    fig = _stacked_area(pivot)
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
        fig.add_trace(go.Bar(x=pivot.index, y=pivot[reg], name=reg,
                             marker_color=palette.color(reg)))
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
        fig.add_trace(go.Bar(x=delta.index, y=delta[cls], name=cls,
                             marker_color=palette.color(cls)))
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
                                 mode="lines+markers",
                                 line=dict(color=palette.color(crop))))
    return _layout(fig, f"Effective yield by crop{sfx}", "Mt per 1000 km²", "Crop")


def plot_forest_trajectory(cap: pd.DataFrame, scenario: str = None):
    """Forest area over time with net-change annotation (carbon-stock proxy)."""
    sfx = f" [{scenario}]" if scenario else ""
    d = cap[cap.TECHNOLOGY.str.startswith("LNDFOR")]
    if d.empty:
        return None
    g = d.groupby("YEAR", as_index=False).VALUE.sum()
    fig = go.Figure(go.Scatter(x=g.YEAR, y=g.VALUE, mode="lines+markers",
                               fill="tozeroy", name="Forest",
                               line=dict(color=palette.color("Forest"))))
    net = g.VALUE.iloc[-1] - g.VALUE.iloc[0]
    fig.add_annotation(x=g.YEAR.iloc[-1], y=g.VALUE.iloc[-1],
                       text=f"net {net:+.2f} kkm²", showarrow=True, arrowhead=2)
    return _layout(fig, f"Forest land trajectory{sfx}", "Thousand Square Km")


# ------------------------------------------------- land tiers from the SETs
@lru_cache(maxsize=4)
def _crop_oar_cached(sets_dir: str) -> pd.DataFrame:
    oar = pd.read_csv(Path(sets_dir) / "OutputActivityRatio.csv")
    oar = oar.loc[oar.FUEL.str.startswith("CRP")
                  & oar.TECHNOLOGY.str.startswith("LNDAGR"),
                  ["TECHNOLOGY", "FUEL", "MODE_OF_OPERATION", "YEAR", "VALUE"]]
    oar["MODE_OF_OPERATION"] = oar.MODE_OF_OPERATION.astype(int)
    return oar


@lru_cache(maxsize=4)
def _tiers_cached(sets_dir: str) -> dict:
    """Land technology tier sets, read from the SETs IAR and OAR."""
    iar = pd.read_csv(Path(sets_dir) / "InputActivityRatio.csv")
    oar = pd.read_csv(Path(sets_dir) / "OutputActivityRatio.csv")

    land_tier = set(iar.loc[iar.FUEL == LAND_POOL, "TECHNOLOGY"])

    agv_modes = {int(m) for m in oar.loc[
        oar.TECHNOLOGY.str.startswith("LNDAGR") & (oar.FUEL == "ELCB01"),
        "MODE_OF_OPERATION"].unique()}

    agv = {t for t in land_tier if t.startswith("LNDAGV")}
    lvs = {t for t in land_tier if t.startswith("LNDLVS")}
    crop = {t for t in land_tier
            if t.startswith("LND")
            and t not in agv | lvs
            and len(t) == len("LND") + 5 + len(REGION_LAND)}
    other = land_tier - agv - lvs - crop

    lvs_prod = set(
        oar.loc[oar.FUEL.str.match(r"^LVS(BEF|MIL|PIG|SHP)$"), "TECHNOLOGY"]
    )

    return {"land_tier": land_tier, "crop": crop, "agv": agv,
            "livestock": lvs, "other": other,
            "agv_modes": agv_modes, "lvs_prod": lvs_prod}


def land_tiers(sets_dir=None) -> dict:
    """Classify the land technologies from the SETs IAR and OAR.

    Keys: 'land_tier', 'crop', 'agv', 'livestock', 'other', 'agv_modes',
    'lvs_prod'. Read once per directory and cached; after a rebuild call
    land_tiers.cache_clear().
    """
    return _tiers_cached(str(Path(sets_dir or SETS_DIR).resolve()))


land_tiers.cache_clear = _tiers_cached.cache_clear


def _category(tech: str, tiers: dict) -> str:
    if tech in tiers["agv"]:
        return "Agrivoltaic"
    if tech in tiers["livestock"]:
        return "Livestock"
    if tech in tiers["crop"]:
        return "Crops"
    if tech.startswith("LNDAGR"):
        return "Cropland (cluster tier)"
    code = tech[len("LND"):len("LND") + 3]
    return _LAND_CLASS_LABELS.get(code, _label(tech))


def _crop_of(tech: str) -> str:
    body = tech[len("LND"):-len(REGION_LAND)]
    code = body[3:6] if body.startswith("AGV") else body[:3]
    return _CROP_LABELS.get(code, code)


def _pwr_label(tech: str) -> str:
    stem = re.sub(r"\d+$", "", tech)
    return _PWR_LABELS.get(stem, _label(stem))


def _agricultural(act: pd.DataFrame, tiers: dict) -> pd.DataFrame:
    agr = act[act.TECHNOLOGY.isin(tiers["crop"] | tiers["agv"])].copy()
    if agr.empty:
        return agr
    agr["System"] = agr.TECHNOLOGY.map(
        lambda t: "Agrivoltaic" if t in tiers["agv"] else "Conventional")
    agr["Crop"] = agr.TECHNOLOGY.map(_crop_of)
    return agr


# ------------------------------------------------------- agrivoltaic figures
def plot_land_by_category(act: pd.DataFrame, scenario: str = None,
                          sets_dir=None, supply_line: bool = True):
    """Provincial land by category: crops, agrivoltaic, livestock, cover.

    Draws the BC total area reference and the MINLND supply trace.
    Input: TotalTechnologyAnnualActivity.
    """
    sfx = f" [{scenario}]" if scenario else ""
    tiers = land_tiers(sets_dir)
    d = act[act.TECHNOLOGY.isin(tiers["land_tier"])].copy()
    if d.empty:
        return None
    d["Category"] = d.TECHNOLOGY.map(lambda t: _category(t, tiers))
    pivot = (d.groupby(["YEAR", "Category"]).VALUE.sum()
             .unstack("Category").fillna(0))

    fig = _stacked_area(pivot)
    fig.add_hline(y=BC_TOTAL_AREA, line_dash="dash", line_color="black",
                  line_width=1,
                  annotation_text=f"BC total area {BC_TOTAL_AREA:,.1f}",
                  annotation_position="top left")

    supply = act[act.TECHNOLOGY == LAND_SUPPLY_TECH].set_index("YEAR").VALUE
    if supply_line and not supply.empty:
        fig.add_trace(go.Scatter(x=supply.index, y=supply.values, mode="lines",
                                 name=f"Land supply ({LAND_SUPPLY_TECH})",
                                 line=dict(color="black", width=1)))
    return _layout(fig, f"Total land in BC by category{sfx}",
                   _AREA_UNIT, "Category")


def land_balance(act: pd.DataFrame, sets_dir=None) -> pd.DataFrame:
    """Allocated versus supplied land per year, with the residual gap."""
    tiers = land_tiers(sets_dir)
    allocated = (act[act.TECHNOLOGY.isin(tiers["land_tier"])]
                 .groupby("YEAR").VALUE.sum())
    supplied = act[act.TECHNOLOGY == LAND_SUPPLY_TECH].set_index("YEAR").VALUE
    return pd.DataFrame({"allocated": allocated, "supplied": supplied,
                         "gap": supplied - allocated})


def plot_agricultural_land(act: pd.DataFrame, scenario: str = None,
                           by: str = "system", sets_dir=None):
    """Agricultural land, conventional and agrivoltaic.

    by='system' stacks the two systems; by='crop' splits each system by crop.
    Input: TotalTechnologyAnnualActivity.
    """
    sfx = f" [{scenario}]" if scenario else ""
    agr = _agricultural(act, land_tiers(sets_dir))
    if agr.empty:
        return None

    if by == "crop":
        agr["Label"] = agr.Crop + " (" + agr.System + ")"
        pivot = (agr.groupby(["YEAR", "Label"]).VALUE.sum()
                 .unstack("Label").fillna(0))
        fig = _stacked_area(pivot)
        return _layout(fig, f"Agricultural land by crop and system{sfx}",
                       _AREA_UNIT, "Crop and system")

    pivot = (agr.groupby(["YEAR", "System"]).VALUE.sum()
             .unstack("System").fillna(0))
    fig = _stacked_area(pivot, order=["Conventional", "Agrivoltaic"])
    return _layout(fig, f"Agricultural land, conventional and agrivoltaic{sfx}",
                   _AREA_UNIT, "System")


def plot_agv_eligible_crops(act: pd.DataFrame, scenario: str = None,
                            sets_dir=None, shared_y: bool = False):
    """Conventional and agrivoltaic land, one panel per AGV eligible crop.

    Panels carry independent y-axes by default, since the agrivoltaic area
    is orders of magnitude below the conventional area in most scenarios.
    Input: TotalTechnologyAnnualActivity.
    """
    sfx = f" [{scenario}]" if scenario else ""
    agr = _agricultural(act, land_tiers(sets_dir))
    if agr.empty:
        return None
    eligible = sorted(agr.loc[agr.System == "Agrivoltaic", "Crop"].unique())
    if not eligible:
        return None

    g = (agr[agr.Crop.isin(eligible)]
         .groupby(["YEAR", "Crop", "System"]).VALUE.sum().reset_index())

    fig = make_subplots(rows=1, cols=len(eligible),
                        shared_yaxes=shared_y,
                        subplot_titles=eligible,
                        horizontal_spacing=0.06)

    for col, crop in enumerate(eligible, start=1):
        for system in ("Conventional", "Agrivoltaic"):
            dd = g[(g.Crop == crop) & (g.System == system)]
            if dd.empty:
                continue
            fig.add_trace(go.Scatter(x=dd.YEAR, y=dd.VALUE, name=system,
                                     stackgroup=f"s{col}", mode="lines",
                                     legendgroup=system,
                                     showlegend=(col == 1),
                                     line=dict(color=palette.color(system)),
                                     fillcolor=palette.color(system)),
                          row=1, col=col)
        fig.update_xaxes(title_text="Year", row=1, col=col)

    fig.update_yaxes(title_text=_AREA_UNIT, row=1, col=1)
    fig.update_layout(title=f"Conventional and agrivoltaic land, eligible crops{sfx}",
                      template="plotly_white", hovermode="x unified",
                      legend_title="System")
    return fig


def agv_share(act: pd.DataFrame, years=None, sets_dir=None) -> pd.DataFrame:
    """Agrivoltaic share of agricultural land, provincial total."""
    agr = _agricultural(act, land_tiers(sets_dir))
    if agr.empty:
        return pd.DataFrame()
    pivot = (agr.groupby(["YEAR", "System"]).VALUE.sum()
             .unstack("System").fillna(0.0))
    pivot["Total"] = pivot.sum(axis=1)
    pivot["AGV share %"] = 100 * pivot.get("Agrivoltaic", 0) / pivot["Total"]
    return pivot.reindex(years) if years else pivot


def plot_land_for_power(df: pd.DataFrame, scenario: str = None):
    """Land occupied by electricity generation, split by generation source.

    Complements plot_energy_land_footprint, which reports only the total.
    Input: UseByTechnology, or ProductionByTechnology.
    """
    sfx = f" [{scenario}]" if scenario else ""
    d = df[df.FUEL == PWR_LAND_FUEL].copy()
    if d.empty:
        return None
    if "TIMESLICE" in d.columns:            # UseByTechnology, timeslice level
        d = d.groupby(["TECHNOLOGY", "YEAR"], as_index=False).VALUE.sum()
    d["Source"] = d.TECHNOLOGY.map(_pwr_label)

    g = d.groupby(["YEAR", "Source"]).VALUE.sum().unstack("Source").fillna(0)
    g = g.loc[:, g.sum() > _TOL]          # drop barrier residue
    if g.empty:
        return None
    fig = _stacked_area(g)
    return _layout(fig, f"Land occupied by electricity generation{sfx}",
                   _AREA_UNIT, "Source")

def plot_crop_production(prod: pd.DataFrame, scenario: str = None):
    """Annual production of every agricultural commodity (CRP fuels).

    Input: ProductionByTechnologyAnnual.
    """
    sfx = f" [{scenario}]" if scenario else ""
    d = prod[prod.FUEL.str.startswith("CRP")].copy()
    if d.empty:
        return None
    d["Crop"] = d.FUEL.str[3:6].map(_CROP_LABELS).fillna(d.FUEL.str[3:6])
    pivot = d.groupby(["YEAR", "Crop"]).VALUE.sum().unstack("Crop").fillna(0)
    fig = _stacked_area(pivot)
    return _layout(fig, f"Crop production{sfx}", "Million tonnes", "Crop")


def plot_crop_production_by_system(bymode: pd.DataFrame, scenario: str = None,
                                   sets_dir=None, shared_y: bool = False):
    """Production of the AGV eligible crops, conventional versus agrivoltaic.

    Reconstructed as activity by mode times the output activity ratio, since
    both systems share the LNDAGR cluster technologies and differ only by
    mode. Input: TotalAnnualTechnologyActivityByMode.
    """
    sfx = f" [{scenario}]" if scenario else ""
    tiers = land_tiers(sets_dir)
    oar = _crop_oar_cached(str(Path(sets_dir or SETS_DIR).resolve()))

    d = bymode[bymode.TECHNOLOGY.str.startswith("LNDAGR")].copy()
    if d.empty or oar.empty:
        return None
    d["MODE_OF_OPERATION"] = d.MODE_OF_OPERATION.astype(int)
    d = d.merge(oar, on=["TECHNOLOGY", "MODE_OF_OPERATION", "YEAR"],
                suffixes=("_act", "_oar"))
    if d.empty:
        return None
    d["VALUE"] = d.VALUE_act * d.VALUE_oar
    d["System"] = d.MODE_OF_OPERATION.map(
        lambda m: "Agrivoltaic" if m in tiers["agv_modes"] else "Conventional")
    d["Crop"] = d.FUEL.str[3:6].map(_CROP_LABELS).fillna(d.FUEL.str[3:6])

    eligible = sorted(d.loc[d.System == "Agrivoltaic", "Crop"].unique())
    if not eligible:
        return None
    g = (d[d.Crop.isin(eligible)]
         .groupby(["YEAR", "Crop", "System"]).VALUE.sum().reset_index())

    fig = make_subplots(rows=1, cols=len(eligible), shared_yaxes=shared_y,
                        subplot_titles=eligible, horizontal_spacing=0.06)
    for col, crop in enumerate(eligible, start=1):
        for system in ("Conventional", "Agrivoltaic"):
            dd = g[(g.Crop == crop) & (g.System == system)]
            if dd.empty:
                continue
            fig.add_trace(go.Scatter(x=dd.YEAR, y=dd.VALUE, name=system,
                                     stackgroup=f"p{col}", mode="lines",
                                     legendgroup=system,
                                     showlegend=(col == 1),
                                     line=dict(color=palette.color(system)),
                                     fillcolor=palette.color(system)),
                          row=1, col=col)
        fig.update_xaxes(title_text="Year", row=1, col=col)
    fig.update_yaxes(title_text="Million tonnes", row=1, col=1)
    fig.update_layout(title=f"Crop production by system{sfx}",
                      template="plotly_white", hovermode="x unified",
                      legend_title="System")
    return fig