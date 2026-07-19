"""Notebook-friendly coefficient scanner for LP/MPS models (gurobipy).

Import into Jupyter and work with the returned DataFrames directly:

    from coef_scan import scan
    r = scan("model.lp")            # or scan(model) for an in-memory gp.Model
    r["summary"]                    # global ranges, one row per component
    r["matrix"].query("abs_coef < 1e-6").groupby(["row_family","col_family"]).size()
    r["row_spread"].head(20)        # worst-conditioned rows first

Author: EL
"""

import re
from collections import defaultdict

import numpy as np
import pandas as pd
import gurobipy as gp

_FAMILY_RE = re.compile(r"^([A-Za-z0-9_]+?)(?:[\(\[#].*)?$")


def family(name: str) -> str:
    """Collapse a constraint/variable name to its family prefix.

    Strips parenthesised indices, then trailing underscore-joined tokens that
    are digits or short all-caps codes (otoole-style flattened indices).
    """
    m = _FAMILY_RE.match(name)
    base = m.group(1) if m else name
    parts = base.split("_")
    while len(parts) > 1 and (
        parts[-1].isdigit() or re.fullmatch(r"[A-Z0-9]{1,8}", parts[-1])
    ):
        parts.pop()
    return "_".join(parts)


def scan(model, lo: float = 1e-6, hi: float = 1e6) -> dict:
    """Scan a model for extreme coefficients.

    Parameters
    ----------
    model : str | gurobipy.Model
        Path to an .lp/.mps(.gz) file, or an already-built Model.
    lo, hi : float
        Thresholds. Matrix/objective/RHS entries with 0 < |v| < lo or
        |v| > hi are flagged; finite bounds are flagged above hi only.

    Returns
    -------
    dict of DataFrames:
        summary     one row per component with min/max/orders of magnitude
        matrix      flagged A-matrix entries (row, col, families, coef)
        objective   flagged objective coefficients
        rhs         flagged RHS values
        bounds      flagged finite variable bounds
        row_spread  per-row min/max |coef| and their ratio, sorted worst first
    """
    if isinstance(model, str):
        gp.setParam("OutputFlag", 0)
        model = gp.read(model)

    A = model.getA().tocoo()
    constrs = model.getConstrs()
    dvars = model.getVars()
    rnames = np.array([c.ConstrName for c in constrs])
    cnames = np.array([v.VarName for v in dvars])
    rfam = np.array([family(n) for n in rnames])
    cfam = np.array([family(n) for n in cnames])

    absdata = np.abs(A.data)
    nz = absdata > 0

    # ---- matrix ---------------------------------------------------------
    flag = nz & ((absdata < lo) | (absdata > hi))
    idx = np.nonzero(flag)[0]
    matrix = pd.DataFrame({
        "row_name": rnames[A.row[idx]],
        "col_name": cnames[A.col[idx]],
        "row_family": rfam[A.row[idx]],
        "col_family": cfam[A.col[idx]],
        "coef": A.data[idx],
    })
    matrix["abs_coef"] = matrix["coef"].abs()
    matrix["side"] = np.where(matrix["abs_coef"] < lo, "small", "large")
    matrix = matrix.sort_values("abs_coef").reset_index(drop=True)

    # ---- objective ------------------------------------------------------
    obj_c = np.array([v.Obj for v in dvars])
    onz = obj_c != 0
    oflag = onz & ((np.abs(obj_c) < lo) | (np.abs(obj_c) > hi))
    oidx = np.nonzero(oflag)[0]
    objective = pd.DataFrame({
        "col_name": cnames[oidx],
        "col_family": cfam[oidx],
        "coef": obj_c[oidx],
    })
    objective["abs_coef"] = objective["coef"].abs()
    objective["side"] = np.where(objective["abs_coef"] < lo, "small", "large")
    objective = objective.sort_values("abs_coef", ascending=False).reset_index(drop=True)

    # ---- rhs ------------------------------------------------------------
    rhs_v = np.array([c.RHS for c in constrs])
    rnz = rhs_v != 0
    rflag = rnz & ((np.abs(rhs_v) < lo) | (np.abs(rhs_v) > hi))
    ridx = np.nonzero(rflag)[0]
    rhs = pd.DataFrame({
        "row_name": rnames[ridx],
        "row_family": rfam[ridx],
        "rhs": rhs_v[ridx],
    })
    rhs["abs_rhs"] = rhs["rhs"].abs()
    rhs["side"] = np.where(rhs["abs_rhs"] < lo, "small", "large")
    rhs = rhs.sort_values("abs_rhs", ascending=False).reset_index(drop=True)

    # ---- bounds (big-M detection) ---------------------------------------
    brec = []
    for v, cn, cf in zip(dvars, cnames, cfam):
        for which, b in (("LB", v.LB), ("UB", v.UB)):
            if np.isfinite(b) and b != 0 and abs(b) > hi:
                brec.append((cn, cf, which, b))
    bounds = pd.DataFrame(brec, columns=["col_name", "col_family", "which", "bound"])
    if len(bounds):
        bounds = bounds.sort_values("bound", key=np.abs, ascending=False).reset_index(drop=True)

    # ---- per-row spread -------------------------------------------------
    rmin = defaultdict(lambda: np.inf)
    rmax = defaultdict(float)
    for k in np.nonzero(nz)[0]:
        i = A.row[k]
        a = absdata[k]
        if a < rmin[i]:
            rmin[i] = a
        if a > rmax[i]:
            rmax[i] = a
    rows = np.array(sorted(rmax))
    row_spread = pd.DataFrame({
        "row_name": rnames[rows],
        "row_family": rfam[rows],
        "min_abs": [rmin[i] for i in rows],
        "max_abs": [rmax[i] for i in rows],
    })
    row_spread["spread"] = row_spread["max_abs"] / row_spread["min_abs"]
    row_spread = row_spread.sort_values("spread", ascending=False).reset_index(drop=True)

    # ---- summary --------------------------------------------------------
    def _rng(a):
        a = a[a > 0]
        return (a.min(), a.max(), np.log10(a.max() / a.min())) if len(a) else (np.nan,) * 3

    comp = {
        "matrix": absdata,
        "objective": np.abs(obj_c[onz]),
        "rhs": np.abs(rhs_v[rnz]),
    }
    summary = pd.DataFrame(
        [(k, *_rng(v)) for k, v in comp.items()],
        columns=["component", "min_abs", "max_abs", "orders"],
    )

    return {
        "summary": summary,
        "matrix": matrix,
        "objective": objective,
        "rhs": rhs,
        "bounds": bounds,
        "row_spread": row_spread,
    }


def family_table(matrix_df: pd.DataFrame) -> pd.DataFrame:
    """Pivot flagged matrix entries into a family-pair overview table."""
    return (
        matrix_df.groupby(["row_family", "col_family", "side"])
        .agg(n=("coef", "size"),
             min_abs=("abs_coef", "min"),
             max_abs=("abs_coef", "max"))
        .reset_index()
        .sort_values("n", ascending=False)
    )