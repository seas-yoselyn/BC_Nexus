"""
Which constraints actually conflict?

When the solve reports "Model is infeasible", Gurobi can compute an IIS - an
Irreducible Inconsistent Subsystem - the smallest set of constraints and
bounds that cannot all hold at once. Removing any one of them makes the rest
satisfiable, so the answer is in there by construction. That beats guessing.

    python tools/diagnose_infeasible.py                       # finds the LP
    python tools/diagnose_infeasible.py path/to/model.lp

Writes <model>.ilp next to the LP and prints a summary grouped by constraint
family, with the land and water constraints this project has been editing
called out first.

Needs gurobipy and a licence - the same one the solve uses. Read-only apart
from the .ilp it writes. An IIS costs roughly what one solve costs.
"""
import sys
from pathlib import Path

try:
    import gurobipy as gp
except ImportError:
    sys.exit("needs gurobipy - run inside the bcnexus conda environment")

BUILD = Path("data/clews_data/clews_build_data")

# Constraint-name prefixes worth calling out, and what they mean. OSeMOSYS
# names its constraints by block; these are the ones this project's land and
# water fixes touch.
INTERESTING = {
    "TotalAnnualTechnologyActivityUpperLimit": "activity ceiling (our caps)",
    "TotalAnnualTechnologyActivityLowerLimit": "activity floor (our pins)",
    "TotalAnnualMaxCapacityConstraint": "capacity ceiling (our pins)",
    "TotalAnnualMinCapacityConstraint": "capacity floor (our pins)",
    "EBa": "energy balance",
    "EBb": "energy balance",
    "Acc": "accumulated demand",
    "CAa": "capacity adequacy",
    "CBa": "capacity",
    "TAC": "total activity",
    "RM": "reserve margin",
}


def find_lp():
    if not BUILD.exists():
        return None
    lps = sorted(BUILD.rglob("*.lp"), key=lambda p: p.stat().st_mtime,
                 reverse=True)
    return lps[0] if lps else None


def family(name):
    """Group a constraint name by its leading alphabetic token."""
    head = name.split("(")[0].split("[")[0].split("_")[0]
    for prefix, label in INTERESTING.items():
        if name.startswith(prefix):
            return prefix, label
    return head, ""


def main():
    arg = [a for a in sys.argv[1:] if not a.startswith("-")]
    lp = Path(arg[0]) if arg else find_lp()
    if lp is None or not lp.exists():
        sys.exit(f"no .lp found under {BUILD} - build the model first")

    print(f"reading {lp}")
    model = gp.read(str(lp))
    model.setParam("OutputFlag", 0)

    print("computing IIS (this takes about as long as one solve) ...")
    model.computeIIS()

    ilp = lp.with_suffix(".ilp")
    model.write(str(ilp))

    rows = [c for c in model.getConstrs() if c.IISConstr]
    lo = [v for v in model.getVars() if v.IISLB]
    hi = [v for v in model.getVars() if v.IISUB]

    print()
    print("=" * 70)
    print(f"IIS: {len(rows)} constraints, {len(lo)} lower bounds, "
          f"{len(hi)} upper bounds")
    print("=" * 70)

    groups = {}
    for c in rows:
        key, label = family(c.ConstrName)
        groups.setdefault((key, label), []).append(c.ConstrName)

    # Ours first, then everything else by size.
    def rank(item):
        (key, label), names = item
        return (0 if label else 1, -len(names))

    for (key, label), names in sorted(groups.items(), key=rank):
        tag = f"  <- {label}" if label else ""
        print(f"\n{key}  x{len(names)}{tag}")
        for n in names[:8]:
            print(f"    {n}")
        if len(names) > 8:
            print(f"    ... and {len(names) - 8} more")

    for title, vars_ in (("variables pinned at a LOWER bound", lo),
                         ("variables pinned at an UPPER bound", hi)):
        if not vars_:
            continue
        print(f"\n{title}  x{len(vars_)}")
        for v in vars_[:12]:
            print(f"    {v.VarName}")
        if len(vars_) > 12:
            print(f"    ... and {len(vars_) - 12} more")

    print(f"\nfull detail written to {ilp}")
    print("\nRead it like this: every line in the IIS is part of the conflict.")
    print("If our activity floors/ceilings appear, a pin is asking for "
          "something the rest of the model cannot deliver - relax that one.")


if __name__ == "__main__":
    main()
