import time
import gurobipy as gp
import pandas as pd

LP = 'data/clews_data/clews_build_data/Model_Kotzur/Base_CNZ/Base_CNZ.lp'
THREADS = 16


def solve(label, crossover, barconvtol):
    m = gp.read(LP)
    m.Params.LogToConsole = 0
    m.Params.LogFile = f'tools/xover_{label}.log'
    m.Params.Method = 2
    m.Params.Threads = THREADS
    m.Params.NumericFocus = 2
    m.Params.ScaleFlag = 2
    m.Params.BarHomogeneous = 1
    m.Params.BarConvTol = barconvtol
    m.Params.Crossover = crossover
    t0 = time.time()
    m.optimize()
    dt = time.time() - t0
    print(f'{label:10s} status={m.Status:3d} time={dt:8.1f}s', end=' ')
    if m.SolCount:
        print(f'obj={m.ObjVal:.6e}')
        return {v.VarName: v.X for v in m.getVars() if abs(v.X) > 1e-9}
    print('NO SOLUTION')
    return None


def land(sol):
    """Pull TotalTechnologyAnnualActivity for the land tier out of the solution."""
    rows = []
    for name, val in sol.items():
        if not name.startswith('TotalTechnologyAnnualActivity'):
            continue
        inner = name[name.find('(') + 1:name.rfind(')')]
        parts = [p.strip() for p in inner.split(',')]
        if len(parts) != 3:
            continue
        _, tech, yr = parts
        if tech.startswith('LND'):
            rows.append((tech, int(yr), val))
    return (pd.DataFrame(rows, columns=['TECH', 'YEAR', 'VALUE'])
              .set_index(['TECH', 'YEAR'])['VALUE'])


base = solve('nocross', 0, 1e-04)
xov = solve('crossover', -1, 1e-08)

if base and xov:
    a, b = land(base), land(xov)
    j = a.to_frame('nocross').join(b.to_frame('crossover'), how='outer').fillna(0)
    j['diff'] = j.crossover - j.nocross
    print(f'\nland rows: {len(j)}  |  max abs diff: {j["diff"].abs().max():.4f}')
    print('\n=== AGV maize, both solves ===')
    agv = j[j.index.get_level_values("TECH").str.startswith("LNDAGVMAI")]
    print(agv.groupby(level='YEAR').sum().loc[[2021, 2025, 2026, 2030, 2050]].to_string())
    print('\n=== conventional maize, both solves ===')
    cnv = j[j.index.get_level_values("TECH").str.match(r"^LNDMAI")]
    print(cnv.groupby(level='YEAR').sum().loc[[2021, 2025, 2026, 2030, 2050]].to_string())
    print('\n=== 12 largest shifts ===')
    print(j.reindex(j['diff'].abs().sort_values(ascending=False).index).head(12).to_string())
