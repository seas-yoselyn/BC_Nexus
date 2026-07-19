"""
Harmonized colour palette for all BCNexus plots.

Author: Md Eliasinul Islam

Single source of truth so the same legend entry gets the same colour in every
figure (and across scenarios). Seeded from config/dashboard.yaml
(custom_colors + colors_name_mapping) and extended with the crop, land-cover,
water and cost entries used by the newer C/L/E/W plots.

Usage
-----
    from bcnexus.vis import palette

    px.bar(df, x='YEAR', y='VALUE', color='Technology',
           color_discrete_map=palette.map_for(df['Technology']))

    # or, for graph_objects figures built trace-by-trace:
    fig.add_trace(go.Bar(..., name=lbl, marker_color=palette.color(lbl)))

    # last resort, after a figure exists:
    palette.harmonize(fig)
"""
from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------- base palette
# Kept identical to config/dashboard.yaml so existing figures don't shift.
POWER = {
    "Wind": "#DDB3F9", "Natural Gas": "#D27A78", "Biomass/Biofuel": "#5BAB59",
    "Hydro": "#86B4D8", "Solar": "#FEE566", "Geothermal": "#B067B3",
    "Nuclear": "#808080", "Power Import": "#FF0000", "Power Export": "#008000",
    "Coal": "#4A4A4A", "Battery": "#7FD4C1", "Storage": "#7FD4C1",
    "Transmission": "#9AA5B1",
}
FUELS = {
    "Carbon Capture and Storage": "#FF6347", "Hydrogen": "#00FFFF",
    "Biomass": "#A52A2A", "Diesel": "#FFA500", "Electricity": "#008000",
    "Gasoline": "#DC143C", "Heavy Fuel Oil": "#800000", "Jet Fuel": "#00008B",
    "Liquefied Petroleum Gas": "#FF1493", "Natural gas": "#D27A78",
    "Refined Petroleum Products": "#B8860B", "Solar PV": "#FEE566",
}
SECTORS = {
    "Agricultural": "#C57F7B", "Agriculture": "#C57F7B",
    "Commercial": "#65B465", "Industrial": "#B3B3B3", "Industry": "#B3B3B3",
    "Residential": "#87B4D7", "Transport": "#676767", "Power": "#86B4D8",
    "CCS": "#FF6347",
}
LAND_CLUSTERS = {
    "Land resource - Cluster 1": "#DDB3F9", "Land resource - Cluster 2": "#D27A78",
    "Land resource - Cluster 3": "#5BAB59", "Land resource - Cluster 4": "#86B4D8",
    "Land resource - Cluster 5": "#FEE566", "Land resource - Cluster 6": "#B067B3",
    "Land resource - Cluster 7": "#808080",
    "C01": "#DDB3F9", "C02": "#D27A78", "C03": "#5BAB59", "C04": "#86B4D8",
    "C05": "#FEE566", "C06": "#B067B3", "C07": "#808080",
}

# ---------------------------------------------------------------- extensions
# Land covers: earth-tone family, deliberately distinct from crop greens.
LAND_COVER = {
    "Agriculture (clusters)": "#C57F7B", "Forest": "#2E6B3E",
    "Grassland": "#9CBF6B", "Barren": "#C4B39A", "Built-up": "#7A7A85",
    "Water bodies": "#4169E1", "Other agricultural land": "#D9C08C",
}
# Crops: distinguishable sequence, warm->cool, colour-blind friendly ordering.
CROPS = {
    "Alfalfa": "#6B8E23", "Barley": "#DAA520", "Maize": "#F4C542",
    "Oats": "#C2A25B", "Peas": "#7BB661", "Potatoes": "#B5651D",
    "Canola": "#FFD400", "Rye": "#8B7355", "Wheat": "#E3B23C",
    "Other crops": "#A9A9A9",
}
WATER = {
    "Precipitation": "#7EC8E3", "Surface water": "#4169E1",
    "Groundwater recharge": "#1F4E9C", "Evapotranspiration": "#9FD8CB",
    "Agriculture withdrawal": "#C57F7B", "Public supply": "#65B465",
    "Power sector water": "#86B4D8", "Public supply water": "#65B465",
    "Irrigated": "#4169E1", "Rainfed": "#9CBF6B",
}
COST = {
    "Capital investment": "#2F6F8F", "Fixed O&M": "#7FA6BF",
    "Variable O&M": "#B7CEDB", "Emissions penalty (disc.)": "#FF6347",
}
EMISSION = {"CO2": "#D9534F", "Net": "#1a202c", "Gross emissions": "#D9534F",
            "CCS captured": "#2E8B57", "Model": "#D9534F", "Target": "#2E8B57"}

# code -> label (mirrors dashboard.yaml legend_labels; extended)
LEGEND_LABELS = {
    "PWRWND": "Wind", "PWRNGS": "Natural Gas", "PWRBIO": "Biomass/Biofuel",
    "PWRHYD": "Hydro", "PWRSOL": "Solar", "PWRGEO": "Geothermal",
    "PWRURN": "Nuclear", "IMPPWR": "Power Import", "EXPPWR": "Power Export",
    "CCS": "Carbon Capture and Storage", "HDG": "Hydrogen", "BIO": "Biomass",
    "DSL": "Diesel", "ELCB02": "Electricity", "GSL": "Gasoline",
    "HFO": "Heavy Fuel Oil", "HYD": "Hydro", "JFL": "Jet Fuel",
    "LPG": "Liquefied Petroleum Gas", "NGS": "Natural Gas",
    "RPP": "Refined Petroleum Products", "WTRSURBC1": "Surface water",
    "SOL": "Solar", "WND": "Wind",
    "RES": "Residential", "IND": "Industrial", "TRA": "Transport",
    "AGR": "Agricultural", "COM": "Commercial",
    "DEMRES": "Residential", "DEMIND": "Industrial", "DEMTRA": "Transport",
    "DEMAGR": "Agricultural", "DEMCOM": "Commercial",
}

# merged lookup (later dicts win only where keys are new)
PALETTE: dict[str, str] = {}
for _d in (POWER, FUELS, SECTORS, LAND_CLUSTERS, LAND_COVER, CROPS, WATER,
           COST, EMISSION):
    for _k, _v in _d.items():
        PALETTE.setdefault(_k, _v)

# fallback cycle for anything unmapped (kept away from the assigned hues)
FALLBACK = ["#5B7DB1", "#E08A5B", "#7FB069", "#B45B78", "#8F7FB0",
            "#C7A76C", "#6FA8A0", "#A0785A", "#98A6AD", "#D4A5A5"]

# ---------------------------------------------------------------- canonicalise
# Two label vocabularies exist in the codebase and must map to ONE colour:
#   dashboard.yaml legend_labels : "Natural Gas", "Heavy Fuel Oil", "Industrial"
#   model_structure.NamingConvention : "Natural gas", "Heavy fuel oil", "Industry"
# Everything is matched case-insensitively after this alias pass.
_ALIASES = {
    # fuels
    "natural gas": "Natural Gas", "ngs": "Natural Gas",
    "heavy fuel oil": "Heavy Fuel Oil", "hfo": "Heavy Fuel Oil",
    "jet fuel": "Jet Fuel", "jfl": "Jet Fuel",
    "lpg": "Liquefied Petroleum Gas",
    "liquefied petroleum gas": "Liquefied Petroleum Gas",
    "refined petroleum products": "Refined Petroleum Products",
    "rpp": "Refined Petroleum Products",
    "diesel": "Diesel", "dsl": "Diesel",
    "gasoline": "Gasoline", "gsl": "Gasoline",
    "biomass": "Biomass", "bio": "Biomass",
    "biomass/biofuel": "Biomass/Biofuel",
    "hydrogen": "Hydrogen", "hdg": "Hydrogen",
    "coal": "Coal", "coa": "Coal",
    "uranium": "Nuclear", "urn": "Nuclear", "nuclear": "Nuclear",
    # electricity carriers - all render as one colour
    "electricity": "Electricity", "elc": "Electricity",
    "electricity from transmission": "Electricity",
    "electricity from power plants": "Electricity",
    "elcb01": "Electricity", "elcb02": "Electricity",
    # power technologies
    "hydro": "Hydro", "hydropower": "Hydro", "hyd": "Hydro",
    "wind": "Wind", "wnd": "Wind",
    "solar": "Solar", "solar pv": "Solar", "sol": "Solar",
    "geothermal": "Geothermal", "geo": "Geothermal",
    "carbon capture and storage": "Carbon Capture and Storage",
    "ccs": "Carbon Capture and Storage",
    "power import": "Power Import", "imppwr": "Power Import",
    "power export": "Power Export", "exppwr": "Power Export",
    "battery": "Battery", "battery_storage": "Battery",
    "transmission": "Transmission", "pwrtrn": "Transmission",
    # sectors - "Industry" (NamingConvention) == "Industrial" (dashboard.yaml)
    "industry": "Industrial", "industrial": "Industrial", "ind": "Industrial",
    "residential": "Residential", "res": "Residential",
    "commercial": "Commercial", "com": "Commercial",
    "transport": "Transport", "transportation": "Transport", "tra": "Transport",
    "agriculture": "Agricultural", "agricultural": "Agricultural", "agr": "Agricultural",
    "power": "Hydro",           # power-sector series share the grid blue
    # water
    "surface water": "Surface water", "wtrsurbc1": "Surface water",
    "precipitation": "Precipitation", "groundwater recharge": "Groundwater recharge",
    "evapotranspiration": "Evapotranspiration",
    "public supply": "Public supply", "public supply water": "Public supply",
    "agriculture withdrawal": "Agriculture withdrawal",
    "power sector water": "Power sector water", "power sector": "Power sector water",
    "irrigated": "Irrigated", "rainfed": "Rainfed",
    # emissions
    "co2": "CO2", "net": "Net", "gross emissions": "Gross emissions",
    "ccs captured": "CCS captured", "model": "Model", "target": "Target",
}


def canon(label) -> str:
    """Canonical palette key for a legend label (handles both vocabularies).

    Strips decorations the plots add, e.g. "Surface water (supply)" or
    "Hydro generation (PJ)" -> the underlying commodity.
    """
    if label is None:
        return ""
    t = str(label).strip()
    # drop trailing qualifiers in parentheses: "(supply)", "(PJ)", "(HR)"
    base = t.split(" (")[0].strip() if " (" in t else t
    # drop trailing role words: "Hydro generation" -> "Hydro"
    stem = base
    for tail in (" generation", " capacity", " withdrawal", " use", " supply",
                 " emissions", " level"):
        if stem.casefold().endswith(tail):
            stem = stem[: -len(tail)].strip()
            break
    for cand in (t, base, stem):
        key = cand.casefold()
        if key in _ALIASES:
            return _ALIASES[key]
        if cand in PALETTE:
            return cand
        # case-insensitive direct hit against palette keys
        for pk in PALETTE:
            if pk.casefold() == key:
                return pk
    return base


def is_known(label) -> bool:
    """True when the label resolves to an explicit palette colour."""
    return canon(label) in PALETTE


def load_from_yaml(dashboard_cfg: str | Path = "config/dashboard.yaml") -> None:
    """Merge colours from dashboard.yaml so the yaml stays authoritative.

    Safe to call at import time of a plotting session; silently no-ops if the
    file is missing (e.g. running from a different working directory).
    """
    try:
        import yaml
        cfg = yaml.safe_load(open(dashboard_cfg, encoding="utf-8")) or {}
    except Exception:
        return
    for key in ("colors_name_mapping", "custom_colors"):
        for k, v in (cfg.get(key) or {}).items():
            PALETTE[k] = v                     # yaml wins
            lbl = LEGEND_LABELS.get(k)
            if lbl:
                PALETTE.setdefault(lbl, v)


def color(label: str, i: int = None) -> str:
    """Colour for one legend label; deterministic fallback if unmapped.

    Resolution order: canonical alias -> palette -> code->label map ->
    stable fallback cycle.
    """
    key = canon(label)
    if key in PALETTE:
        return PALETTE[key]
    if label in LEGEND_LABELS and LEGEND_LABELS[label] in PALETTE:
        return PALETTE[LEGEND_LABELS[label]]
    idx = i if i is not None else (abs(hash(str(label))) % len(FALLBACK))
    return FALLBACK[idx % len(FALLBACK)]


def map_for(labels) -> dict:
    """{label: colour} for a series/list of legend labels — pass straight to
    plotly express as `color_discrete_map=`."""
    uniq = list(dict.fromkeys(map(str, labels)))
    return {lbl: color(lbl, i) for i, lbl in enumerate(uniq)}


def harmonize(fig, by: str = "name"):
    """Recolour an existing figure's traces by their legend name.

    Use when a figure was built without a colour map; leaves traces whose
    name is unmapped untouched only if they already carry an explicit colour.
    """
    if fig is None:
        return fig
    for i, tr in enumerate(fig.data):
        name = getattr(tr, by, None)
        if not name:
            continue
        c = color(str(name), i)
        if hasattr(tr, "marker") and tr.marker is not None:
            try:
                tr.marker.color = c
            except Exception:
                pass
        if getattr(tr, "type", "") in ("scatter", "scattergl") and tr.line is not None:
            try:
                tr.line.color = c
            except Exception:
                pass
    return fig


# opportunistic merge at import (no-op when cwd has no config/)
load_from_yaml()
