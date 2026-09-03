import pandas as pd
from pathlib import Path

DIRS = [Path('data/clews_data/SETs'),
        Path('data/clews_data/clews_build_data/input_csvs'),
        Path('data/clews_data/clews_build_data/Model_Kotzur/storage_case_input_csvs')]

for D in DIRS:
    if not (D / 'TECHNOLOGY.csv').exists():
        print(f'\n### {D}  -- no TECHNOLOGY.csv, skipped')
        continue
    techs = set(pd.read_csv(D / 'TECHNOLOGY.csv')['VALUE'])
    print(f'\n### {D}   ({len(techs)} technologies)')
    print('LNDAGV in TECHNOLOGY set:',
          sorted(t for t in techs if t.startswith('LNDAGV'))[:4], '...')

    for f in sorted(D.glob('*.csv')):
        try:
            df = pd.read_csv(f)
        except Exception:
            continue
        if 'TECHNOLOGY' not in df.columns:
            continue
        orph = sorted(set(df.TECHNOLOGY.dropna().unique()) - techs)
        if orph:
            print(f'  {f.stem:44s} {len(orph):4d} orphan techs  {orph[:3]}')

    print('  -- land tier capacity params --')
    for p in ['ResidualCapacity', 'OperationalLife', 'CapacityToActivityUnit',
              'TotalAnnualMaxCapacity',
              'TotalTechnologyAnnualActivityLowerLimit',
              'TotalTechnologyAnnualActivityUpperLimit']:
        f = D / f'{p}.csv'
        if not f.exists():
            print(f'  {p:44s} FILE MISSING')
            continue
        df = pd.read_csv(f)
        lnd = df[df.TECHNOLOGY.str.startswith('LND', na=False)]
        live = lnd[lnd.TECHNOLOGY.isin(techs)]
        if 'YEAR' in df.columns and len(live):
            yrs = sorted(live.YEAR.unique())
            print(f'  {p:44s} {len(live):5d} live LND rows | '
                  f'{yrs[0]}-{yrs[-1]} | techs {live.TECHNOLOGY.nunique()}')
        else:
            print(f'  {p:44s} {len(live):5d} live LND rows | '
                  f'values {sorted(live.VALUE.unique())[:5]}')

D = DIRS[2] if (DIRS[2] / 'TECHNOLOGY.csv').exists() else DIRS[1]
print(f'\n=== 2025 to 2026 steps in {D} ===')
for f in sorted(D.glob('*.csv')):
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
    a, b = a[~a.index.duplicated()], b[~b.index.duplicated()]
    j = a.to_frame('y25').join(b.to_frame('y26'), how='outer')
    ch = j[(j.y25.fillna(0) - j.y26.fillna(0)).abs() > 1e-9]
    if len(ch):
        tag = ''
        if 'TECHNOLOGY' in keys:
            r = ch.index.get_level_values('TECHNOLOGY')
            tag = f" | LND {sum(1 for t in r if str(t).startswith('LND'))}"
        print(f'{f.stem:44s} {len(ch):6d} changed{tag}')
        print(ch.head(3).to_string())
