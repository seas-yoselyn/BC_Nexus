import pandas as pd
from pathlib import Path

S = Path('data/clews_data/SETs')

print('=== land tier capacity parameters ===')
for p in ['ResidualCapacity', 'OperationalLife', 'CapacityToActivityUnit',
          'TotalAnnualMaxCapacity', 'TotalAnnualMinCapacity',
          'TotalTechnologyAnnualActivityLowerLimit',
          'TotalTechnologyAnnualActivityUpperLimit']:
    f = S / f'{p}.csv'
    if not f.exists():
        print(f'{p:42s} FILE MISSING')
        continue
    df = pd.read_csv(f)
    lnd = df[df.TECHNOLOGY.str.startswith('LND', na=False)]
    if lnd.empty:
        print(f'{p:42s} no LND rows')
        continue
    if 'YEAR' in lnd.columns:
        yrs = sorted(lnd.YEAR.unique())
        print(f'{p:42s} {len(lnd):6d} rows | years {yrs[0]}-{yrs[-1]} '
              f'| techs {lnd.TECHNOLOGY.nunique()}')
        nz = lnd[lnd.VALUE != 0].groupby('YEAR').size()
        print(f'{"":42s} nonzero rows by year: '
              f'{ {y: int(nz.get(y, 0)) for y in range(2024, 2029) if y in yrs} }')
    else:
        print(f'{p:42s} {len(lnd):6d} rows | no YEAR '
              f'| values {sorted(lnd.VALUE.unique())[:6]}')

print()
print('=== every parameter that steps between 2025 and 2026 ===')
for f in sorted(S.glob('*.csv')):
    try:
        df = pd.read_csv(f)
    except Exception:
        continue
    if 'YEAR' not in df.columns or 'VALUE' not in df.columns:
        continue
    keys = [c for c in df.columns if c not in ('YEAR', 'VALUE')]
    if not keys:
        continue
    a = df[df.YEAR == 2025].set_index(keys)['VALUE']
    b = df[df.YEAR == 2026].set_index(keys)['VALUE']
    a = a[~a.index.duplicated()]
    b = b[~b.index.duplicated()]
    j = a.to_frame('y25').join(b.to_frame('y26'), how='outer')
    d = (j.y25.fillna(0) - j.y26.fillna(0)).abs()
    ch = j[d > 1e-9]
    if len(ch):
        rel = ch.index.get_level_values('TECHNOLOGY') if 'TECHNOLOGY' in keys else None
        tag = ''
        if rel is not None:
            n = sum(1 for t in rel if str(t).startswith('LND'))
            tag = f' | LND rows: {n}'
        print(f'{f.stem:42s} {len(ch):6d} changed{tag}')
        print(ch.head(4).to_string())
