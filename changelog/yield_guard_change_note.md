# Yield Guard in sets_n_ratios.py

*Change note and impact assessment, BC Nexus model*

Elias Islam, Delta E+ Research Group, Simon Fraser University. 
Report Date: 19 July 2026.

## Summary

A guard added to `sets_n_ratios.py` now skips agricultural land-use modes whose cluster-mean crop yield falls below 1e-4 after calibration. The change removes OutputActivityRatio coefficients at the 1e-8 to 1e-7 scale from the LP matrix. These coefficients contributed to a 14 order of magnitude coefficient range that caused the Gurobi barrier method to stall with sub-optimal termination. The change alters model structure only for cluster and crop combinations with negligible production potential.

## Problem

A 24-timeslice solve of the Kotzur Base_CNZ scenario terminated sub-optimally after 133 barrier iterations. The constraint matrix spanned coefficients from 9e-9 to 1e6. A coefficient scan traced 1,200 of the smallest entries to energy balance constraints (EBa11, EBb4) on crop commodities, with values between 4.03e-8 and 1.58e-7.

The generating chain was traced end to end. The LP coefficient equals the cluster yield from `clustering_results_BC1.csv`, multiplied by the calibration factor CropYieldFactors (0.95 for all crops) and by YearSplit. The exemplar coefficient 4.034232e-8 reconstructs as 3.9584e-7 (cluster 1, ALF Rain-fed Low) times 0.95 times a YearSplit of approximately 0.107. The pipeline introduces no error. The small values originate in the CSV.

## Root cause

Cluster-mean yields are averaged over all cells in a cluster, including cells under forest, barren, and other non-crop land uses. Cluster 1 contains 12,126 cells and 471.3 area units, of which cultivated land totals 1.98 units (0.42%). Its ALF yields fall near 1e-6. Cluster 3, with 3.6% cultivated share, shows ALF yields near 1e-1. The five order of magnitude spread between clusters reflects dilution by non-crop cells rather than agronomic variation.

The codebase already contained partial recognition of this issue. The irrigation input ratio carries a 1e-4 floor with the comment "fix to prevent scientific e-8 numbers from breaking the system". The crop output ratio, computed ten lines above, carried no equivalent guard.

## Change

A guard now executes at the top of the mode loop in `sets_n_ratios.py`, before any parameter rows are written for the mode. When the calibrated yield for a cluster and crop combination falls below 1e-4, the entire mode is skipped for that cluster.

```python
_yield_check = csv_yield * CropYieldFactors[crop]
if _yield_check < 0.0001:
    continue
```

Three design constraints shaped the implementation. First, the guard skips the whole mode rather than the output ratio alone. A mode retaining its land input ratio but lacking an output ratio would consume land while producing nothing, which the optimizer could exploit as a free land sink. Second, mode numbering is preserved because the enumeration continues across skipped entries, so mode-indexed references elsewhere in the configuration remain valid. Third, the guard steps aside when the combination label is absent from the CSV header, leaving original behavior unchanged in that case.

## Impact

Table 1 summarizes the guard outcome for ALF across the first three clusters of land region BC1.

**Table 1.** Guard outcome for alfalfa (ALF) by cluster, land region BC1. Yield ranges are raw CSV values across the five irrigation and intensity combinations, before the 0.95 calibration factor. All retained cluster 2 values remain above the 1e-4 threshold after calibration.

| Cluster | Cultivated share | ALF yield range      | Guard outcome (1e-4) |
|---------|------------------|----------------------|----------------------|
| 1       | 0.42%            | `3.96e-7 to 1.12e-6` | ALF modes removed    |
| 2       | 4.5%             | `1.32e-4 to 3.76e-4` | ALF modes retained   |
| 3       | 3.6%             | `4.90e-2 to 1.42e-1` | ALF modes retained   |

Numerical impact. The EBa11 and EBb4 coefficient families below 1e-6 are removed from the matrix. The matrix range contracts accordingly. Storage-related conditioning issues identified in the same audit are independent of this change and are addressed separately.

Structural impact. Excluded modes represent clusters where cultivated land is a negligible share of cluster area. The production potential removed is bounded by that share. The exact excluded share should be quantified at regeneration and reported alongside results.

Result impact. Prior solves permitted activity in the excluded modes. If those modes carried nonzero activity, earlier land-use results absorbed a small distortion in which near-zero-yield agriculture occupied land. Comparison of the next solve against the prior baseline will bound this effect.

## Limitations and alternatives considered

- The guard treats a symptom. The correct repair computes conditional yields over cultivated cells during clustering. That repair is deferred because re-clustering is not currently feasible.
- Reconstructing conditional yields from existing CSV columns was evaluated and rejected. De-diluted yields disagreed across clusters by up to four orders of magnitude, which indicates the dilution model is crop or cluster specific and unsafe as a blanket correction.
- Rescaling the crop commodity unit was rejected because it propagates into demand data, cost parameters, and downstream reporting.
- The 1e-4 threshold matches the existing irrigation guard for internal consistency. It is not derived from the cultivated-share distribution. The threshold appears as a literal in two places and should be promoted to a named constant in `model_structure.py`.

## Verification plan

- Confirm the minimum crop OutputActivityRatio in regenerated data is at least 9.5e-5.
- Re-run the coefficient scan. The EBa11 and EBb4 small-coefficient families should be absent.
- Quantify the cultivated area share of excluded modes for the methods documentation.
- Compare objective value and land allocation against the prior baseline. Material shifts would indicate the optimizer was exploiting the removed modes and warrant investigation before results are used.