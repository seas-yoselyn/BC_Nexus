import pandas as pd
from pathlib import Path

S = Path('data/clews_data/SETs')
iar = pd.read_csv(S/'InputActivityRatio.csv')
oar = pd.read_csv(S/'OutputActivityRatio.csv')
mop = pd.read_csv(S/'MODE_OF_OPERATION.csv')
techs = set(pd.read_csv(S/'TECHNOLOGY.csv')['VALUE'])
fuels = set(pd.read_csv(S/'FUEL.csv')['VALUE'])

clu = iar[iar.TECHNOLOGY.str.startswith('LNDAGR')]
agv = clu[clu.FUEL.str.startswith('LAGV')]
modes = sorted(agv.MODE_OF_OPERATION.astype(int).unique())
print('AGV modes on cluster techs   :', modes)

ml = S/'ModeList.txt'
if ml.exists():
    txt = ml.read_text().split()
    print('ModeList.txt entries         :', len(txt),
          '| AGV labels:', sum(1 for t in txt if t.startswith('AGV')))
else:
    print('ModeList.txt                 : MISSING')
print('missing from MODE_OF_OPERATION:',
      [m for m in modes if m not in set(mop.VALUE.astype(int))])

alloc = sorted(t for t in techs if t.startswith('LNDAGV'))
lagv  = sorted(f for f in fuels if f.startswith('LAGV'))
print('LNDAGV techs / LAGV fuels    :', len(alloc), '/', len(lagv))

prod = set(oar[oar.FUEL.str.startswith('LAGV')].FUEL)
cons = set(agv.FUEL)
print('LAGV produced not consumed   :', sorted(prod - cons))
print('LAGV consumed not produced   :', sorted(cons - prod))

bad = agv.groupby('MODE_OF_OPERATION').FUEL.nunique()
print('modes with >1 LAGV fuel      :', bad[bad > 1].to_dict())

leak = clu[clu.MODE_OF_OPERATION.isin(modes)
           & clu.FUEL.str.match(r'^L(?!AGV)')]
print('legacy conv land IAR on AGV modes:', len(leak), list(leak.FUEL.unique())[:5])

yr = agv.groupby('MODE_OF_OPERATION').YEAR.agg(['min', 'max', 'nunique'])
print('AGV year coverage            :', yr['min'].min(), yr['max'].max(),
      '| distinct year counts:', sorted(yr['nunique'].unique()))

pairs = agv.assign(combo=agv.FUEL.str[4:-3])
conv = (clu[clu.FUEL.str.match(r'^L(?!AGV|BC1)')]
        .assign(combo=lambda d: d.FUEL.str[1:-3]))
a = set(zip(pairs.TECHNOLOGY, pairs.combo))
c = set(zip(conv.TECHNOLOGY, conv.combo))
print('AGV cluster-combos with no conventional parent:', len(a - c))
for x in sorted(a - c)[:8]:
    print('    ', x)

d = agv.duplicated(subset=['REGION', 'TECHNOLOGY', 'FUEL',
                           'MODE_OF_OPERATION', 'YEAR']).sum()
print('duplicate AGV IAR rows       :', d)
print('ELCB01 OAR values on AGV modes:',
      sorted(oar[oar.TECHNOLOGY.str.startswith('LNDAGR')
                 & (oar.FUEL == 'ELCB01')].VALUE.unique())[:5])
