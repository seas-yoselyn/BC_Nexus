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

## 2. Issues (session log 2026-07-14)

- **Dispatch realism** — with correct costs the merit order (hydro 1.2, VRE ~0, bio 6.6–8.1,
   gas ~12.9 $/GJ) never dispatches bio/gas. Reality: biomass = must-take EPAs; gas = reliability.
   Encode as constraints (§3.1) or capacity-credit reserve margin.

---

## 3. Copy-paste-ready data for Calibrating History

### 3.1 `TotalTechnologyAnnualActivityLowerLimit.csv` — contracted biomass floor

#### __Biomass__:

 - Floor = 14.0 PJ/yr (3.9 TWh, CER 2023). Split by capacity share (B01 0.022 GW / B02 0.945 GW →
  ~2 % / 98 %). Extend or taper beyond 2035 per EPA-expiry assumptions.
 - In 2021–2023 the max is 1.013 × 31.536 × 0.4433 = 14.16 PJ, so 13.7 just fits; from 2024 it doesn't.

  ```csv
  REGION,TECHNOLOGY,YEAR,VALUE
  REGION1,PWRBIOB01,2021,0.3
  REGION1,PWRBIOB01,2022,0.3
  REGION1,PWRBIOB01,2023,0.3
  REGION1,PWRBIOB01,2024,0.3
  REGION1,PWRBIOB01,2025,0.3
  REGION1,PWRBIOB01,2026,0.3
  REGION1,PWRBIOB02,2021,13.4
  REGION1,PWRBIOB02,2022,13.4
  REGION1,PWRBIOB02,2023,13.4
  REGION1,PWRBIOB02,2024,12.5
  REGION1,PWRBIOB02,2025,12.5
  REGION1,PWRBIOB02,2026,12.5
  REGION1,PWRBIOB02,2027,12.5
  REGION1,PWRBIOB02,2028,12.5
  REGION1,PWRBIOB02,2029,12.5
  REGION1,PWRBIOB02,2030,12.5
  REGION1,PWRBIOB02,2031,12.5
  REGION1,PWRBIOB02,2032,12.5
  REGION1,PWRBIOB02,2033,12.5
  REGION1,PWRBIOB02,2034,12.5
  REGION1,PWRBIOB02,2035,12.5
  ```

#### __Natural Gas__ :
  - Historical gas floor (2021–2025): **TO FILL** from StatCan 25-10-0020-01 (BC gas generation was
  ~2–3 % of total; do not guess — insert the reported GWh ÷ 277.778).

  - PWRNGSB01: 0.37 GW × 31.536 × 0.906 ≈ 10.6 PJ (but drops to 0.08 GW from 2024 → max ≈ 2.3 PJ)
  - PWRNGSB02: 0.11 GW × 31.536 × 0.799 ≈ 2.8 PJ 
  - Magnitude. 10 PJ/yr total ≈ 2.8 TWh — above BC's reported ~2–3% of ~72 TWh (≈ 1.5–2.2 TWh ≈ 5.4–7.9 PJ). A floor should sit below the actual, not at the ceiling of the plausible range.
  - Finalized block — total ≈ 6 PJ (1.7 TWh ≈ 2.3% of 2021 generation), split by capacity share, stepped down when B01's residual capacity drops in 2024, everything ≤ 85% of technical max:
    
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
> __Caution__:
> Hard Emission limits may trigger infeasibility if there are __Actual Annual demands__ that always creates emission.


### 3.3 Hydro variable cost (reference — now generated automatically)

`create_schema_hydro` writes capacity-weighted VOM, CAD/MWh ÷ 3.6 → $/GJ:
reservoir (PWRHYDB01) ≈ 1.16, run-of-river (PWRHYDB02) ≈ 0.58; fallback 0.001 as degeneracy
tie-breaker. Do **not** re-add these manually to the yaml — they are wiped and regenerated.

---

## 4. Biomass in end-use sectors (2026-07-19)

Diagnosed from `Model_Kotzur_Base_CNZ_noCCS / 24ts` results.

### 4.1 What the model does

| | 2021 | 2035 | 2050 |
|---|---|---|---|
| Total biomass (`RNWBIO`) | 268.0 PJ | 374.6 PJ | 357.0 PJ |
| Share of final energy | 22.4 % | 24.8 % | 21.6 % |
| CO₂ attributed to biomass | 13.9 Mt (24 % of gross) | — | 20.9 Mt (32 %) |

Destination (PJ):

| Sector | 2021 | 2030 | 2040 | 2050 |
|---|---|---|---|---|
| Industry (`DEMINDBIO`) | 185.8 | 245.7 | 262.2 | 270.7 |
| Transport (`DEMTRABIO`) | 30.5 | 52.8 | 53.0 | 57.7 |
| Residential (`DEMRESBIO`) | 11.8 | 17.9 | 16.9 | 16.9 |
| Commercial (`DEMCOMBIO`) | 0.8 | 11.7 | 11.1 | 11.4 |
| Power (`DEMPWRBIO`) | 39.1 | 39.4 | 7.8 | 0.2 |

Only the power-sector share responds to decarbonisation; end-use biomass grows throughout.

### 4.2 Root cause — biomass is prescribed, not chosen

The `DEM<SEC>BIO` technologies are **1:1 pass-throughs** (BIO in = sector fuel out, 100 %
efficiency; verified for IND/TRA/RES/COM in 2050). Each end-use fuel carries its **own exogenous
demand**, so the optimiser cannot substitute between fuels in end-use sectors. Evidence: every
industrial fuel grows in near-fixed proportion 2021 → 2050 —

| Industrial fuel | 2021 | 2050 | Growth |
|---|---|---|---|
| INDNGS | 218.4 | 335.6 | +54 % |
| INDBIO | 185.8 | 270.7 | +46 % |
| INDELCB02 | 88.7 | 166.6 | +88 % |
| INDDSL | 96.4 | 127.6 | +32 % |

No fuel is displaced. The biomass level therefore reflects the **demand projection's fuel split**
(CER Energy Futures sectoral fuels), not an economic choice by the model.

**Consequence:** placing an upper limit on `RNWBIO` would render the model infeasible (or force
unserved demand) rather than shift industry to electricity. A supply cap alone is the wrong fix.

### 4.3 Plausibility of the level

Published BC estimates (technical potential, verify before citing):

| Estimate | Value | Scope |
|---|---|---|
| Residues available beyond current forest-industry demand | 110–176 PJ/yr | incremental supply |
| Residues + silviculture plantations | 273 PJ/yr (≈ 24 % of BC energy) | total potential |
| Model 2021 / 2050 | 268 / 357 PJ | unconstrained |

The 2021 level is plausible: BC industry (pulping liquor, hog fuel) is unusually biomass-intensive.
The 2050 level sits between the "total potential" and "existing + full incremental" brackets while
BC's pulp sector is contracting — defensible only if stated as an assumption of the demand
projection, never as a model result.

Sources: BC Hydro *Wood Based Biomass Energy Potential of British Columbia*; BC Hydro
*Wood Based Biomass in BC and its Potential for New Electricity Generation* (2015);
Energy Policy, *GHG emission reduction potential and cost of bioenergy in BC* (2020);
CER *Canada's Bioenergy Diversity and Potential* (2023). **TO VERIFY:** whether the 273 PJ figure
double-counts residues already burned in-industry, and the BC industrial biomass baseline against
StatCan RESD Table 25-10-0029.

### 4.4 Actions

1. **Verify the demand split** — reconcile prescribed `INDBIO` demand with CER Energy Futures
   and StatCan RESD. If the projection holds industrial biomass roughly flat while the model grows
   it +46 %, the error is in demand construction, not supply.
2. **Enable fuel switching (structural)** — for end-use fuel choice to be endogenous, sectors must
   demand *useful energy* with competing conversion technologies, rather than one fixed demand per
   fuel. Larger change; required before any "biomass vs electrification" claim.
3. **Add a supply constraint only after (2)** — `TotalTechnologyAnnualActivityUpperLimit` on
   `RNWBIO` at 273 PJ (citable ceiling), with 176 and 450 PJ as sensitivity bounds.
4. **Decide biogenic-carbon convention** — biomass carries 20.9 Mt (32 % of gross) in 2050 under
   full stack accounting. Under IPCC convention, biogenic CO₂ from sustainable harvest is reported
   in LULUCF, not energy. State the choice explicitly and apply it consistently.

> **Do not report** biomass levels as a model finding until (1) and (2) are resolved; at present
> they restate the demand projection's assumptions.

---
