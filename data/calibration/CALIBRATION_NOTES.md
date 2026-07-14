<!--
title: BCNexus Calibration Notes
author: M Eliasinul Islam (EL)
date: 2026-07-14
-->

# BCNexus Calibration — Benchmarks, Fixes, and Ready-to-Paste Data

This note consolidates the 2021–2026 calibration diagnosis, the code/data fixes applied, benchmark
values against BC actuals, and copy-paste-ready parameter rows for the full-horizon (2021–2050) runs.

---

## 1. Benchmark: model vs. BC actuals

Model unit: PJ. Conversion: 1 PJ = 277.778 GWh.

| Quantity | BC actual | Model (calibrated) | Assessment |
|---|---|---|---|
| Total generation 2021 | 71.7 TWh (258.1 PJ) — CER | ~232 PJ required (demand 208.8 + trans. losses) | Model excludes exports/imports; BC traded net ~5–10 TWh/yr |
| Hydro generation 2021 | ~87–90 % of total — CER | 242.1 PJ (67.3 TWh) pre-fix | Consistent once storage pseudo-fuel excluded from plots |
| Biomass generation 2023 | 3.9 TWh (14.0 PJ) — CER | 0 (uncorrected) | Needs contract floor (§3.1) |
| Wind generation 2023 | 1.8 TWh (6.5 PJ) — CER | ~0 (uncorrected) | Runs on merit after VOM fixes |
| Solar generation 2023 | 0.007 TWh — CER | ~0 | Consistent |
| Net imports 2023 | 11.2 TWh (drought) — CER | not represented | Structural gap: no ELC trade techs |
| Hydro capacity | 15,953 MW — CER | 17.73 GW (B01 12.42 + B02 5.30) | Verify IPP hydro inclusion in PWRHYDB02 |
| Wind capacity | 702 MW — CER | 728 MW (B01–B08) | Consistent |
| Electricity demand IND (2020) | 23.3 TWh — CER | 88.7 PJ = 24.6 TWh (2021) | Consistent |
| Electricity demand RES (2020) | 20.2 TWh — CER | 65.7 PJ = 18.3 TWh (2021) | Check growth assumption |
| Electricity demand COM (2020) | 14.5 TWh — CER | 53.0 PJ = 14.7 TWh (2021) | Consistent |

Sources: CER Provincial Energy Profile (BC); CER Renewable Energy in Canada (BC); StatCan
"Electricity year in review 2023". Per-source splits for 2021–2022, 2024–2025: StatCan Table
25-10-0020-01 (marked TO FILL in `BC_electricity_actuals.csv`).

---

## 2. Root causes identified (session log 2026-07-13/14)

1. **Plotting** — `get_annual_power_generation_plot` plotted PJ under a GWh axis label and included
   the `WATER_STORAGE01` pseudo-fuel (+42 % apparent hydro). Timeslice plot used consumption data,
   a dimensionally wrong MW conversion, and a hardcoded 24-ts argument.
2. **LP degeneracy** — zero variable cost on the hydro→transmission→demand chain allowed costless
   overproduction (production ≥ demand is an inequality in OSeMOSYS). Fixed via data-driven hydro
   VOM (§3.3); any zero-cost chain segment reintroduces the problem.
3. **Updater crash (silent)** — `add_technologies_variable_cost` raised `KeyError` on techs without
   `variable_cost` (first: CCS01); a blanket `try/except` in `update_yearly_params.main()` swallowed
   it and silently skipped storage links and max-capacity updates. Guard added; **recommend adding
   `raise` to the except block.**
4. **Generated config** — `clews_builder.yaml` is regenerated on every build by `update_clews_builder_config`;
   manual edits to generated blocks (PWRHYD, PWRWND, PWRSOL, PWRBIO, PWRNGS, INFLOW) are wiped.
   Persistent values must be set in the generators (`create_schema_*` in `schema.py`).
5. **Units at the data→model boundary** — model VariableCost is M$/PJ (= $/GJ).
   `variable_om_cost_CAD_per_MWh` must be ÷ 3.6. Future-VRE `vom` (NREL ATB) is **fixed** O&M in
   $/kW-yr — dimensionally wrong for VariableCost (schema.py lines ~639, ~654, ~833). Hydro fixed;
   VRE/tpp pending.
6. **Horizon truncation** — `trim_snapshot_data` permanently trimmed persistent `input_csvs` to the
   calibration snapshot; extending the snapshot to 2050 left most year-indexed params defaulting
   (AnnualEmissionLimit → −1 → `E8 … <= -1` infeasibility, empty LHS). Fix:
   `get_csv_template(force_replace=True)` before build (templates span 2050).
7. **Dispatch realism** — with correct costs the merit order (hydro 1.2, VRE ~0, bio 6.6–8.1,
   gas ~12.9 $/GJ) never dispatches bio/gas. Reality: biomass = must-take EPAs; gas = reliability.
   Encode as constraints (§3.1) or capacity-credit reserve margin.

---

## 3. Copy-paste-ready data

### 3.1 `TotalTechnologyAnnualActivityLowerLimit.csv` — contracted biomass floor

Floor = 14.0 PJ/yr (3.9 TWh, CER 2023). Split by capacity share (B01 0.022 GW / B02 0.945 GW →
~2 % / 98 %). Extend or taper beyond 2035 per EPA-expiry assumptions.

```csv
REGION,TECHNOLOGY,YEAR,VALUE
REGION1,PWRBIOB01,2021,0.3
REGION1,PWRBIOB01,2022,0.3
REGION1,PWRBIOB01,2023,0.3
REGION1,PWRBIOB01,2024,0.3
REGION1,PWRBIOB01,2025,0.3
REGION1,PWRBIOB01,2026,0.3
REGION1,PWRBIOB02,2021,13.7
REGION1,PWRBIOB02,2022,13.7
REGION1,PWRBIOB02,2023,13.7
REGION1,PWRBIOB02,2024,13.7
REGION1,PWRBIOB02,2025,13.7
REGION1,PWRBIOB02,2026,13.7
REGION1,PWRBIOB02,2027,13.7
REGION1,PWRBIOB02,2028,13.7
REGION1,PWRBIOB02,2029,13.7
REGION1,PWRBIOB02,2030,13.7
REGION1,PWRBIOB02,2031,13.7
REGION1,PWRBIOB02,2032,13.7
REGION1,PWRBIOB02,2033,13.7
REGION1,PWRBIOB02,2034,13.7
REGION1,PWRBIOB02,2035,13.7
```

Historical gas floor (2021–2025): **TO FILL** from StatCan 25-10-0020-01 (BC gas generation was
~2–3 % of total; do not guess — insert the reported GWh ÷ 277.778).

> PWRNGSB01: 0.37 GW × 31.536 × 0.906 ≈ 10.6 PJ (but drops to 0.08 GW from 2024 → max ≈ 2.3 PJ)
> PWRNGSB02: 0.11 GW × 31.536 × 0.799 ≈ 2.8 PJ 
> Magnitude. 10 PJ/yr total ≈ 2.8 TWh — above BC's reported ~2–3% of ~72 TWh (≈ 1.5–2.2 TWh ≈ 5.4–7.9 PJ). A floor should sit below the actual, not at the ceiling of the plausible range.
> Finalized block — total ≈ 6 PJ (1.7 TWh ≈ 2.3% of 2021 generation), split by capacity share, stepped down when B01's residual capacity drops in 2024, everything ≤ 85% of technical max:
```csv
REGION,TECHNOLOGY,YEAR,VALUE
REGION1,PWRNGSB01,2021,4.6
REGION1,PWRNGSB01,2022,4.6
REGION1,PWRNGSB01,2023,4.6
REGION1,PWRNGSB01,2024,1.8
REGION1,PWRNGSB01,2025,1.8
REGION1,PWRNGSB02,2021,1.4
REGION1,PWRNGSB02,2022,1.4
REGION1,PWRNGSB02,2023,1.4
REGION1,PWRNGSB02,2024,1.4
REGION1,PWRNGSB02,2025,1.4
```

### 3.2 `AnnualEmissionLimit.csv` — CNZ trajectory (Mt CO2e)

Targets from `constants.emission_targets` (40 @ 2030, 25 @ 2040, 0 @ 2050), linear between;
non-binding (999) through 2029. Replace the template's flat 999 rows.

```csv
REGION,EMISSION,YEAR,VALUE
REGION1,CO2,2021,999
REGION1,CO2,2022,999
REGION1,CO2,2023,999
REGION1,CO2,2024,999
REGION1,CO2,2025,999
REGION1,CO2,2026,999
REGION1,CO2,2027,999
REGION1,CO2,2028,999
REGION1,CO2,2029,999
REGION1,CO2,2030,40.0
REGION1,CO2,2031,38.5
REGION1,CO2,2032,37.0
REGION1,CO2,2033,35.5
REGION1,CO2,2034,34.0
REGION1,CO2,2035,32.5
REGION1,CO2,2036,31.0
REGION1,CO2,2037,29.5
REGION1,CO2,2038,28.0
REGION1,CO2,2039,26.5
REGION1,CO2,2040,25.0
REGION1,CO2,2041,22.5
REGION1,CO2,2042,20.0
REGION1,CO2,2043,17.5
REGION1,CO2,2044,15.0
REGION1,CO2,2045,12.5
REGION1,CO2,2046,10.0
REGION1,CO2,2047,7.5
REGION1,CO2,2048,5.0
REGION1,CO2,2049,2.5
REGION1,CO2,2050,0.0
```

### 3.3 Hydro variable cost (reference — now generated automatically)

`create_schema_hydro` writes capacity-weighted VOM, CAD/MWh ÷ 3.6 → $/GJ:
reservoir (PWRHYDB01) ≈ 1.16, run-of-river (PWRHYDB02) ≈ 0.58; fallback 0.001 as degeneracy
tie-breaker. Do **not** re-add these manually to the yaml — they are wiped and regenerated.

---
