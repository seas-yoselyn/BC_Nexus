"""
CLEW report builder — assembles the combined tabbed HTML report.

Author: Md Eliasinul Islam

Separation of concerns:
    templates/report_template.html  -> ALL markup, CSS and JS (edit there)
    this module                     -> data/figure -> token substitution

Tokens the template expects (see its header comment):
    {{scenario}} {{info_html}} {{meta_html}} {{extra_html}}
    {{plotly_script}} {{buttons_html}} {{tabs_html}} {{kept0}}
    {{gh}} {{site}} {{logo_html}} {{cols}} {{layout}}
    {{runlog_btn}} {{runlog_html}}            (runtime_memory_log.txt)
    {{gurobi_btn}} {{gurobi_html}}            (solver log)
    {{constraints_btn}} {{constraints_html}}  (constraints_summary.txt)

Use a custom skin by passing `template=` a path to your own copy — nothing
in Python needs to change.
"""
from __future__ import annotations

import base64
from pathlib import Path

GITHUB_URL = "https://github.com/DeltaE/BC_Nexus"
SITE_URL = "https://deltae.github.io/BC_Nexus/"
SITE_TITLE = "BCNexus · CLEWs Climate–Land–Energy–Water Model"
DELTAE_URL = "https://www.sfu.ca/see/research/delta-e.html"

_HERE = Path(__file__).parent
TEMPLATE_PATH = _HERE / "templates" / "report_template.html"
LOGO_PATH = _HERE / "assets" / "deltae_logo.png"
BRAND_LOGO_PATH = _HERE / "assets" / "BCNexus logo.png"

TAB_ORDER = ["Inputs", "Climate", "Land", "Energy", "Water"]

# Shown at the top of the Inputs tab (and the Energy sub-tab), where the
# distinction between a prescribed input and an optimisation result matters.
READ_NOTE = (
    "<div class='readnote'><b>Reading these plots.</b> End-use fuel demand is "
    "exogenous: the demand technologies are unit-efficiency pass-throughs, so "
    "the fuel mix shown in the projection is an input assumption, not an "
    "optimisation outcome. Consult <code>data/calibration/README.md</code> "
    "before reporting an end-use fuel level as a model finding.</div>")

# result genres folded under the "Outputs" super-tab
OUTPUT_GENRES = ["Climate", "Land", "Energy", "Water"]
_COLS = {"1": "1fr", "2": "1fr 1fr", "3": "1fr 1fr 1fr"}

_GH_SVG = (
    "<svg viewBox='0 0 16 16' width='16' height='16' fill='currentColor'>"
    "<path d='M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17"
    ".55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-"
    ".94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1"
    ".87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87"
    ".31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1"
    ".32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92."
    "08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73"
    ".54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16"
    " 8c0-4.42-3.58-8-8-8z'/></svg>")
_INFO_SVG = (
    "<svg viewBox='0 0 16 16' width='14' height='14' fill='none' "
    "stroke='currentColor' stroke-width='1.6' stroke-linecap='round'>"
    "<circle cx='8' cy='8' r='6.6'/><path d='M8 7.2v4M8 4.9v.1'/></svg>")


def logo_data_uri(logo_path: str | Path = None) -> str:
    """Base64 data-URI for the Delta E+ logo (keeps the report offline-safe)."""
    p = Path(logo_path) if logo_path else LOGO_PATH
    try:
        return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
    except Exception:
        return ""


def brand_logo_data_uri(logo_path: str | Path = None) -> str:
    """Base64 data-URI for the BCNexus brand mark.

    Both marks in assets/ are white-on-transparent, so they are placed on the
    dark header as-is; on light backgrounds the templates apply a CSS
    `filter:invert(1)` (class `.wm`) rather than shipping a second file.
    """
    return logo_data_uri(logo_path or BRAND_LOGO_PATH)



# ---------------------------------------------------------------- run log
_RUNLOG_ORDER = ["Scenario", "Timeslices", "Clustering Attributes", "Runtime",
                 "Run Start Time", "Run End Time", "Memory Usage",
                 "Linux User", "User", "CPU Cores/Threads Used", "Machine ID"]


def parse_runlog(runlog: str | Path | dict) -> dict:
    """Parse a runtime_memory_log.txt into {field: value}.

    The log is appended to on every run, so the LAST block (most recent run)
    is returned. A dict may be passed through unchanged.
    """
    if isinstance(runlog, dict):
        return dict(runlog)
    try:
        text = Path(runlog).read_text(encoding="utf-8")
    except Exception:
        return {}
    blocks, cur = [], {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if key == "Scenario" and cur:          # new block starts
            blocks.append(cur)
            cur = {}
        if key:
            cur[key] = val
    if cur:
        blocks.append(cur)
    return blocks[-1] if blocks else {}


def _runlog_html(info: dict) -> str:
    """Definition-list markup for the run-info panel."""
    if not info:
        return ""
    ordered = [k for k in _RUNLOG_ORDER if k in info]
    ordered += [k for k in info if k not in ordered]
    rows = "".join(
        f"<div class='rl-row'><span class='rl-k'>{k}</span>"
        f"<span class='rl-v'>{info[k]}</span></div>" for k in ordered)
    return (f"<div class='runlog' id='runlog'>"
            f"<div class='rl-title'>Run diagnostics</div>{rows}"
            f"<div class='rl-note'>Source: runtime_memory_log.txt "
            f"(most recent entry).</div></div>")



# ---------------------------------------------------------------- solver log
def parse_constraints(summary: str | Path | dict) -> dict:
    """Parse constraints_summary.txt -> {'binding': [...], 'non_binding': [...]}.

    Written by RunModel.get_summary_report(): a 'Binding Constraints:' block,
    a dotted separator, then 'Non-Binding Constraints:'. A dict with the same
    keys passes through unchanged.
    """
    if isinstance(summary, dict):
        return {"binding": list(summary.get("binding", [])),
                "non_binding": list(summary.get("non_binding", []))}
    try:
        text = Path(summary).read_text(encoding="utf-8")
    except Exception:
        return {}
    binding, non_binding, bucket = [], [], None
    for line in text.splitlines():
        st = line.strip()
        if not st or set(st) <= set("=."):        # separators
            continue
        low = st.lower()
        if low.startswith("binding constraints"):
            bucket = binding
            continue
        if low.startswith("non-binding constraints"):
            bucket = non_binding
            continue
        if low.startswith("constraints"):          # header line
            continue
        if bucket is not None:
            bucket.append(st)
    return {"binding": binding, "non_binding": non_binding}



def parse_gurobi_log(log: str | Path) -> dict:
    """Extract headline stats from a gurobi.log (last solve in the file).

    Pulls model size, presolve reduction, objective, MIP gap, iterations,
    barrier/simplex method, solve time and status. Missing fields are simply
    absent from the returned dict.
    """
    import re
    try:
        text = Path(log).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {}
    # keep only the final solve if the log holds several
    marks = [m.start() for m in re.finditer(r"Gurobi Optimizer version", text)]
    if marks:
        text = text[marks[-1]:]

    out = {}
    m = re.search(r"Gurobi Optimizer version ([\w.]+)", text)
    if m:
        out["Gurobi version"] = m.group(1)
    m = re.search(r"Optimize a model with (\d+) rows?, (\d+) columns?"
                  r"(?: and ([\d,]+) nonzeros)?", text)
    if m:
        out["Model size"] = f"{int(m.group(1)):,} rows x {int(m.group(2)):,} cols"
        if m.group(3):
            out["Nonzeros"] = f"{int(m.group(3).replace(',', '')):,}"
    m = re.search(r"Presolved: (\d+) rows?, (\d+) columns?", text)
    if m:
        out["After presolve"] = f"{int(m.group(1)):,} rows x {int(m.group(2)):,} cols"
    m = re.findall(r"(Barrier|Simplex|Concurrent|Dual simplex|Primal simplex)"
                   r"[^\n]*?(?:solved|log|method)", text, re.I)
    if m:
        out["Method"] = m[-1] if isinstance(m[-1], str) else m[-1][0]
    m = re.search(r"Optimal objective\s+([-\d.eE+]+)", text)
    if m:
        out["Objective"] = m.group(1)
    else:
        m = re.search(r"Best objective ([-\d.eE+]+)", text)
        if m:
            out["Objective"] = m.group(1)
    m = re.search(r"gap ([\d.]+%)", text)
    if m:
        out["MIP gap"] = m.group(1)
    m = re.search(r"Solved in (\d+) iterations and ([\d.]+) seconds", text)
    if m:
        out["Iterations"] = f"{int(m.group(1)):,}"
        out["Solve time"] = f"{m.group(2)} s"
    else:
        m = re.search(r"Explored \d+ nodes \(([\d,]+) simplex iterations\)"
                      r" in ([\d.]+) seconds", text)
        if m:
            out["Iterations"] = m.group(1)
            out["Solve time"] = f"{m.group(2)} s"
    m = re.search(r"(Model is infeasible|Model is unbounded|"
                  r"Optimal solution found|Time limit reached|"
                  r"Solution count \d+)", text)
    if m:
        out["Status"] = ("optimal" if "Optimal" in m.group(1)
                         else m.group(1).lower())
    m = re.search(r"Thread count[^\n]*?using (\d+) threads", text)
    if m:
        out["Solver threads"] = m.group(1)
    return out


def _rows(d: dict) -> str:
    return "".join(f"<div class='rl-row'><span class='rl-k'>{k}</span>"
                   f"<span class='rl-v'>{v}</span></div>" for k, v in d.items())


def _gurobi_html(stats: dict, solver_meta: dict = None) -> str:
    """Panel markup for solver/optimizer statistics (gurobi.log)."""
    merged = {**(solver_meta or {}), **(stats or {})}
    if not merged:
        return ""
    return (f"<div class='runlog' id='gurobilog'>"
            f"<div class='rl-title'>Solver log</div>{_rows(merged)}"
            f"<div class='rl-note'>Source: solver log (last solve).</div></div>")


def _constraints_html(cons: dict) -> str:
    """Panel markup for the binding / non-binding constraint lists."""
    cons = cons or {}
    b, nb = cons.get("binding", []), cons.get("non_binding", [])
    if not (b or nb):
        return ""
    def _list(items, cls):
        if not items:
            return "<div class='cn-empty'>none</div>"
        return "".join(f"<span class='cn {cls}'>{i}</span>" for i in items)
    counts = _rows({"Binding": len(b), "Non-binding": len(nb)})
    return (f"<div class='runlog' id='constraintslog'>"
            f"<div class='rl-title'>Constraints summary</div>{counts}"
            f"<div class='cn-h'>Binding <span>(active at the optimum — these "
            f"drive the solution)</span></div>"
            f"<div class='cn-wrap'>{_list(b, 'cn-b')}</div>"
            f"<div class='cn-h'>Non-binding</div>"
            f"<div class='cn-wrap'>{_list(nb, 'cn-nb')}</div>"
            f"<div class='rl-note'>Source: constraints_summary.txt.</div></div>")



# ---------------------------------------------------------------- constants

def _constants_html(meta: dict, sets: dict = None) -> str:
    """Panel markup for the model-configuration button (same style as the
    run/solver diagnostics panels)."""
    if not meta and not sets:
        return ""
    rows = "".join(f"<div class='rl-row'><span class='rl-k'>{k}</span>"
                   f"<span class='rl-v'>{v}</span></div>" for k, v in (meta or {}).items())
    set_rows = "".join(f"<div class='rl-row'><span class='rl-k'>{k}</span>"
                       f"<span class='rl-v'>{v}</span></div>"
                       for k, v in (sets or {}).items())
    return (f"<div class='runlog' id='constantslog'>"
            f"<div class='rl-title'>Model configuration</div>{rows}"
            + (f"<div class='cn-h'>Sets</div>{set_rows}" if set_rows else "")
            + f"<div class='rl-note'>Constants for this run.</div></div>")


def build_constants_figure(meta: dict, sets: dict = None, structure: dict = None):
    """Compact 'model configuration' visual: a labelled table of the run's
    constants (region, horizon, storage algorithm, timeslices, solver, ...)
    plus set sizes. Rendered as a plotly table so it lives in the same tab
    machinery as the plots.
    """
    import plotly.graph_objects as go
    rows = list(meta.items())
    if sets:
        rows += [("", "")] + [(f"Set: {k}", v) for k, v in sets.items()]
    if structure:
        rows += [("", "")] + list(structure.items())
    if not rows:
        return None
    fig = go.Figure(go.Table(
        columnwidth=[46, 54],
        header=dict(values=["<b>Configuration</b>", "<b>Value</b>"],
                    fill_color="#123c46", font=dict(color="white", size=13),
                    align="left", height=30),
        cells=dict(values=[[r[0] for r in rows], [str(r[1]) for r in rows]],
                   fill_color=[["#f6f7f9" if i % 2 else "white"
                                for i in range(len(rows))]],
                   align="left", height=25, font=dict(size=12))))
    fig.update_layout(margin=dict(t=8, b=8, l=4, r=4),
                      height=min(90 + 25 * len(rows), 760))
    return fig


def _render_tabs(nexus_plots: dict) -> tuple[str, str, list]:
    """-> (buttons_html, tabs_html, kept_tab_names)

    Top-level tabs are Constants, Inputs and Outputs. The C/L/E/W genres are
    nested inside Outputs as labelled sections, so the reader moves
    configuration -> assumptions -> results rather than straight to results.
    """
    import plotly.io as pio

    def _cards(figs: dict) -> str:
        return "".join(
            f"<div class='card'><h3>{name.replace('_', ' ').strip('(').title()}</h3>"
            + pio.to_html(fig, include_plotlyjs=False, full_html=False,
                          default_height=460)
            + "</div>"
            for name, fig in figs.items())

    def _keep(genre) -> dict:
        return {n: f for n, f in (nexus_plots.get(genre) or {}).items()
                if f is not None and hasattr(f, "to_html")}

    buttons, sections, kept = "", "", []

    # --- Constants and Inputs: plain tabs
    for tab in ("Inputs",):
        figs = _keep(tab)
        if not figs:
            continue
        kept.append(tab)
        buttons += (f"<button class='tb' id='b{tab}' onclick=\"show('{tab}')\">"
                    f"{tab}<span class='n'>{len(figs)}</span></button>")
        sections += (f"<div class='sec' id='{tab}' style='display:none'>"
                     f"{READ_NOTE}"
                     f"<div class='grid'>{_cards(figs)}</div></div>")

    # --- Outputs: C/L/E/W as sticky SUB-TABS inside one tab
    sub_buttons, sub_panes, out_n, first_sub = "", "", 0, None
    for genre in OUTPUT_GENRES:
        figs = _keep(genre)
        if not figs:
            continue
        out_n += len(figs)
        first_sub = first_sub or genre
        sub_buttons += (f"<button class='stb' id='s{genre}' "
                        f"onclick=\"showSub('{genre}')\">{genre}"
                        f"<span class='n'>{len(figs)}</span></button>")
        _note = READ_NOTE if genre == "Energy" else ""
        sub_panes += (f"<div class='subsec' id='sub{genre}' style='display:none'>"
                      f"{_note}<div class='grid'>{_cards(figs)}</div></div>")
    if sub_panes:
        kept.append("Outputs")
        buttons += ("<button class='tb' id='bOutputs' onclick=\"show('Outputs')\">"
                    f"Outputs<span class='n'>{out_n}</span></button>")
        sections += (f"<div class='sec' id='Outputs' style='display:none'>"
                     f"<div class='subtabs'>{sub_buttons}</div>"
                     f"{sub_panes}</div>")

    # --- anything else the caller added (e.g. a timeslice genre)
    for genre in nexus_plots:
        if genre in ("Constants", "Inputs") or genre in OUTPUT_GENRES:
            continue
        if genre == "Constants":
            continue
        figs = _keep(genre)
        if not figs:
            continue
        kept.append(genre)
        buttons += (f"<button class='tb' id='b{genre}' onclick=\"show('{genre}')\">"
                    f"{genre}<span class='n'>{len(figs)}</span></button>")
        sections += (f"<div class='sec' id='{genre}' style='display:none'>"
                     f"<div class='grid'>{_cards(figs)}</div></div>")

    return buttons, sections, kept



def save_model_map(fig, save_to: str | Path, scenario: str = None,
                   plotly_js: str = "inline",
                   subtitle: str = "Reference energy system — fuel to technology "
                                   "to fuel, from InputActivityRatio / "
                                   "OutputActivityRatio (structure, not flows)"):
    """Write the reference-energy-system figure as its OWN html page.

    Kept out of the tabbed report on purpose: the map needs the full viewport
    to be readable. Returns the path written, or None when fig is None.
    """
    if fig is None:
        return None
    import plotly.io as pio
    from plotly.offline import get_plotlyjs

    js = (f"<script>{get_plotlyjs()}</script>" if plotly_js == "inline"
          else '<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>')
    body = pio.to_html(fig, include_plotlyjs=False, full_html=False,
                       default_height=920)
    _brand = brand_logo_data_uri()
    brand_html = (f"<img class='brand' src='{_brand}' alt='BCNexus'>"
                  if _brand else "")
    title = f"BCNexus Model Map{f' · {scenario}' if scenario else ''}"
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>{js}
<style>
:root{{--bg:#f6f7f9;--fg:#1a202c;--card:#fff;--border:#e2e8f0;--muted:#64748b;
--head:#123c46;--accent:#0284c7;--font:Cambria,Georgia,serif}}
html.dark{{--bg:#0f1621;--fg:#e2e8f0;--card:#1a2332;--border:#2d3a4f;
--muted:#8b9bb3;--head:#0a0f16;--accent:#38bdf8}}
*{{box-sizing:border-box}}
body{{font-family:var(--font);margin:0;background:var(--bg);color:var(--fg)}}
header{{background:var(--head);color:#fff;padding:16px 26px;display:flex;
align-items:flex-start;justify-content:space-between;gap:18px}}
h1{{margin:0;font-size:15px;font-weight:500;text-transform:uppercase;
letter-spacing:.5px;opacity:.75}}
h1 .scen{{display:block;margin-top:5px;font-size:26px;font-weight:700;
text-transform:none;letter-spacing:0;opacity:1;
border-left:4px solid var(--accent);padding-left:11px}}
.sub{{margin:10px 0 0;font-size:13.5px;opacity:.9;max-width:900px;line-height:1.5}}
.btn{{background:none;border:1px solid rgba(255,255,255,.3);color:#fff;
border-radius:8px;width:34px;height:34px;cursor:pointer;font-size:15px}}
.btn:hover{{background:rgba(255,255,255,.14)}}
.wrap{{padding:18px 22px}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:12px;
padding:8px 14px 14px}}
.brandrow{{display:flex;align-items:center;gap:14px}}
img.brand{{height:52px;width:auto;display:block;flex:none}}
</style></head><body>
<header>
  <div><div class="brandrow">{brand_html}<h1>CLEWs<span class="scen">Model Map</span></h1></div>
       <p class="sub">{subtitle}</p></div>
  <div>
    <button class="btn" onclick="document.documentElement.classList.toggle('dark');
      document.querySelectorAll('.js-plotly-plot').forEach(function(p){{
        var d=document.documentElement.classList.contains('dark');
        Plotly.relayout(p, d?{{paper_bgcolor:'#1a2332',plot_bgcolor:'#1a2332','font.color':'#e2e8f0'}}
                           :{{paper_bgcolor:'#ffffff',plot_bgcolor:'#ffffff','font.color':'#2a3f5f'}});}});"
      title="Toggle dark mode">&#9680;</button>
    <button class="btn" onclick="if(!document.fullscreenElement)
      {{document.documentElement.requestFullscreen();}}else{{document.exitFullscreen();}}"
      title="Fullscreen">&#9906;</button>
  </div>
</header>
<div class="wrap"><div class="card">{body}</div></div>
</body></html>"""
    save_to = Path(save_to)
    save_to.parent.mkdir(parents=True, exist_ok=True)
    save_to.write_text(html, encoding="utf-8")
    return save_to


def build_report(nexus_plots: dict,
                 scenario: str,
                 save_to: str | Path,
                 scenario_info: str = "",
                 run_meta: str = "",
                 extra_info: str = "",
                 plotly_js: str = "inline",
                 layout: str = "2",
                 github_url: str = GITHUB_URL,
                 site_url: str = SITE_URL,
                 deltae_url: str = DELTAE_URL,
                 logo_path: str | Path = None,
                 runlog: str | Path | dict = None,
                 constants: dict = None,
                 sets: dict = None,
                 constraints: str | Path | dict = None,
                 solver_meta: dict = None,
                 gurobi_log: str | Path = None,
                 template: str | Path = None) -> Path:
    """Render the combined CLEW report to `save_to` and return the path.

    Args:
        nexus_plots: {genre: {plot_name: plotly_fig_or_None}}.
        scenario_info: brief scenario description (header).
        run_meta: run signature, e.g. "Kotzur · 32 timeslices · gurobi".
        extra_info: OPTIONAL one-line note; rendered as a highlighted layer
            with a glowing badge. Omitted entirely when empty.
        plotly_js: "inline" (default, ~3.5 MB, works OFFLINE) or "cdn".
        layout: initial grid columns "1" | "2" | "3" (switchable in-report).
        runlog: OPTIONAL path to runtime_memory_log.txt (or a dict). When
            given, a "Run info" button appears in the toolbar showing runtime,
            memory, start/end times, user and threads. Omitted entirely when
            None — no button, no panel.
        constraints: OPTIONAL path to constraints_summary.txt (or a dict with
            'binding'/'non_binding' lists). Adds its own button beside the
            tabs. Omitted entirely when None.
        solver_meta: OPTIONAL {label: value} rows shown above the constraint
            lists (e.g. {'Solver': 'gurobi', 'Status': 'optimal'}).
        gurobi_log: OPTIONAL path to the solver log; headline stats (model
            size, objective, iterations, solve time, status) get their own
            button/panel. Omitted entirely when None.
        template: path to an alternative report template.
    """
    from plotly.offline import get_plotlyjs

    tpl_path = Path(template) if template else TEMPLATE_PATH
    tpl = tpl_path.read_text(encoding="utf-8")

    buttons_html, tabs_html, kept = _render_tabs(nexus_plots)

    plotly_script = (f"<script>{get_plotlyjs()}</script>" if plotly_js == "inline"
                     else '<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>')

    logo = logo_data_uri(logo_path)
    brand = brand_logo_data_uri()
    tokens = {
        "brand_html": (f"<img class='brand' src='{brand}' alt='BCNexus'>"
                       if brand else ""),
        "scenario": scenario,
        "info_html": f"<p class='info'>{scenario_info}</p>" if scenario_info else "",
        "meta_html": f"<p class='meta'>{run_meta}</p>" if run_meta else "",
        "extra_html": (f"<p class='extra'><span class='badge'>i</span>"
                       f"<span>{extra_info}</span></p>") if extra_info else "",
        "plotly_script": plotly_script,
        "buttons_html": buttons_html,
        "tabs_html": tabs_html,
        # GitHub / About / Delta E+ now live on the master index page, so the
        # per-run report stays uncluttered. Tokens kept for custom templates.
        "gh": (f"<a class='ic' href='{github_url}' target='_blank' "
               f"title='Source code on GitHub'>{_GH_SVG}</a>") if github_url else "",
        "site": (f"<a class='about' href='{site_url}' target='_blank' "
                 f"title='{SITE_TITLE}'>{_INFO_SVG}<span>About the model</span></a>")
                if site_url else "",
        "logo_html": (f"<a class='logo' href='{deltae_url}' target='_blank' "
                      f"title='Delta E+ Research Group'>"
                      f"<img src='{logo}' alt='Delta E+'></a>")
                     if logo and deltae_url else "",
        "cols": _COLS.get(str(layout), "1fr 1fr"),
        "layout": str(layout),
    }

    # optional run diagnostics (button + panel only when runlog is provided)
    _info = parse_runlog(runlog) if runlog is not None else {}
    tokens["runlog_html"] = _runlog_html(_info)
    tokens["runlog_btn"] = ("<button class='tb-ic' id='runlogBtn' "
                            "onclick=\"togglePanel('runlog','runlogBtn')\" "
                            "title='Run diagnostics (runtime, memory, threads)'>"
                            "&#9201;</button>" if _info else "")

    # --- optional diagnostics: each button/panel appears only if its
    #     source was provided (runlog / gurobi_log / constraints)
    _cons = parse_constraints(constraints) if constraints is not None else {}
    _gstats = parse_gurobi_log(gurobi_log) if gurobi_log is not None else {}

    tokens["gurobi_html"] = _gurobi_html(_gstats, solver_meta if _gstats else None)
    tokens["gurobi_btn"] = ("<button class='tb-ic' id='gurobiBtn' "
                            "onclick=\"togglePanel('gurobilog','gurobiBtn')\" "
                            "title='Solver log (objective, iterations, time)'>"
                            "&#9881;</button>" if tokens["gurobi_html"] else "")

    tokens["constraints_html"] = _constraints_html(_cons)
    tokens["constraints_btn"] = ("<button class='tb-ic' id='constraintsBtn' "
                                 "onclick=\"togglePanel('constraintslog',"
                                 "'constraintsBtn')\" "
                                 "title='Constraints summary (binding / non-binding)'>"
                                 "&#8942;&#8942;</button>"
                                 if tokens["constraints_html"] else "")

    # optional model-configuration panel (button sits after the diagnostics)
    tokens["constants_html"] = _constants_html(constants or {}, sets or {})
    tokens["constants_btn"] = ("<button class='tb-ic' id='constantsBtn' "
                               "onclick=\"togglePanel('constantslog','constantsBtn')\" "
                               "title='Model configuration (sets, horizon, solver)'>"
                               "&#9881;&#65038;</button>"
                               if tokens["constants_html"] else "")
    tokens["kept0"] = kept[0] if kept else ""   # first tab shown on load
    tokens["sub0"] = next((g for g in OUTPUT_GENRES
                           if (nexus_plots.get(g) or {})), "")
    for key, val in tokens.items():
        tpl = tpl.replace("{{" + key + "}}", val)

    save_to = Path(save_to)
    save_to.parent.mkdir(parents=True, exist_ok=True)
    save_to.write_text(tpl, encoding="utf-8")
    return save_to
