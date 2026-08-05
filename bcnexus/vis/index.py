"""
Master index for CLEW reports — one HTML that browses every run in a folder.

Author: Md Eliasinul Islam

`get_plots()` writes one report per run, named by convention:

    CLEW_report_<algo>_<scenario>_<N>ts_<solver>_<YYYY_MM_DD>.html
    CLEW_model_map_<scenario>_<YYYY_MM_DD>.html

This module parses those names into a manifest and writes a single
`CLEW_index.html` with cascading dropdowns (scenario / timeslices / storage
algorithm / solver / date) that loads the matching report in an iframe. The
manifest is baked in because a page opened from file:// cannot list a
directory — re-run after new runs.

    from bcnexus.vis import index
    index.build_index('vis')          # -> report/BCNexus_report_v1.html

Or from the shell:

    python -m bcnexus.vis.index vis [output.html]

The index may live outside the report folder (it does by default); links are
rewritten relative to wherever it is written, so the pair stays portable as
long as `report/` and `vis/` keep their relative position.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from bcnexus.vis import report as _report

_HERE = Path(__file__).parent
TEMPLATE_PATH = _HERE / "templates" / "index_template.html"

DEFAULT_OUT = Path("report") / "BCNexus_report_v1.html"

# CLEW_report_<algo>_<scenario...>_<N>ts_<solver>_<YYYY_MM_DD>.html
_REPORT_RE = re.compile(
    r"^CLEW_report_(?P<algo>[^_]+)_(?P<scenario>.+?)_(?P<ts>\d+)ts_"
    r"(?P<solver>[^_]+)(?:_(?P<date>\d{4}_\d{2}_\d{2}))?\.html$")
# CLEW_model_map_<scenario...>_<YYYY_MM_DD>.html
_MAP_RE = re.compile(
    r"^CLEW_model_map_(?P<scenario>.+?)"
    r"(?:_(?P<date>\d{4}_\d{2}_\d{2}))?\.html$")


def _human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def scan_reports(vis_dir: str | Path, recursive: bool = False) -> list[dict]:
    """Parse report/map filenames in `vis_dir` into manifest records.

    Args:
        vis_dir: folder holding the CLEW_*.html files.
        recursive: also scan sub-folders (paths stay relative to vis_dir, so
            the index still works when opened from file://).

    Returns:
        List of dicts: scenario, ts, algo, solver, date, report, map, size.
        `map` is the matching model-map file (same scenario, nearest date) or
        None. Files that do not follow the naming convention are ignored.
    """
    root = Path(vis_dir)
    it = root.rglob("CLEW_*.html") if recursive else root.glob("CLEW_*.html")

    maps: dict[tuple[str, str], str] = {}
    reports: list[dict] = []
    for f in sorted(it):
        rel = f.relative_to(root).as_posix()
        m = _REPORT_RE.match(f.name)
        if m:
            d = m.groupdict()
            reports.append({
                "scenario": d["scenario"], "ts": int(d["ts"]),
                "algo": d["algo"], "solver": d["solver"],
                "date": d["date"] or "undated", "report": rel, "map": None,
                "size": _human(f.stat().st_size),
            })
            continue
        m = _MAP_RE.match(f.name)
        if m:
            d = m.groupdict()
            maps[(d["scenario"], d["date"] or "undated")] = rel

    # attach a model map: exact (scenario, date) first, then any date
    for r in reports:
        key = (r["scenario"], r["date"])
        if key in maps:
            r["map"] = maps[key]
        else:
            same = [v for (s, _), v in maps.items() if s == r["scenario"]]
            r["map"] = sorted(same)[-1] if same else None

    reports.sort(key=lambda r: (r["scenario"], -r["ts"], r["date"]))
    return reports


def build_index(vis_dir: str | Path = "vis",
                save_to: str | Path = None,
                title: str = "BCNexus · CLEW run index",
                recursive: bool = False,
                template: str | Path = None) -> Path:
    """Write the master index.

    Args:
        vis_dir: folder scanned for CLEW_*.html.
        save_to: output path; defaults to `report/BCNexus_report_v1.html`.
            The parent folder is created if absent. Report links are rewritten
            relative to this location, so the index need not sit beside the
            reports — but moving one without the other breaks the links.
        title: header text.
        recursive: include sub-folders (e.g. dated run directories).
        template: custom skin; defaults to templates/index_template.html.

    Returns:
        Path to the written file.
    """
    root = Path(vis_dir)
    runs = scan_reports(root, recursive=recursive)
    out = Path(save_to) if save_to else DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)

    # links are relative to the index, not to vis_dir
    base = out.resolve().parent
    for r in runs:
        for key in ("report", "map"):
            if r[key]:
                r[key] = Path(os.path.relpath((root / r[key]).resolve(),
                                              base)).as_posix()

    logo = _report.logo_data_uri()
    logo_html = (f"<a class='logo' href='{_report.DELTAE_URL}' target='_blank' "
                 f"rel='noopener' title='Delta E+ Research Group'>"
                 f"<img src='{logo}' alt='Delta E+'></a>" if logo else "")
    brand = _report.brand_logo_data_uri()
    brand_html = (f"<img class='brand' src='{brand}' alt='BCNexus'>"
                  if brand else "<span class='word'>BCNexus</span>")

    html = Path(template or TEMPLATE_PATH).read_text(encoding="utf-8")
    for tok, val in {
        "{{title}}": title,
        "{{manifest}}": json.dumps(runs),
        "{{logo_html}}": logo_html,
        "{{brand_html}}": brand_html,
        "{{brand_src}}": brand,
        "{{gh_icon}}": _report._GH_SVG,
        "{{gh}}": _report.GITHUB_URL,
        "{{site}}": _report.SITE_URL,
        "{{deltae}}": _report.DELTAE_URL,
        "{{generated}}": time.strftime("%Y-%m-%d %H:%M"),
        "{{n_runs}}": str(len(runs)),
    }.items():
        html = html.replace(tok, val)

    out.write_text(html, encoding="utf-8")
    print(f"[index] {len(runs)} run(s) indexed -> {out}")
    return out


if __name__ == "__main__":
    import sys
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    build_index(args[0] if args else "vis",
                save_to=args[1] if len(args) > 1 else None,
                recursive="--recursive" in sys.argv)
