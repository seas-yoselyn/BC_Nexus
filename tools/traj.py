import pandas as pd
from pathlib import Path
pd.set_option('display.width', 200)

D = Path('data/clews_data/clews_build_data/Model_Kotzur/storage_case_input_csvs')
techs = set(pd.read_csv(D / 'TECHNOLOGY.csv')['VALUE'])
lnd = sorted(t for t in techs if t.startswith('LND'))
agv = [t for t in lnd if t.startswith('LNDAGV')]

print('=== land tier coverage ===')
for p in ['ResidualCapacity', 'OperationalLife', 'CapacityToActivityUnit']:
    df = pd.read_csv(D / f'{p}.csv')
    have = set(df.TECHNOLOGY) & set(lnd)
    print(f'{p:26s} covers {len(have):3d}/{len(lnd)} land techs | '
          f'AGV covered: {len(set(agv) & have)}/{len(agv)}')
    miss = sorted(set(lnd) - have)
    print(f'{"":26s} missing: {miss[:6]}{" ..." if len(miss) > 6 else ""}')

print('\n=== mode 52 VariableCost trajectory (one cluster) ===')
vc = pd.read_csv(D / 'VariableCost.csv')
m52 = vc[(vc.TECHNOLOGY == 'LNDAGRBC1C01') & (vc.MODE_OF_OPERATION == 52)]
print(m52.set_index('YEAR')['VALUE'].to_string())

print('\n=== gas must run trajectory ===')
ll = pd.read_csv(D / 'TotalTechnologyAnnualActivityLowerLimit.csv')
g = ll[ll.TECHNOLOGY.str.startswith('PWRNGS')]
print(g.pivot_table(index='YEAR', columns='TECHNOLOGY', values='VALUE').to_string())

print('\n=== ResidualCapacity, land total by year ===')
rc = pd.read_csv(D / 'ResidualCapacity.csv')
rl = rc[rc.TECHNOLOGY.isin(lnd)]
s = rl.groupby('YEAR').VALUE.sum()
print(pd.DataFrame({'total': s, 'delta': s.diff()}).to_string())

print('\n=== AGV rows in any parameter file ===')
for f in sorted(D.glob('*.csv')):
    try:
        df = pd.read_csv(f)
    except Exception:
        continue
    if 'TECHNOLOGY' not in df.columns:
        continue
    n = df.TECHNOLOGY.isin(agv).sum()
    if n:
        print(f'  {f.stem:44s} {n:5d} rows')
