import gurobipy as gp

m = gp.read('data/clews_data/clews_build_data/Model_Kotzur/Base_CNZ/Base_CNZ.lp')
m.Params.LogToConsole = 1
m.Params.LogFile = 'tools/diag.log'
m.Params.Method = 1            # dual simplex
m.Params.DualReductions = 0    # separate infeasible from unbounded
m.Params.Threads = 16
m.Params.TimeLimit = 1800
m.optimize()

print('\nstatus =', m.Status)
print('  3 = INFEASIBLE, 5 = UNBOUNDED, 2 = OPTIMAL, 9 = TIME_LIMIT')
if m.Status == 5:
    m.setParam('InfUnbdInfo', 1)
    ray = [(v.VarName, v.UnbdRay) for v in m.getVars() if abs(v.UnbdRay) > 1e-9]
    print(f'\nunbounded ray, {len(ray)} nonzero entries, first 25:')
    for n, x in sorted(ray, key=lambda t: -abs(t[1]))[:25]:
        print(f'  {x:14.4f}  {n}')
