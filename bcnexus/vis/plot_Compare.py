"""Side-by-side scenario comparison figures for the BC Nexus CLEWs model.

Every figure is a single call from the notebook and returns a plotly figure.
Scenarios are drawn as panels next to each other in one figure, sharing the
y-axis so the levels are directly comparable, and sharing colours through
bcnexus.vis.palette so a category keeps its colour across every panel.

    import bcnexus.vis.plot_Compare as Cmp

    runs = Cmp.load_runs(['Base_Current_Measure', 'CEF_High',
                          'AGV_SUB', 'AGV_SUB_HIGH'])
    Cmp.compare_land_for_power(runs)
    Cmp.compare_generation(runs)
    Cmp.compare_agricultural_land(runs)

The category extraction is not reimplemented here: it reuses the tier and
source classification already in plot_Land and plot_Energy, so a comparison
panel and its single-scenario counterpart always agree.

Two layouts are available. `panels` puts one scenario per panel and is the
default for anything with a stacked category breakdown. `trend` puts every
scenario on a single axis, which suits scalar indicators (a share, a total, an
intensity) where the comparison is the whole point; pass kind='bar', 'area' or
'line' to choose how those are drawn. `trend` never stacks the scenarios,
in any mode - a stack reads as a total, and scenarios are alternative futures
rather than components of one.
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from bcnexus.vis import palette
from bcnexus.vis import plot_Land as Lvis
from bcnexus.vis import plot_Energy as Evis

try:                                   # optional: only needed by the loader
    from bcnexus.clews.datapackage import GetDataPackage
except Exception:                      # pragma: no cover
    GetDataPackage = None

# Run directory layout: results/clews/Model_<algo>_<scene>/<N>ts/<date>/result_csvs_<solver>
RESULTS_ROOT = "results/clews"
MAX_COLS = 4                           # panels per row before wrapping
PANEL_HEIGHT = 430                     # px for a single row of panels
MIN_PANEL_HEIGHT = 360                 # below this the bottom legend collides
# Reporting years for the bar figures. Every year of the horizon makes 120
# bars across four scenarios, which reads as noise; these are the milestones
# the results get discussed at.
MILESTONE_YEARS = (2021, 2025, 2030, 2035, 2040, 2045, 2050)
MAX_BAR_LABELS = 16                    # above this, auto value labels collide


# --------------------------------------------------------------------------- #
# loading runs
# --------------------------------------------------------------------------- #

def find_runs(scenarios=None, results_root=RESULTS_ROOT,
              storage_algorithm="Kotzur", timeslices=None, date=None,
              solver="gurobi", quiet=False):
    """Resolve each scenario to its result_csvs directory on disk.

    scenarios: names in the order you want them plotted. None discovers every
    Model_<algo>_* directory under results_root.
    timeslices: the '24ts' folder, as an int or a string. None takes the only
    one present, or the largest when a scenario has several.
    date: a 'YYYY_MM_DD' run folder. None takes the most recent, which is what
    you want after a re-run.

    Returns {scenario: Path}. Scenarios with no usable directory are reported
    and left out rather than raising, so one missing run does not block the
    other three.
    """
    root = Path(results_root)
    prefix = f"Model_{storage_algorithm}_"

    if scenarios is None:
        scenarios = sorted(p.name[len(prefix):] for p in root.glob(prefix + "*")
                           if p.is_dir())

    found, missing = {}, []
    for scene in scenarios:
        base = root / f"{prefix}{scene}"
        if not base.is_dir():
            missing.append((scene, f"no directory {base}"))
            continue

        ts_dirs = [p for p in base.iterdir() if p.is_dir() and p.name.endswith("ts")]
        if timeslices is not None:
            want = str(timeslices).removesuffix("ts") + "ts"
            ts_dirs = [p for p in ts_dirs if p.name == want]
        if not ts_dirs:
            missing.append((scene, f"no timeslice folder in {base}"))
            continue
        ts_dir = max(ts_dirs, key=lambda p: _ts_count(p.name))

        run_dirs = [p for p in ts_dir.iterdir() if p.is_dir()
                    and (p / f"result_csvs_{solver}").is_dir()]
        if date is not None:
            run_dirs = [p for p in run_dirs if p.name == date]
        if not run_dirs:
            missing.append((scene, f"no result_csvs_{solver} under {ts_dir}"))
            continue

        newest = max(run_dirs, key=lambda p: p.name)   # YYYY_MM_DD sorts as text
        found[scene] = newest / f"result_csvs_{solver}"

    if not quiet:
        for scene, path in found.items():
            print(f"  {scene:24s} {path}")
        for scene, why in missing:
            print(f"  {scene:24s} SKIPPED - {why}")
    return found


def _ts_count(name):
    stem = name.removesuffix("ts")
    return int(stem) if stem.isdigit() else -1


def load_runs(scenarios=None, results_root=RESULTS_ROOT,
              storage_algorithm="Kotzur", timeslices=None, date=None,
              solver="gurobi"):
    """{scenario: GetDataPackage} for every scenario that has results.

    Insertion order follows the scenarios argument, and that is the panel
    order in every comparison figure.
    """
    if GetDataPackage is None:                        # pragma: no cover
        raise ImportError("bcnexus.clews.datapackage is unavailable.")
    paths = find_runs(scenarios, results_root, storage_algorithm,
                      timeslices, date, solver)
    return {scene: GetDataPackage(path) for scene, path in paths.items()}


def load_one(scenario, **kw):
    """The result pack for a single scenario, newest run.

        result_pack = Cmp.load_one('CEF_High')

    For the single-scenario figures. When `runs` is already loaded, index it
    instead - runs['CEF_High'] - which avoids re-reading the CSVs.
    """
    runs = load_runs([scenario], **kw)
    if scenario not in runs:
        raise FileNotFoundError(f"no results found for scenario {scenario!r}")
    return runs[scenario]


def _df(pack, variable):
    """Pull one result table out of a pack, a dict of frames, or a frame."""
    if pack is None:
        return None
    if isinstance(pack, pd.DataFrame):
        return pack
    if hasattr(pack, "get_df"):
        return pack.get_df(variable)
    if isinstance(pack, dict):
        return pack.get(variable)
    raise TypeError(f"Cannot read results from {type(pack).__name__}.")


# --------------------------------------------------------------------------- #
# layout engines
# --------------------------------------------------------------------------- #

def _tidy(d, category="Category", value="VALUE", x="YEAR"):
    """Normalise an extractor result to a YEAR x category pivot."""
    if d is None or len(d) == 0:
        return None
    if isinstance(d, pd.Series):
        d = d.rename(value).reset_index()
        d[category] = value
    if category not in d.columns:                     # single unnamed series
        d = d.copy()
        d[category] = value
    p = d.pivot_table(index=x, columns=category, values=value,
                      aggfunc="sum").fillna(0.0)
    return p if not p.empty else None


def _rgba(colour, alpha):
    """'#0F8B8D' -> 'rgba(15,139,141,0.45)' for translucent area fills.

    Overlaid scenario areas have to be see-through or the last one drawn hides
    the rest; plotly needs rgba for that, and the palette stores hex.
    """
    c = str(colour).lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        return colour
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def _shared_order(pivots, order=None):
    """One category order for every panel, so the stacks read the same way."""
    totals = {}
    for p in pivots.values():
        if p is None:
            continue
        for col, tot in p.sum().items():
            totals[col] = totals.get(col, 0.0) + float(tot)
    cats = sorted(totals, key=lambda c: -totals[c])
    if callable(order):
        return [c for c in order(cats) if c in totals]
    if order:
        return [c for c in order if c in totals] + [c for c in cats if c not in order]
    return cats


def panels(runs, extract, title, ytitle, legend_title="", kind="area",
           shared_y=True, order=None, xtitle="Year", height=None,
           max_cols=MAX_COLS, percent=False, show=True):
    """One panel per scenario, side by side, in a single figure.

    extract: pack -> tidy frame with columns [YEAR, Category, VALUE], or a
    YEAR-indexed Series for a single-category metric.
    kind: 'area' stacks, 'bar' stacks bars, 'line' draws unstacked lines.
    shared_y: keep one y-scale across panels. On by default, because an
    independent scale per panel makes scenarios look alike when they are not.
    """
    pivots = {scene: _tidy(extract(pack)) for scene, pack in runs.items()}
    if not any(p is not None for p in pivots.values()):
        print(f"No data for any scenario: {title}")
        return None

    cats = _shared_order(pivots, order)
    names = list(pivots)
    cols = min(max_cols, len(names)) or 1
    rows = -(-len(names) // cols)

    fig = make_subplots(rows=rows, cols=cols, shared_yaxes=shared_y,
                        subplot_titles=names, horizontal_spacing=0.035,
                        vertical_spacing=0.12)

    seen = set()
    for i, scene in enumerate(names):
        r, c = divmod(i, cols)
        r, c = r + 1, c + 1
        p = pivots[scene]
        if p is None:
            fig.add_annotation(text="no data", showarrow=False,
                               xref=f"x{i + 1} domain", yref=f"y{i + 1} domain",
                               x=0.5, y=0.5)
            continue
        for cat in cats:
            if cat not in p.columns:
                continue
            colour = palette.color(cat)
            first = cat not in seen
            seen.add(cat)
            if kind == "bar":
                trace = go.Bar(x=p.index, y=p[cat], name=str(cat),
                               marker_color=colour, legendgroup=str(cat),
                               showlegend=first)
            elif kind == "line":
                trace = go.Scatter(x=p.index, y=p[cat], name=str(cat),
                                   mode="lines", line=dict(color=colour),
                                   legendgroup=str(cat), showlegend=first)
            else:
                trace = go.Scatter(x=p.index, y=p[cat], name=str(cat),
                                   mode="lines", stackgroup=f"s{i}",
                                   line=dict(color=colour, width=0.5),
                                   fillcolor=colour, legendgroup=str(cat),
                                   showlegend=first)
            fig.add_trace(trace, row=r, col=c)

    # One x title per row, under the leftmost panel: four identical "Year"
    # labels are noise, and they are what the bottom legend collides with.
    for r in range(1, rows + 1):
        fig.update_yaxes(title_text=ytitle, row=r, col=1)
        fig.update_xaxes(title_text=xtitle, row=r, col=1)
    if percent:
        fig.update_yaxes(range=[0, 100])

    # The legend sits under the panels, so it has to clear the x-axis title.
    # Its y is a paper fraction, so a fixed pixel allowance is divided by the
    # real figure height; below MIN_PANEL_HEIGHT there is no room for the
    # title, panels, axis title and legend at once, so the height is raised
    # to keep the layout from degenerating.
    total_height = max(height or PANEL_HEIGHT * rows, MIN_PANEL_HEIGHT * rows)
    fig.update_layout(
        title=title, template="plotly_white", barmode="stack",
        height=total_height, hovermode="x unified",
        legend=dict(title=legend_title or None, orientation="h",
                    yanchor="top", y=-(78 / total_height), xanchor="left",
                    x=0, font=dict(size=11)),
        margin=dict(t=90, b=120))
    if show:
        fig.show()
    return fig


def _num(v, span):
    """Format a bar label at a precision suited to the values on the axis."""
    if v is None or pd.isna(v):
        return ""
    if span < 10:
        return f"{v:,.2f}"
    if span < 100:
        return f"{v:,.1f}"
    return f"{v:,.0f}"


def trend(runs, extract, title, ytitle, xtitle="Year", markers=True,
          height=460, kind="line", years=None, opacity=0.45, log_y=False,
          labels=None, show=True):
    """One series per scenario on a single axis, for scalar indicators.

    extract: pack -> YEAR-indexed Series, or a frame whose VALUE column is
    summed by YEAR. Scenario colours come from the palette, so a scenario
    keeps its colour across every trend figure.

    kind:
        'line'  one line per scenario (default)
        'bar'   grouped bars, side by side within each year
        'area'  translucent filled areas, drawn over one another

    Scenarios are never stacked in any mode. A stack would read as a total,
    and adding two scenarios of the same system together has no meaning -
    they are alternative futures, not components.

    years: which years to draw. kind='bar' defaults to MILESTONE_YEARS, since
    thirty years by four scenarios is 120 bars and unreadable; pass
    years='all' to override that, or any sequence to choose your own.
    Requesting a single year puts the scenario names on the x axis and drops
    the legend, which is the one-bar-per-scenario figure.

    labels: print the value on each bar. None turns them on automatically
    while there are few enough bars to stay legible.

    log_y: log y axis. Worth it when the scenarios span an order of magnitude
    or more - on a linear axis the low scenarios are squashed into the bottom
    few percent of the plot and become unreadable. Zeros drop out of a log
    axis, so the first year of a ramp that starts at zero will not be drawn.
    """
    if kind not in ("line", "bar", "area"):
        raise ValueError("kind must be 'line', 'bar' or 'area'")

    if isinstance(years, str):
        if years.strip().casefold() != "all":
            raise ValueError("years must be 'all' or a sequence of years")
        years = None
    elif years is None and kind == "bar":
        years = MILESTONE_YEARS
    elif isinstance(years, (int, float)):
        years = (int(years),)

    series = {}
    for scene, pack in runs.items():
        s = extract(pack)
        if s is None or len(s) == 0:
            continue
        if isinstance(s, pd.DataFrame):
            s = s.groupby("YEAR").VALUE.sum()
        if years is not None:
            s = s.reindex([y for y in years if y in s.index])
            if s.empty or s.isna().all():
                continue
        series[scene] = s

    if not series:
        print(f"No data for any scenario: {title}")
        return None

    span = max(abs(float(v)) for s in series.values() for v in s.values
               if v is not None and not pd.isna(v))
    n_bars = sum(len(s) for s in series.values())
    if labels is None:
        # 7 milestone years x 4 scenarios is 28 labels, which collide at any
        # sensible figure width; a handful of bars can carry their values
        labels = kind == "bar" and n_bars <= MAX_BAR_LABELS
    single_year = years is not None and len(list(years)) == 1

    fig = go.Figure()
    for scene, s in series.items():
        colour = palette.color(scene)
        x, y = list(s.index), list(s.values)
        if kind == "bar":
            # one year: scenarios go on the x axis, so the names label the
            # bars directly and the legend becomes redundant
            fig.add_trace(go.Bar(
                x=[scene] if single_year else x, y=y, name=scene,
                marker_color=colour, showlegend=not single_year,
                text=[_num(v, span) for v in y] if labels else None,
                textposition="outside" if labels else None,
                texttemplate="%{text}" if labels else None,
                cliponaxis=False))
        elif kind == "area":
            fig.add_trace(go.Scatter(x=x, y=y, name=scene, mode="lines",
                                     line=dict(color=colour, width=1.5),
                                     fill="tozeroy",
                                     fillcolor=_rgba(colour, opacity)))
        else:
            fig.add_trace(go.Scatter(
                x=x, y=y, name=scene,
                mode="lines+markers" if markers else "lines",
                line=dict(color=colour)))

    if single_year:
        # a one-year figure has no year on the x axis, so it belongs in the
        # title or the reader cannot tell which year they are looking at
        year = list(years)[0]
        if str(year) not in title:
            title = f"{title}, {year}"

    fig.update_layout(title=title, yaxis_title=ytitle,
                      xaxis_title="Scenario" if single_year else xtitle,
                      template="plotly_white",
                      hovermode="closest" if single_year else "x unified",
                      height=height, legend_title="Scenario",
                      barmode="group", bargap=0.15, bargroupgap=0.02)
    if kind == "bar" and years is not None:
        fig.update_xaxes(type="category")
    if labels:
        # outside labels need headroom or the top one is clipped
        fig.update_yaxes(automargin=True)
        if not log_y:
            fig.update_yaxes(range=[min(0, -0.02 * span), span * 1.15])
    if log_y:
        fig.update_yaxes(type="log")
    if show:
        fig.show()
    return fig


def save(fig, name, vis_dir="vis", html=True, png=False, scale=2):
    """Write a figure next to your results. Returns the paths written."""
    out = Path(vis_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    if html:
        p = out / f"{name}.html"
        fig.write_html(p, include_plotlyjs="cdn")
        written.append(p)
    if png:                                # needs kaleido
        p = out / f"{name}.png"
        fig.write_image(p, scale=scale)
        written.append(p)
    for p in written:
        print(f"  wrote {p}")
    return written


# --------------------------------------------------------------------------- #
# extractors, reusing the single-scenario classification
# --------------------------------------------------------------------------- #

_ELIGIBLE_KEYS = ("eligible", "agv", "agv_eligible", "agv-eligible")


def _resolve_crops(available, crops):
    """Map requested crop names onto the crop labels present in the results.

    Accepts display labels ('Potatoes'), model codes ('PTW'), and singular or
    partial spellings ('potato'), case-insensitively, so the caller does not
    have to know which vocabulary the figures use. Returns the string
    'eligible' for the auto-detect keywords, which the caller resolves against
    the run, since which crops carry agrivoltaic land is a property of the
    scenario rather than of this function.
    """
    if crops is None:
        return None
    if isinstance(crops, str):
        if crops.strip().casefold() in _ELIGIBLE_KEYS:
            return "eligible"
        crops = [crops]
    labels = {c.casefold(): c for c in available}
    codes = {code.casefold(): label
             for code, label in Lvis._CROP_LABELS.items() if label in available}
    out, missing = [], []
    for want in crops:
        w = str(want).strip().casefold()
        if w in labels:
            out.append(labels[w])
        elif w in codes:
            out.append(codes[w])
        else:
            hits = [c for c in available if c.casefold().startswith(w)]
            if len(hits) == 1:
                out.append(hits[0])
            else:
                missing.append(want)
    if missing:
        print(f"  crops not matched: {missing}. Available: {sorted(available)}")
    return list(dict.fromkeys(out))

def _land_by_category(pack, sets_dir=None):
    act = _df(pack, "TotalTechnologyAnnualActivity")
    if act is None or act.empty:
        return None
    tiers = Lvis.land_tiers(sets_dir)
    d = act[act.TECHNOLOGY.isin(tiers["land_tier"])].copy()
    if d.empty:
        return None
    d["Category"] = d.TECHNOLOGY.map(lambda t: Lvis._category(t, tiers))
    return d.groupby(["YEAR", "Category"], as_index=False).VALUE.sum()


def _agricultural(pack, by="system", sets_dir=None, crops=None):
    act = _df(pack, "TotalTechnologyAnnualActivity")
    if act is None or act.empty:
        return None
    agr = Lvis._agricultural(act, Lvis.land_tiers(sets_dir))
    if agr.empty:
        return None

    if crops is not None:
        sel = _resolve_crops(set(agr.Crop.unique()), crops)
        if sel == "eligible":
            # the crops this run actually deploys agrivoltaics on
            sel = sorted(agr.loc[agr.System == "Agrivoltaic", "Crop"].unique())
        if not sel:
            return None
        agr = agr[agr.Crop.isin(sel)]
        if agr.empty:
            return None

    if by == "crop":
        agr["Category"] = agr.Crop + " (" + agr.System + ")"
    else:
        agr["Category"] = agr.System
    return agr.groupby(["YEAR", "Category"], as_index=False).VALUE.sum()


def _land_for_power(pack):
    use = _df(pack, "UseByTechnology")
    if use is None or use.empty:
        return None
    d = use[use.FUEL == Lvis.PWR_LAND_FUEL].copy()
    if d.empty:
        return None
    if "TIMESLICE" in d.columns:
        d = d.groupby(["TECHNOLOGY", "YEAR"], as_index=False).VALUE.sum()
    d["Category"] = d.TECHNOLOGY.map(Lvis._pwr_label)
    g = d.groupby(["YEAR", "Category"], as_index=False).VALUE.sum()
    keep = g.groupby("Category").VALUE.sum()
    return g[g.Category.isin(keep[keep > Lvis._TOL].index)]


def _irrigation(pack):
    prod = _df(pack, "ProductionByTechnologyAnnual")
    if prod is None or prod.empty:
        return None
    d = prod[prod.FUEL.str.match(r"^L[A-Z]{3}(" + Lvis._REGIME_RE + r")")].copy()
    if d.empty:
        return None
    d["Category"] = d.FUEL.str[4:6].map(
        lambda r: "Irrigated" if r in Lvis._IRRIGATED else "Rainfed")
    return d.groupby(["YEAR", "Category"], as_index=False).VALUE.sum()


def _generation(pack, unit="GWh", variable="ProductionByTechnologyAnnual"):
    df = _df(pack, variable)
    if df is None or df.empty:
        return None
    col = Evis._unit_column(unit)
    gen = Evis.generation_by_source(Evis._collapse_timeslice(df))
    if gen.empty:
        return None
    return gen.rename(columns={"Source": "Category", col: "VALUE"})[
        ["YEAR", "Category", "VALUE"]]


def _generation_share(pack):
    gen = _generation(pack, unit="PJ")
    if gen is None:
        return None
    p = gen.pivot_table(index="YEAR", columns="Category", values="VALUE",
                        aggfunc="sum").fillna(0.0)
    share = p.div(p.sum(axis=1).replace(0, pd.NA), axis=0) * 100
    return share.dropna(how="all").stack().rename("VALUE").reset_index()


def _capacity(pack):
    cap = _df(pack, "TotalCapacityAnnual")
    if cap is None or cap.empty:
        return None
    d = cap[cap.TECHNOLOGY.str.startswith("PWR")
            & ~cap.TECHNOLOGY.str.startswith("PWRTRN")].copy()
    if d.empty:
        return None
    d["Category"] = d.TECHNOLOGY.map(Evis._source)
    return d.groupby(["YEAR", "Category"], as_index=False).VALUE.sum()


def _crop_production(pack):
    prod = _df(pack, "ProductionByTechnologyAnnual")
    if prod is None or prod.empty:
        return None
    d = prod[prod.FUEL.str.startswith("CRP")].copy()
    if d.empty:
        return None
    d["Category"] = d.FUEL.str[3:6].map(Lvis._CROP_LABELS).fillna(d.FUEL.str[3:6])
    return d.groupby(["YEAR", "Category"], as_index=False).VALUE.sum()


def _livestock_production(pack):
    prod = _df(pack, "ProductionByTechnologyAnnual")
    if prod is None or prod.empty:
        return None
    labels = {"BEF": "Beef", "MIL": "Milk", "PIG": "Pork", "SHP": "Sheep"}
    d = prod[prod.FUEL.str.match(r"^LVS(BEF|MIL|PIG|SHP)$")].copy()
    if d.empty:
        return None
    d["Category"] = d.FUEL.str[3:6].map(labels)
    return d.groupby(["YEAR", "Category"], as_index=False).VALUE.sum()


def _production_by_system(pack, crop=None, sets_dir=None):
    """Crop output split conventional vs agrivoltaic, via activity x OAR."""
    bymode = _df(pack, "TotalAnnualTechnologyActivityByMode")
    if bymode is None or bymode.empty:
        return None
    tiers = Lvis.land_tiers(sets_dir)
    oar = Lvis._crop_oar_cached(str(Path(sets_dir or Lvis.SETS_DIR).resolve()))
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
    d["Crop"] = d.FUEL.str[3:6].map(Lvis._CROP_LABELS).fillna(d.FUEL.str[3:6])
    if crop is not None:
        d = d[d.Crop.str.lower() == str(crop).lower()]
        if d.empty:
            return None
    d["Category"] = d.System
    return d.groupby(["YEAR", "Category"], as_index=False).VALUE.sum()


def _agv_series(pack, sets_dir=None, crops=None):
    """Agrivoltaic land area, as a YEAR-indexed Series."""
    agr = _agricultural(pack, by="system", sets_dir=sets_dir, crops=crops)
    if agr is None:
        return None
    d = agr[agr.Category == "Agrivoltaic"]
    return None if d.empty else d.set_index("YEAR").VALUE


def _agv_share_series(pack, sets_dir=None, crops=None):
    agr = _agricultural(pack, by="system", sets_dir=sets_dir, crops=crops)
    if agr is None:
        return None
    p = agr.pivot_table(index="YEAR", columns="Category", values="VALUE",
                        aggfunc="sum").fillna(0.0)
    if "Agrivoltaic" not in p.columns:
        return None
    total = p.sum(axis=1).replace(0, pd.NA)
    return (100 * p["Agrivoltaic"] / total).dropna()


def _agv_generation_series(pack, unit="GWh"):
    gen = _generation(pack, unit=unit)
    if gen is None:
        return None
    d = gen[gen.Category == "Agrivoltaic"]
    return None if d.empty else d.set_index("YEAR").VALUE


def _emissions_series(pack, cumulative=False):
    df = _df(pack, "AnnualEmissions")
    if df is None or df.empty:
        return None
    s = df.groupby("YEAR").VALUE.sum()
    return s.cumsum() if cumulative else s


def _timeslice(pack, year, n_clusters=None):
    df = _df(pack, "ProductionByTechnology")
    if df is None or df.empty:
        return None
    d = df[(df.FUEL == Evis.ELEC_BUS) & (df.YEAR == year)].copy()
    if d.empty:
        return None
    d["Category"] = d.TECHNOLOGY.map(Evis._source)
    g = d.groupby(["TIMESLICE", "Category"], as_index=False).VALUE.sum()
    labeller = Evis.slice_labeller(sorted(d.TIMESLICE.unique()), n_clusters)
    g["Slice"] = g.TIMESLICE.map(labeller)
    return g.rename(columns={"Slice": "YEAR"})[["YEAR", "Category", "VALUE"]]


# --------------------------------------------------------------------------- #
# land use
# --------------------------------------------------------------------------- #

def compare_land_by_category(runs, sets_dir=None, **kw):
    """Provincial land by category, one panel per scenario.

    Input: TotalTechnologyAnnualActivity.
    """
    return panels(runs, lambda p: _land_by_category(p, sets_dir),
                  "Total land in BC by category", Lvis._AREA_UNIT,
                  legend_title="Category", **kw)


def compare_agricultural_land(runs, by="system", crops=None, sets_dir=None,
                              **kw):
    """Agricultural land, conventional and agrivoltaic, one panel per scenario.

    by='system' stacks the two systems; by='crop' splits each by crop.

    crops restricts the land counted, which is what you want when the question
    is about the agrivoltaic-eligible crops rather than the whole farm sector:

        crops=None                  every crop (default)
        crops='eligible'            only crops this run puts agrivoltaics on
        crops=['Maize', 'Potatoes', 'Wheat']    an explicit set

    Labels, model codes ('MAI') and partial spellings ('potato') all resolve.
    Input: TotalTechnologyAnnualActivity.
    """
    label = "by crop and system" if by == "crop" else "conventional and agrivoltaic"
    order = None if by == "crop" else ["Conventional", "Agrivoltaic"]

    if crops is None:
        sfx = ""
    elif isinstance(crops, str) and crops.strip().casefold() in _ELIGIBLE_KEYS:
        sfx = " - agrivoltaic-eligible crops"
    else:
        names = [crops] if isinstance(crops, str) else list(crops)
        sfx = " - " + ", ".join(str(c) for c in names)

    return panels(runs, lambda p: _agricultural(p, by, sets_dir, crops),
                  f"Agricultural land, {label}{sfx}", Lvis._AREA_UNIT,
                  legend_title="System", order=order, **kw)


def compare_land_for_power(runs, **kw):
    """Land occupied by electricity generation, split by source.

    Input: UseByTechnology.
    """
    return panels(runs, _land_for_power,
                  "Land occupied by electricity generation", Lvis._AREA_UNIT,
                  legend_title="Source", **kw)


def compare_irrigated_vs_rainfed(runs, **kw):
    """Irrigated versus rainfed cropland.

    Input: ProductionByTechnologyAnnual.
    """
    return panels(runs, _irrigation, "Irrigated versus rainfed cropland",
                  Lvis._AREA_UNIT, legend_title="Regime", kind="bar",
                  order=["Irrigated", "Rainfed"], **kw)


# --------------------------------------------------------------------------- #
# agrivoltaics
# --------------------------------------------------------------------------- #

def compare_agv_land(runs, crops=None, sets_dir=None, **kw):
    """Agrivoltaic land area, one bar group per year.

    crops restricts the crops counted; see compare_agricultural_land.
    kind='bar' (default), 'area' or 'line'. Bars are drawn at
    MILESTONE_YEARS; pass years='all' for every year, a sequence for your
    own, or a single year for one bar per scenario.
    Input: TotalTechnologyAnnualActivity.
    """
    kw.setdefault("kind", "bar")
    return trend(runs, lambda p: _agv_series(p, sets_dir, crops),
                 "Agrivoltaic land area", Lvis._AREA_UNIT, **kw)


def compare_agv_share(runs, crops=None, sets_dir=None, **kw):
    """Agrivoltaic share of agricultural land, one bar group per year.

    crops='eligible' gives the share of the land that agrivoltaics can
    actually occupy, which is the more meaningful denominator: as a share of
    all BC farmland the number stays near zero whatever the scenario does.
    kind='bar' (default), 'area' or 'line'.
    Input: TotalTechnologyAnnualActivity.
    """
    base = ("eligible cropland" if isinstance(crops, str)
            and crops.strip().casefold() in _ELIGIBLE_KEYS
            else "agricultural land" if crops is None else "selected cropland")
    kw.setdefault("kind", "bar")
    return trend(runs, lambda p: _agv_share_series(p, sets_dir, crops),
                 f"Agrivoltaic share of {base}",
                 f"Share of {base} (%)", **kw)


def compare_agv_generation(runs, unit="GWh", **kw):
    """Agrivoltaic electricity generation, one bar group per year.

    kind='bar' (default), 'area' or 'line'.
    Input: ProductionByTechnologyAnnual.
    """
    col = Evis._unit_column(unit)
    kw.setdefault("kind", "bar")
    return trend(runs, lambda p: _agv_generation_series(p, unit),
                 "Agrivoltaic electricity generation",
                 f"Generation ({col})", **kw)


def compare_agv_production(runs, crop=None, sets_dir=None, **kw):
    """Crop output on conventional versus agrivoltaic systems.

    crop: restrict to one crop, e.g. 'Maize'. None totals the eligible crops.
    Input: TotalAnnualTechnologyActivityByMode.
    """
    sfx = f", {crop}" if crop else ""
    return panels(runs, lambda p: _production_by_system(p, crop, sets_dir),
                  f"Crop production by system{sfx}", "Million tonnes",
                  legend_title="System",
                  order=["Conventional", "Agrivoltaic"], **kw)


# --------------------------------------------------------------------------- #
# energy
# --------------------------------------------------------------------------- #

def compare_generation(runs, unit="GWh", **kw):
    """Annual electricity generation by source, one panel per scenario.

    Input: ProductionByTechnologyAnnual.
    """
    col = Evis._unit_column(unit)
    return panels(runs, lambda p: _generation(p, unit),
                  "Annual electricity generation by source",
                  f"Generation ({col})", legend_title="Source",
                  order=Evis._order, **kw)


def compare_generation_mix(runs, **kw):
    """Generation mix as a share of busbar output, one panel per scenario.

    Input: ProductionByTechnologyAnnual.
    """
    return panels(runs, _generation_share,
                  "Generation mix, share of busbar output", "Share (%)",
                  legend_title="Source", order=Evis._order, percent=True, **kw)


def compare_capacity(runs, **kw):
    """Installed power capacity by source, one panel per scenario.

    Input: TotalCapacityAnnual.
    """
    return panels(runs, _capacity, "Installed power capacity by source",
                  "Capacity (GW)", legend_title="Source",
                  order=Evis._order, **kw)


def compare_generation_by_timeslice(runs, year=2050, n_clusters=None, **kw):
    """Generation by timeslice in one year, one panel per scenario.

    Shows whether agrivoltaic output lands in the slices that need it.
    Input: ProductionByTechnology.
    """
    fig = panels(runs, lambda p: _timeslice(p, year, n_clusters),
                 f"Generation by timeslice, {year}", "Generation (PJ)",
                 legend_title="Source", kind="bar", xtitle="Timeslice",
                 order=Evis._order, **kw)
    if fig is not None:
        fig.update_xaxes(tickangle=45, type="category")
    return fig


# --------------------------------------------------------------------------- #
# food production
# --------------------------------------------------------------------------- #

def compare_crop_production(runs, **kw):
    """Annual crop production by commodity, one panel per scenario.

    Input: ProductionByTechnologyAnnual.
    """
    return panels(runs, _crop_production, "Crop production", "Million tonnes",
                  legend_title="Crop", **kw)


def compare_livestock_production(runs, **kw):
    """Annual livestock production by product, one panel per scenario.

    Input: ProductionByTechnologyAnnual.
    """
    return panels(runs, _livestock_production, "Livestock production",
                  "Million tonnes", legend_title="Product", **kw)


# --------------------------------------------------------------------------- #
# emissions
# --------------------------------------------------------------------------- #

def compare_emissions(runs, targets=True, **kw):
    """Annual net emissions, one line per scenario, with the BC targets.

    Input: AnnualEmissions.
    """
    fig = trend(runs, _emissions_series, "Annual net emissions",
                "Mt CO2e", show=False, **kw)
    if fig is None:
        return None
    if targets:
        from bcnexus import constants as bc
        tg = getattr(bc, "emission_targets", None)
        if tg:
            fig.add_trace(go.Scatter(
                x=tg["years"], y=tg["emissions_MTeCO2"], mode="markers+text",
                text=[f"{y} target" for y in tg["years"]],
                textposition="top center", name="BC emission targets",
                marker=dict(size=12, color="gold", line=dict(width=1,
                                                             color="orange"))))
    fig.show()
    return fig


def compare_cumulative_emissions(runs, budget_Mt=None, **kw):
    """Cumulative net emissions, one line per scenario; optional budget line.

    Input: AnnualEmissions.
    """
    fig = trend(runs, lambda p: _emissions_series(p, cumulative=True),
                "Cumulative net emissions", "Mt CO2e (cumulative)",
                show=False, **kw)
    if fig is None:
        return None
    if budget_Mt is not None:
        fig.add_hline(y=budget_Mt, line_dash="dash", line_color="red",
                      annotation_text=f"budget {budget_Mt:,.0f} Mt")
    fig.show()
    return fig


# --------------------------------------------------------------------------- #
# tables
# --------------------------------------------------------------------------- #

def summary_table(runs, years=(2030, 2040, 2050), sets_dir=None, digits=2):
    """Headline indicators per scenario at the reporting years.

    Rows are (indicator, year), columns are scenarios — the table that goes
    next to the figures in a scenario chapter.
    """
    def at(s, y):
        if s is None or y not in s.index:
            return float("nan")
        return float(s.loc[y])

    out = {}
    for scene, pack in runs.items():
        gen = _generation(pack, unit="GWh")
        gen_tot = (gen.groupby("YEAR").VALUE.sum() if gen is not None else None)
        agv_gen = _agv_generation_series(pack, unit="GWh")
        agr = _agricultural(pack, "system", sets_dir)
        agr_tot = (agr.groupby("YEAR").VALUE.sum() if agr is not None else None)
        agv_land = _agv_series(pack, sets_dir)
        agv_sh = _agv_share_series(pack, sets_dir)
        lfp = _land_for_power(pack)
        lfp_tot = (lfp.groupby("YEAR").VALUE.sum() if lfp is not None else None)
        crop = _crop_production(pack)
        crop_tot = (crop.groupby("YEAR").VALUE.sum() if crop is not None else None)
        emis = _emissions_series(pack)
        cum = _emissions_series(pack, cumulative=True)

        series = {
            "Generation (GWh)": gen_tot,
            "Agrivoltaic generation (GWh)": agv_gen,
            "Agricultural land (kkm2)": agr_tot,
            "Agrivoltaic land (kkm2)": agv_land,
            "Agrivoltaic share (%)": agv_sh,
            "Land for power (kkm2)": lfp_tot,
            "Crop production (Mt)": crop_tot,
            "Emissions (Mt CO2e)": emis,
            "Cumulative emissions (Mt CO2e)": cum,
        }
        out[scene] = {(k, y): at(s, y) for k, s in series.items() for y in years}

    table = pd.DataFrame(out)
    table.index = pd.MultiIndex.from_tuples(table.index,
                                            names=["Indicator", "Year"])
    return table.round(digits)


def compare_all(runs, year=2050, show=True):
    """Every comparison figure in one call. Returns {name: figure}."""
    figs = {
        "land_by_category": compare_land_by_category(runs, show=show),
        "agricultural_land": compare_agricultural_land(runs, show=show),
        "land_for_power": compare_land_for_power(runs, show=show),
        "irrigated_vs_rainfed": compare_irrigated_vs_rainfed(runs, show=show),
        "agv_land": compare_agv_land(runs, show=show),
        "agv_share": compare_agv_share(runs, show=show),
        "agv_generation": compare_agv_generation(runs, show=show),
        "agv_production": compare_agv_production(runs, show=show),
        "generation": compare_generation(runs, show=show),
        "generation_mix": compare_generation_mix(runs, show=show),
        "capacity": compare_capacity(runs, show=show),
        "generation_by_timeslice": compare_generation_by_timeslice(
            runs, year=year, show=show),
        "crop_production": compare_crop_production(runs, show=show),
        "livestock_production": compare_livestock_production(runs, show=show),
        "emissions": compare_emissions(runs, **({} if show else {})),
        "cumulative_emissions": compare_cumulative_emissions(runs),
    }
    return {k: v for k, v in figs.items() if v is not None}
