import gurobipy as gp
from collections import Counter
import re

m = gp.read('data/clews_data/clews_build_data/Model_Kotzur/Base_CNZ/Base_CNZ.lp')
m.Params.LogToConsole = 1
m.Params.LogFile = 'tools/iis.log'
m.Params.Threads = 16
m.Params.IISMethod = 1          # faster, may not be minimal
m.Params.TimeLimit = 3600
m.computeIIS()
m.write('tools/infeasible.ilp')

cons = [c.ConstrName for c in m.getConstrs() if c.IISConstr]
lb = [v.VarName for v in m.getVars() if v.IISLB]
ub = [v.VarName for v in m.getVars() if v.IISUB]
print(f'\nIIS: {len(cons)} constraints, {len(lb)} lower bounds, {len(ub)} upper bounds')

fam = Counter(re.split(r'[\(_]', c)[0] for c in cons)
print('\nconstraint families:')
for k, v in fam.most_common(15):
    print(f'  {v:5d}  {k}')

print('\nfirst 30 constraints:')
for c in cons[:30]:
    print('  ', c)

tech = Counter()
for c in cons:
    for t in re.findall(r'\b(LND[A-Z0-9]+|PWR[A-Z0-9]+|LVS[A-Z0-9]+)\b', c):
        tech[t] += 1
print('\ntechnologies named in IIS:')
for k, v in tech.most_common(20):
    print(f'  {v:5d}  {k}')
