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

TAB_ORDER = ["Climate", "Land", "Energy", "Water"]
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


def _render_tabs(nexus_plots: dict) -> tuple[str, str, list]:
    """-> (buttons_html, tabs_html, kept_genre_names)"""
    import plotly.io as pio

    genres = [g for g in TAB_ORDER if nexus_plots.get(g)] + \
             [g for g in nexus_plots if g not in TAB_ORDER and nexus_plots.get(g)]
    buttons, sections, kept = "", "", []
    for genre in genres:
        figs = {n: f for n, f in nexus_plots[genre].items()
                if f is not None and hasattr(f, "to_html")}
        if not figs:
            continue
        kept.append(genre)
        cards = "".join(
            f"<div class='card'><h3>{name.replace('_', ' ').strip('(').title()}</h3>"
            + pio.to_html(fig, include_plotlyjs=False, full_html=False,
                          default_height=460)
            + "</div>"
            for name, fig in figs.items())
        buttons += (f"<button class='tb' id='b{genre}' onclick=\"show('{genre}')\">"
                    f"{genre}<span class='n'>{len(figs)}</span></button>")
        sections += (f"<div class='sec' id='{genre}' style='display:none'>"
                     f"<div class='grid'>{cards}</div></div>")
    return buttons, sections, kept


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
    tokens = {
        "scenario": scenario,
        "info_html": f"<p class='info'>{scenario_info}</p>" if scenario_info else "",
        "meta_html": f"<p class='meta'>{run_meta}</p>" if run_meta else "",
        "extra_html": (f"<p class='extra'><span class='badge'>i</span>"
                       f"<span>{extra_info}</span></p>") if extra_info else "",
        "plotly_script": plotly_script,
        "buttons_html": buttons_html,
        "tabs_html": tabs_html,
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

    tokens["kept0"] = kept[0] if kept else ""   # first tab shown on load
    for key, val in tokens.items():
        tpl = tpl.replace("{{" + key + "}}", val)

    save_to = Path(save_to)
    save_to.parent.mkdir(parents=True, exist_ok=True)
    save_to.write_text(tpl, encoding="utf-8")
    return save_to
