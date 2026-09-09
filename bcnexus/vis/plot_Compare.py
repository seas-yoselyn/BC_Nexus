"""Side-by-side scenario comparison figures for the BC Nexus CLEWs model.

    import bcnexus.vis.plot_Compare as Cmp

    runs = Cmp.load_runs(['Base_Current_Measure', 'CEF_High',
                          'AGV_SUB', 'AGV_SUB_HIGH'])
    Cmp.compare_agricultural_land(runs)

`panels` draws one scenario per panel, wrapping at MAX_COLS so four scenarios
land as a 2x2 grid sized for a 16:9 slide. `trend` puts every scenario on one
axis. Every figure carries an explicit width, so what the notebook shows is
what gets exported.

Plotly's `shared_yaxes` only ties panels within a row, so a multi-row grid
would otherwise carry one scale per row. `panels` links every panel to the
first when shared_y is set, which keeps scenarios comparable across rows.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from bcnexus.vis import palette
from bcnexus.vis import plot_Land as Lvis
from bcnexus.vis import plot_Energy as Evis

try:
    from bcnexus.clews.datapackage import GetDataPackage
except Exception:                      # pragma: no cover
    GetDataPackage = None

RESULTS_ROOT = "results/clews"
MAX_COLS = 4                           # panels per row before wrapping
PANEL_WIDTH = 235                      # 860 across two columns
PANEL_HEIGHT = 450                     # 600 down two rows
MIN_PANEL_HEIGHT = 340                 # floor of 520, so 600 is not raised
FIG_WIDTH = 720                        # single-axis trend figures
SLIDE_WIDTH = 1280                     # save(..., slide=True), 16:9
SLIDE_HEIGHT = 720
MILESTONE_YEARS = (2030, 2035, 2040, 2045, 2050)
MAX_BAR_LABELS = 16

# The shared palette gives every crop a yellow, so a crop split is unreadable.
# These hues are used instead whenever a figure is keyed on crop.
CROP_HUES = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
             "#937860", "#DA8BC3", "#64B5CD", "#CCB974", "#8C8C8C"]


# --------------------------------------------------------------------------- #
# loading runs
# --------------------------------------------------------------------------- #

def find_runs(scenarios=None, results_root=RESULTS_ROOT,
              storage_algorithm="Kotzur", timeslices=None, date=None,
              solver="gurobi", quiet=False):
    """{scenario: result_csvs Path}. Missing runs are reported, not raised."""
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

        found[scene] = max(run_dirs, key=lambda p: p.name) / f"result_csvs_{solver}"

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
    """{scenario: GetDataPackage}. Insertion order is the panel order."""
    if GetDataPackage is None:                        # pragma: no cover
        raise ImportError("bcnexus.clews.datapackage is unavailable.")
    paths = find_runs(scenarios, results_root, storage_algorithm,
                      timeslices, date, solver)
    return {scene: GetDataPackage(path) for scene, path in paths.items()}


def load_one(scenario, **kw):
    """The result pack for a single scenario, newest run."""
    runs = load_runs([scenario], **kw)
    if scenario not in runs:
        raise FileNotFoundError(f"no results found for scenario {scenario!r}")
    return runs[scenario]


def _df(pack, variable):
    """One result table out of a pack, a dict of frames, or a frame."""
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
# colour
# --------------------------------------------------------------------------- #

def _lighten(colour, t):
    c = str(colour).lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        return colour
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (round(v + (255 - v) * t) for v in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def _rgba(colour, alpha):
    """Hex to rgba, for translucent area fills."""
    c = str(colour).lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        return colour
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def crop_colors(cats):
    """{category: colour} for crop keyed figures.

    One hue per crop, so Maize and Wheat no longer share a yellow. Where the
    label carries a system - 'Maize (Agrivoltaic)' - agrivoltaic keeps the
    full hue and conventional takes a pale version of it, so the pair reads as
    one crop while staying distinguishable.
    """
    crops = sorted({str(c).split(" (")[0] for c in cats})
    hues = {c: CROP_HUES[i % len(CROP_HUES)] for i, c in enumerate(crops)}
    out = {}
    for c in cats:
        base = hues[str(c).split(" (")[0]]
        out[c] = _lighten(base, 0.55) if "(Conventional)" in str(c) else base
    return out


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
    if category not in d.columns:
        d = d.copy()
        d[category] = value
    p = d.pivot_table(index=x, columns=category, values=value,
                      aggfunc="sum").fillna(0.0)
    return p if not p.empty else None


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


def _width(width, default):
    """Pixels, or None to autosize. None takes the default; 'auto' is responsive."""
    if width is None:
        return default
    if isinstance(width, str):
        if width.strip().casefold() != "auto":
            raise ValueError("width must be a number, None or 'auto'")
        return None
    return width


def panels(runs, extract, title, ytitle, legend_title="", kind="area",
           shared_y=True, order=None, xtitle="Year", height=None, width=None,
           max_cols=MAX_COLS, percent=False, colors=None, legend_bottom=120,
           show=True):
    """One panel per scenario, side by side, in a single figure.

    extract: pack -> tidy frame [YEAR, Category, VALUE], or a YEAR-indexed
    Series. kind: 'area' stacks, 'bar' stacks bars, 'line' is unstacked.
    colors: {category: colour} or a callable taking the category list;
    anything it does not cover falls back to the shared palette.
    shared_y ties every panel to one scale, across rows as well as within
    them. legend_bottom is the bottom margin in pixels; raise it when a
    figure carries enough categories to wrap the legend over several rows.
    """
    pivots = {scene: _tidy(extract(pack)) for scene, pack in runs.items()}
    if not any(p is not None for p in pivots.values()):
        print(f"No data for any scenario: {title}")
        return None

    cats = _shared_order(pivots, order)
    cmap = colors(cats) if callable(colors) else dict(colors or {})
    names = list(pivots)
    cols = min(max_cols, len(names)) or 1
    rows = -(-len(names) // cols)

    fig = make_subplots(rows=rows, cols=cols, shared_yaxes=shared_y,
                        subplot_titles=names, horizontal_spacing=0.06,
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
            colour = cmap.get(cat) or palette.color(cat)
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

    for r in range(1, rows + 1):
        fig.update_yaxes(title_text=ytitle, row=r, col=1)
        fig.update_xaxes(title_text=xtitle, row=r, col=1)

    # shared_yaxes only links panels inside a row, so a multi-row grid keeps
    # one scale per row. Matching every axis to the first makes the whole grid
    # comparable. Axis 1 is the reference, so the loop starts at 2.
    if shared_y and rows > 1:
        for i in range(2, rows * cols + 1):
            fig.update_layout({f"yaxis{i}": {"matches": "y"}})

    if percent:
        fig.update_yaxes(range=[0, 100])

    # the legend sits below the panels, so its paper-fraction y has to clear
    # the x-axis title by a fixed pixel allowance
    total_height = max(height or PANEL_HEIGHT * rows, MIN_PANEL_HEIGHT * rows)
    total_width = _width(width, PANEL_WIDTH * cols)
    fig.update_layout(
        title=title, template="plotly_white", barmode="stack",
        height=total_height, width=total_width,
        autosize=total_width is None, hovermode="x unified",
        legend=dict(title=legend_title or None, orientation="h",
                    yanchor="top", y=-(78 / total_height), xanchor="left",
                    x=0, font=dict(size=11)),
        margin=dict(t=90, b=legend_bottom))
    if show:
        fig.show()
    return fig


def _num(v, span):
    """Bar label at a precision suited to the values on the axis."""
    if v is None or pd.isna(v):
        return ""
    v = float(v)
    if span >= 1000:
        return f"{v:,.0f}"
    if span >= 10:
        return f"{v:,.1f}"
    if span >= 1:
        return f"{v:,.2f}"
    return f"{v:,.3f}"


def trend(runs, extract, title, ytitle, xtitle="Year", markers=True,
          height=560, width=None, kind="line", years=None, opacity=0.45,
          log_y=False, labels=None, show=True):
    """One series per scenario on a single axis, for scalar indicators.

    kind: 'line', 'bar' (grouped, at MILESTONE_YEARS unless years says
    otherwise) or 'area'. Scenarios are never stacked - they are alternative
    futures, not components. years='all' draws every year; a single year puts
    the scenario names on the x axis. labels=None prints bar values while
    there are few enough to stay legible.
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
        labels = kind == "bar" and n_bars <= MAX_BAR_LABELS
    single_year = years is not None and len(list(years)) == 1

    fig = go.Figure()
    for scene, s in series.items():
        colour = palette.color(scene)
        x, y = list(s.index), list(s.values)
        if kind == "bar":
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
        year = list(years)[0]
        if str(year) not in title:
            title = f"{title}, {year}"

    total_width = _width(width, FIG_WIDTH)
    fig.update_layout(title=title, yaxis_title=ytitle,
                      xaxis_title="Scenario" if single_year else xtitle,
                      template="plotly_white",
                      hovermode="closest" if single_year else "x unified",
                      height=height, width=total_width,
                      autosize=total_width is None, legend_title="Scenario",
                      barmode="group", bargap=0.15, bargroupgap=0.02)
    if kind == "bar" and years is not None:
        fig.update_xaxes(type="category")
    if labels:
        fig.update_yaxes(automargin=True)
        if not log_y:
            fig.update_yaxes(range=[min(0, -0.02 * span), span * 1.15])
    if log_y:
        fig.update_yaxes(type="log")
    if show:
        fig.show()
    return fig


def save(fig, name, vis_dir="vis", html=True, png=False, scale=2,
         width=None, height=None, slide=False):
    """Write a figure next to your results. Returns the paths written.

    width/height override the figure's own size for the png without mutating
    it; slide=True is the 16:9 SLIDE_WIDTH x SLIDE_HEIGHT shorthand. Leave
    slide off for panel grids - it restretches a 2x2 into a shape it was not
    laid out for. scale=2 on the figure's own size is sharp enough for a
    slide at any placement width.
    """
    out = Path(vis_dir)
    out.mkdir(parents=True, exist_ok=True)
    if slide:
        width = width or SLIDE_WIDTH
        height = height or SLIDE_HEIGHT
    written = []
    if html:
        p = out / f"{name}.html"
        fig.write_html(p, include_plotlyjs="cdn")
        written.append(p)
    if png:                                # needs kaleido
        p = out / f"{name}.png"
        fig.write_image(p, scale=scale, width=width, height=height)
        written.append(p)
    for p in written:
        print(f"  wrote {p}")
    return written


# --------------------------------------------------------------------------- #
# extractors
# --------------------------------------------------------------------------- #

_ELIGIBLE_KEYS = ("eligible", "agv", "agv_eligible", "agv-eligible")


def _resolve_crops(available, crops):
    """Map requested crop names onto the labels present in the results.

    Accepts labels ('Potatoes'), model codes ('PTW') and partial spellings,
    case-insensitively. Returns 'eligible' for the auto-detect keywords, which
    the caller resolves against the run.
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


def _pick_crops(d, crops):
    """Filter a frame with a Crop column to the requested crops."""
    if crops is None:
        return d
    sel = _resolve_crops(set(d.Crop.unique()), crops)
    if sel == "eligible":
        sel = sorted(d.loc[d.System == "Agrivoltaic", "Crop"].unique()
                     if "System" in d.columns else d.Crop.unique())
    return d[d.Crop.isin(sel or [])]


def _sfx(crops):
    """Title suffix naming the crop selection."""
    if crops is None:
        return ""
    if isinstance(crops, str) and crops.strip().casefold() in _ELIGIBLE_KEYS:
        return " - agrivoltaic-eligible crops"
    names = [crops] if isinstance(crops, str) else list(crops)
    return " - " + ", ".join(str(c) for c in names)


def _group(d):
    return d.groupby(["YEAR", "Category"], as_index=False).VALUE.sum()


def _land_by_category(pack, sets_dir=None):
    act = _df(pack, "TotalTechnologyAnnualActivity")
    if act is None or act.empty:
        return None
    tiers = Lvis.land_tiers(sets_dir)
    d = act[act.TECHNOLOGY.isin(tiers["land_tier"])].copy()
    if d.empty:
        return None
    d["Category"] = d.TECHNOLOGY.map(lambda t: Lvis._category(t, tiers))
    return _group(d)


def _agr_land(pack, sets_dir=None):
    """Agricultural land with Crop and System columns."""
    act = _df(pack, "TotalTechnologyAnnualActivity")
    if act is None or act.empty:
        return None
    agr = Lvis._agricultural(act, Lvis.land_tiers(sets_dir))
    return None if agr.empty else agr


def _agricultural(pack, by="system", sets_dir=None, crops=None):
    agr = _agr_land(pack, sets_dir)
    if agr is None:
        return None
    agr = _pick_crops(agr, crops)
    if agr.empty:
        return None
    agr = agr.copy()
    agr["Category"] = (agr.Crop + " (" + agr.System + ")" if by == "crop"
                       else agr.System)
    return _group(agr)


def _agv_land_by_crop(pack, sets_dir=None, crops=None):
    agr = _agr_land(pack, sets_dir)
    if agr is None:
        return None
    d = _pick_crops(agr[agr.System == "Agrivoltaic"], crops)
    if d.empty:
        return None
    return _group(d.assign(Category=d.Crop))


def _agv_series(pack, sets_dir=None, crops=None):
    """Agrivoltaic land area, as a YEAR-indexed Series."""
    agr = _agricultural(pack, "system", sets_dir, crops)
    if agr is None:
        return None
    d = agr[agr.Category == "Agrivoltaic"]
    return None if d.empty else d.set_index("YEAR").VALUE


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
    g = _group(d)
    keep = g.groupby("Category").VALUE.sum()
    return g[g.Category.isin(keep[keep > Lvis._TOL].index)]


def _generation(pack, unit="GWh"):
    df = _df(pack, "ProductionByTechnologyAnnual")
    if df is None or df.empty:
        return None
    col = Evis._unit_column(unit)
    gen = Evis.generation_by_source(Evis._collapse_timeslice(df))
    if gen.empty:
        return None
    return gen.rename(columns={"Source": "Category", col: "VALUE"})[
        ["YEAR", "Category", "VALUE"]]


def _crop_output(pack, sets_dir=None):
    """Crop output by mode, with Crop and System columns: activity x OAR."""
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
    return d


def _production_by_system(pack, crop=None, sets_dir=None):
    d = _crop_output(pack, sets_dir)
    if d is None:
        return None
    if crop is not None:
        d = d[d.Crop.str.lower() == str(crop).lower()]
        if d.empty:
            return None
    return _group(d.assign(Category=d.System))


def _agv_production_by_crop(pack, sets_dir=None, crops=None):
    d = _crop_output(pack, sets_dir)
    if d is None:
        return None
    d = _pick_crops(d[d.System == "Agrivoltaic"], crops)
    if d.empty:
        return None
    return _group(d.assign(Category=d.Crop))


@lru_cache(maxsize=4)
def _elc_oar(sets_dir):
    """Electricity output per unit of agrivoltaic land, by technology and mode."""
    oar = pd.read_csv(Path(sets_dir) / "OutputActivityRatio.csv")
    oar = oar.loc[(oar.FUEL == Evis.ELEC_BUS)
                  & oar.TECHNOLOGY.str.startswith("LNDAGR"),
                  ["TECHNOLOGY", "MODE_OF_OPERATION", "YEAR", "VALUE"]]
    oar["MODE_OF_OPERATION"] = oar.MODE_OF_OPERATION.astype(int)
    return oar


def _mode_crop(sets_dir):
    """Technology and mode to crop, read off the crop side of the OAR."""
    oar = Lvis._crop_oar_cached(sets_dir)
    m = oar[["TECHNOLOGY", "MODE_OF_OPERATION", "FUEL"]].drop_duplicates()
    m["Crop"] = m.FUEL.str[3:6].map(Lvis._CROP_LABELS).fillna(m.FUEL.str[3:6])
    return m.drop(columns="FUEL")


def _agv_generation_series(pack, unit="GWh"):
    """Total agrivoltaic generation, as a YEAR-indexed Series."""
    gen = _generation(pack, unit)
    if gen is None:
        return None
    d = gen[gen.Category == "Agrivoltaic"]
    return None if d.empty else d.set_index("YEAR").VALUE


def _agv_generation_by_crop(pack, unit="GWh", sets_dir=None, crops=None):
    """Agrivoltaic generation split by crop; falls back to the pooled total."""
    def total():
        s = _agv_generation_series(pack, unit)
        return None if s is None else _group(
            s.rename("VALUE").reset_index().assign(Category="Agrivoltaic"))

    bymode = _df(pack, "TotalAnnualTechnologyActivityByMode")
    if bymode is None or bymode.empty:
        return total()
    sd = str(Path(sets_dir or Lvis.SETS_DIR).resolve())
    oar = _elc_oar(sd)
    d = bymode[bymode.TECHNOLOGY.str.startswith("LNDAGR")].copy()
    if d.empty or oar.empty:
        return total()
    d["MODE_OF_OPERATION"] = d.MODE_OF_OPERATION.astype(int)
    d = d.merge(oar, on=["TECHNOLOGY", "MODE_OF_OPERATION", "YEAR"],
                suffixes=("_act", "_oar"))
    if d.empty:
        return total()
    d["VALUE"] = d.VALUE_act * d.VALUE_oar
    if Evis._unit_column(unit) == "GWh":
        d["VALUE"] *= Evis.PJ_TO_GWH
    d = d.merge(_mode_crop(sd), on=["TECHNOLOGY", "MODE_OF_OPERATION"],
                how="left")
    d["Crop"] = d.Crop.fillna("Agrivoltaic")
    d = _pick_crops(d, crops)
    if d.empty:
        return total()
    return _group(d.assign(Category=d.Crop))


# --------------------------------------------------------------------------- #
# land use
# --------------------------------------------------------------------------- #

def compare_land_by_category(runs, sets_dir=None, **kw):
    """Provincial land by category, one panel per scenario."""
    return panels(runs, lambda p: _land_by_category(p, sets_dir),
                  "Total land in BC by category", Lvis._AREA_UNIT,
                  legend_title="Category", **kw)


def compare_agricultural_land(runs, by="system", crops=None, sets_dir=None,
                              **kw):
    """Agricultural land, conventional and agrivoltaic, one panel per scenario.

    by='system' stacks the two systems; by='crop' splits each by crop and
    colours by crop. crops restricts the land counted: None is every crop,
    'eligible' only the crops this run puts agrivoltaics on, or a list.
    """
    label = "by crop and system" if by == "crop" else "conventional and agrivoltaic"
    if by == "crop":
        kw.setdefault("colors", crop_colors)
        # a crop and system split runs to a dozen or more entries, so the
        # legend wraps over several rows and needs the extra bottom margin
        kw.setdefault("legend_bottom", 170)
        order = None
    else:
        order = ["Conventional", "Agrivoltaic"]
    return panels(runs, lambda p: _agricultural(p, by, sets_dir, crops),
                  f"Agricultural land, {label}{_sfx(crops)}", Lvis._AREA_UNIT,
                  legend_title="System", order=order, **kw)


def compare_land_for_power(runs, **kw):
    """Land occupied by electricity generation, split by source."""
    return panels(runs, _land_for_power,
                  "Land occupied by electricity generation", Lvis._AREA_UNIT,
                  legend_title="Source", **kw)


# --------------------------------------------------------------------------- #
# agrivoltaics
# --------------------------------------------------------------------------- #

def compare_agv_land(runs, crops=None, sets_dir=None, **kw):
    """Agrivoltaic land area, one bar group per year (MILESTONE_YEARS)."""
    kw.setdefault("kind", "bar")
    return trend(runs, lambda p: _agv_series(p, sets_dir, crops),
                 "Agrivoltaic land area", Lvis._AREA_UNIT, **kw)


def compare_agv_land_by_crop(runs, crops=None, sets_dir=None,
                             years=MILESTONE_YEARS, **kw):
    """Agrivoltaic land alone, split by crop, one panel per scenario.

    years=None draws every year of the horizon.
    """
    kw.setdefault("colors", crop_colors)
    kw.setdefault("kind", "bar")

    def extract(pack):
        d = _agv_land_by_crop(pack, sets_dir, crops)
        if d is None or years is None:
            return d
        return d[d.YEAR.isin(list(years))]

    return panels(runs, extract,
                  f"Agrivoltaic land by crop{_sfx(crops)}", Lvis._AREA_UNIT,
                  legend_title="Crop", **kw)


def compare_agv_generation(runs, unit="GWh", years=MILESTONE_YEARS,
                           crops=None, sets_dir=None, **kw):
    """Agrivoltaic electricity generation by crop, one panel per scenario.

    years=None draws every year of the horizon.
    """
    col = Evis._unit_column(unit)
    kw.setdefault("colors", crop_colors)
    kw.setdefault("kind", "bar")

    def extract(pack):
        d = _agv_generation_by_crop(pack, unit, sets_dir, crops)
        if d is None or years is None:
            return d
        return d[d.YEAR.isin(list(years))]

    return panels(runs, extract, "Agrivoltaic electricity generation by crop",
                  f"Generation ({col})", legend_title="Crop", **kw)


def compare_agv_production(runs, crop=None, sets_dir=None, **kw):
    """Crop output on conventional versus agrivoltaic systems."""
    sfx = f", {crop}" if crop else ""
    return panels(runs, lambda p: _production_by_system(p, crop, sets_dir),
                  f"Crop production by system{sfx}", "Million tonnes",
                  legend_title="System",
                  order=["Conventional", "Agrivoltaic"], **kw)


def compare_agv_production_by_crop(runs, crops=None, sets_dir=None, **kw):
    """Tonnes produced under agrivoltaics, split by crop."""
    kw.setdefault("colors", crop_colors)
    return panels(runs, lambda p: _agv_production_by_crop(p, sets_dir, crops),
                  f"Agrivoltaic crop production{_sfx(crops)}",
                  "Million tonnes", legend_title="Crop", **kw)


# --------------------------------------------------------------------------- #
# energy
# --------------------------------------------------------------------------- #

def compare_generation(runs, unit="GWh", **kw):
    """Annual electricity generation by source, one panel per scenario."""
    col = Evis._unit_column(unit)
    return panels(runs, lambda p: _generation(p, unit),
                  "Annual electricity generation by source",
                  f"Generation ({col})", legend_title="Source",
                  order=Evis._order, **kw)