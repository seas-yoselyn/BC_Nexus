Adapted from [OSeMOSYS Structure](https://osemosys.readthedocs.io/en/latest/manual/Structure%20of%20OSeMOSYS.html)  

Interpretation: **`Type (used/total)`**

# Sets (7/11)
The ‘sets’ define the physical structure of a model, usually independent from the specific scenarios which will be run. They define the time domain and time split, the spatial coverage, the technologies and energy vectors to be considered, etc. The SETS are handled by [module structure module](https://github.com/DeltaE/BC_Nexus/blob/main/bcnexus/clews/model_structure.py)+ [sets_n_ratio module](https://github.com/DeltaE/BC_Nexus/blob/main/bcnexus/clews/sets_n_ratios.py).
 > the legacy model handled this part with a config + _clewsy_ tool.

| Used | *Not Used* |
| :- | :--- |
|EMISSION (e)<br/>FUEL (f)<br/>MODE_OF_OPERATION (m)<br />REGION (r)<br/>TECHNOLOGY (t)<br/>TIMESLICE (l)<br />YEAR (y)<br /> STORAGE (s)| DAYTYPE (ld)<br /> DAILYTIMEBRACKET (lh) <br />SEASON (ls)<br />

# Parameters
## Global Parameters (1/9)
The parameters are the user-defined numerical inputs to the model. While usually the structure of a model, therefore the sets, remains fixed across scenarios, it is common practice to change the values of some parameters when running different scenarios and/or sensitivity analyses. Each parameter is a function of the elements in one or more sets.

| Used | *Not Used* |
| :- | :--- |
|YearSplit| *DiscountRate<br />DaySplit<br />Conversionls<br />Conversionld<br />Conversionlh<br />DaysInDayType<br />TradeRoute<br />DepreciationMethod*|

## Demands (3/3)

| Used | *Not Used* |
| :- | :--- |
|AccumulatedAnnualDemand<br />SpecifiedAnnualDemand<br />SpecifiedDemandProfile|-||

## Performance (7/7)

| Used | *Not Used* |
| :- | :--- |
|CapacityToActivityUnit<br />AvailabilityFactor<br />OperationalLife<br />CapacityFactor<br />InputActivityRatio<br />OutputActivityRatio<br />ResidualCapacity|-||

## Technology Costs (3/3)

| Used | *Not Used* |
| :- | :--- |
|CapitalCost<br />VariableCost<br />FixedCost.csv|-|

## Capacity Constraints (1/3)

| Used | *Not Used* |
| :- | :--- |
|TotalAnnualMaxCapacity<br />TotalAnnualMinCapacity<br />| CapacityOfOneTechnologyUnit|

## Activity Constraints (2/4)

| Used | *Not Used* |
| :- | :--- |
|TotalTechnologyAnnualActivityUpperLimit<br />TotalTechnologyModelPeriodActivityUpperLimit|*TotalTechnologyAnnualActivityLowerLimit<br />TotalTechnologyModelPeriodActivityLowerLimit*|

## Investment Constraints (2/2)

| Used | *Not Used* |
| :- | :--- |
|TotalAnnualMaxCapacityInvestment<br />TotalAnnualMinCapacityInvestment|-|

## Reserve Margin (3/3)

| Used | *Not Used* |
| :- | :--- |
|ReserveMarginTagTechnology<br />ReserveMarginTagFuel<br />ReserveMargin|-|

## Emissions (4/6)

| Used | *Not Used* |
| :- | :--- |
|EmissionActivityRatio<br />EmissionsPenalty<br />AnnualEmissionLimit<br />ModelPeriodEmissionLimit<br />|*AnnualExogenousEmission<br />ModelPeriodExogenousEmission*|

## RE Generation Target (-/3)

| Used | *Not Used* |
| :- | :--- |
|-|RETagTechnology<br />RETagFuel<br />REMinProductionTarget<br />|

## Storage (-/9)

| Used | *Not Used* |
| :- | :--- |
|TechnologyToStorage<br />TechnologyFromStorage<br />OperationalLifeStorage<br />CapitalCostStorage<br />|StorageLevelStart<br />StorageMaxChargeRate<br />StorageMaxDischargeRate<br />MinStorageCharge<br />ResidualStorageCapacity<br />|

# Variables
Read [this](https://osemosys.readthedocs.io/en/latest/manual/Structure%20of%20OSeMOSYS.html#variables)

# Equations
Read [this](https://osemosys.readthedocs.io/en/latest/manual/Structure%20of%20OSeMOSYS.html#equations)

> BC Nexus model has some modified equations but the above documentation will give the idea.