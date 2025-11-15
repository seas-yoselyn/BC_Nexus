# About configurations:

1. [config.yaml](https://github.com/DeltaE/BC_Combined_Modelling/blob/main/config/config.yaml)

   - Scenario config file for BC Combined Modelling project. BCNexus scenarios are configured with this yaml file.

2. [dashboard.yaml](https://github.com/DeltaE/BC_Combined_Modelling/blob/main/config/dashboard.yaml)
   - We update this to document description about the scenario and harmonizing plots' color coding and legends for all scenarios. When you define a scenario at _config.yaml_, you should update information inside this dashboard.yaml's _[info_SCENARIOS](https://github.com/DeltaE/BC_Combined_Modelling/blob/c35a62c7139ad9952d02cdd1c18e06b2f44662af/config/dashboard.yaml#L13)_ key.
  
3. [data.yaml](https://github.com/DeltaE/BC_Combined_Modelling/blob/main/config/data.yaml)
   - config for modelling data-pipeline. We use the automated data-pipeline for PyPSA and RESource/Linking Tool's workflow. This configuration helps to harmonize the directories of downloaded, processed and model-specific datasets.

4. [validate.yaml](https://github.com/DeltaE/BC_Combined_Modelling/blob/main/config/validate.yaml)
   - We use this config file to extract a summarized and simplified validation report on input dataset. It can be considered as a simplified sanity check on SETS and Parameters [Input_checker_summary_report.txt](https://github.com/DeltaE/BC_Combined_Modelling/blob/main/data/clews_data/Example_SCENARIO_datafiles/Base_CNZ/Input_checker_summary_report.txt)
   - The _Input_checker_summary_report.txt_ will be generated inside each 'data/clews_data/MODEL_Kotzur (or Storage Algorithm name)/ SCENARIO' directory.
   - The input checker summary report should echo your FUEL and TECH set-up aligned with the SCENARIO.If it gives unanticipated reprots, then you ahve recheck the SETS and Parameters of the SCENARIO input dataset.
  
----
__Future Scopes and development__:

- a. Improve the workflow to support more scenario axes and technologies.
- b. Improve user interaction with the scenario setup and explore alternative options like excel interface to collect scenario configuration.
- c. Improve error handling stemmed user scenario setup. Improve database of default parameters to validate user scenario attributes.
- d. Introduce key FUEL price in the model structure.
  > use the _VariableCost_ parameter to introduce fuel cost at source. [Learning resource here](https://www.open.edu/openlearncreate/af/fe/affe0cfdd553a719ded8df2f24600be44b944b88?response-content-disposition=inline%3Bfilename%3D%22Hands%20on%20lecture%204.pdf%22&response-content-type=application%2Fpdf&Expires=1745702280&Signature=ZgmxL-Tt2git-YHE4l2Brx4s9OZ8Fmo4uAupiiy~ys9FmQYu-nwLZWQ9Qc8V9R4gHORwrdejCERKPFyEQMCIwunar0p0vNKFDIIp0UXCxw9i9Rgr8iaQDZhFTVNnFUuvnZ7lpDD9pqNzcCeBBRyE1CXPxuuWTC6XIQG4l4gitKKs5oKKsJuqbaJklCcNQVw6xv6H90moU9EdOYbbPE03-QZ2MxgxBaHj1A-SRgheg7KeyT-uy7Veen-mgs2j8MAZXSq~HYJckB5g6AxW08AugtFo1EUGZsDdgTYxlz-VaHyEL5EY6ThHo4yILprBDoBc1nbWP9QH2asIg~qiX0gpaQ__&Key-Pair-Id=K19YM1UI0NPZI1)

- Create results processing automation to compare results from other capacity expansion/operational modelling frameworks.

  - [iamc_convert.yaml](https://github.com/DeltaE/BC_Combined_Modelling/blob/main/config/iamc_convert.yaml)
    - Still under testing and development stage. The aim is to use this config to create results compatible with [Integrated Assessment Modeling Consortium(IAMC)](hhttps://pyam-iamc.readthedocs.io/en/stable/data.html) formats. 
    - Helps in comparing modelling results from other frameworks.
    - Aiming to use the [IDEA](https://cme-emh.ca/en/idea/) platform to compare results from other models. IDEA requires IAMC format to compare results.
        > [know more about IDEA](https://gitlab.com/sesit/idea/-/wikis/IDEA)

---
# [config.yaml](https://github.com/DeltaE/BC_Combined_Modelling/blob/main/config/config.yaml)

Lets take a look a bit more inside the [config.yaml](https://github.com/DeltaE/BC_Combined_Modelling/blob/main/config/config.yaml): 

- The main 'key' that controls the scenarios is 'clews'. The abstract structure is as follows:
```python
clews:
  SCENARIOS:
    # SCENARIO_NAME: <str>
      # Scenario_axes: <str>
        # TECHID: 
            # capital_cost: float or vector
            # operational_life: int
            # input_fuel: supported FUELS
            # efficiency: float
            # total_annual_min_capacity: float
            # total_annual_max_capacity: float 
            # total_annual_max_capacity_investment : float
```
- __SCENARIO_NAME__: To be replaced by the SCNEARIO_NAME. It is a convention to use 'snake_case' or 'SCREAMING_SNAKE_CASE'  in scenario naming formation.
    > 'snake_case' or 'SCREAMING_SNAKE_CASE' : Words are lower/UPPERCASE and separated by underscores, no spaces.
- __Scenario_axes__: To be replaced by the supported (configured) scenario axes. Currently supports 3 scenario axes set-up e.g. 
  - __Demand__ : We configure _AccumulatedAnnualDemand_ parameter via defining energy demands (PJ) for different fuels that are already defined in the model structure. If new fuel is required to introduced for scenarios, it has to be structured in the model. 
    > The axis name can't be deleted. It has to be an empty dictionary in-case no changes requires from default/baseline setup.
  - __EMISSION__ : We configure attributes of defined _EMISSION_ carriers via _annual_emission_limit_ and/or _emission_penalty_ under this axes.
  - __TECHS__: We configure market indicator attributes of defined _TECHNOLOGIES_ with this axis e.g. 
      - capital_cost: float or vector
        - vector here is an array of floats that represents values for specific year starting from base year.
        - example: capital_cost: [0,0,0,100,200] denotes the technology will be 100 $/MW capital cost if it's build in 4th year and 200 $/MW if built on 5th year, otherwise it will not have any cost.
      - operational_life: int
      - input_fuel: supported FUELS
      - efficiency: float
      - total_annual_min_capacity: float
      - total_annual_max_capacity: float 
      - total_annual_max_capacity_investment : float

Scenario axes set-up example:

We want to set :
- Transportation sectors Hydrogen, Diesel, Jet-fuel and Industrial Sector's Hydrogen and Natural Gas demand. 
- Emission penalty and emission limits for CO2 and 
- Carbon Capture Storage (CCS) and Hydrogen Technology (HDG). 

For a test scenario the axes may look-like this:

| **Demand** | **EMISSION** | **TECHS** |
|------------|--------------|-----------|
| TRAHDG  <br> TRADSL  <br> TRAJFL <br> INDHDG <br> INDNGS | CO2 | CCS01: <br> - capital_cost: High <br> - total_annual_max_capacity:  modeller justifications <br> - operational_life: in Years <br> - total_annual_max_capacity_investment: modeller justifications <br> HDG01: <br> - total_annual_max_capacity: modeller justifications <br> - total_annual_max_capacity_investment: Consider for investments from 2026 |


An __example scenario__ in configuration level with the example scenario axes described above:

```python
clews:
  SCENARIOS:
    Base_CNZ_noCCS:
      Demand:
       TRAHDG:
          accumulated_annual_demand: [0.0, 0.0, 0.0, 0.0, 9.0, 12.9, 16.8, 20.6, 24.8, 28.8, 33.1, 37.3, 41.7, 46.2, 50.8, 55.3, 60.0, 64.6, 6922646.0, 74.0, 78.9, 83.8, 89.0]
        TRADSL:
          accumulated_annual_demand: [97.1, 96.2, 97.7, 94.3, 89.0, 85.7, 81.6, 77.7, 76.3, 73.8, 71.9, 69.9, 68.0, 66.3, 64.6, 62.7, 60.9, 59.0, 57.1, 55.2, 53.5, 51.7, 50.1]
        TRAJFL:
          accumulated_annual_demand: [39.9, 72.3, 80.0, 82.6, 81.2, 80.9, 80.2, 79.2, 78.5, 77.7, 76.8, 75.8, 74.7, 73.8, 72.7, 71.5, 70.1, 68.6, 67.1, 65.5, 63.8, 62.2, 60.5]
        INDHDG:
          accumulated_annual_demand: [0.0, 0.0, 0.0, 0.0, 12.6, 19.9, 25.1, 30.0, 38.2, 47.6, 53.9, 59.8, 67.3, 75.1, 82.3, 89.1, 95.5, 102.0, 108.9, 116.1, 123.5, 131.0, 138.7]
        INDNGS:
          accumulated_annual_demand: [218.4, 229.2, 236.9, 230.2, 239.4, 256.0, 242.1, 228.6, 238.6, 249.8, 242.3, 233.4, 230.6, 227.8, 222.5, 216.0, 208.6, 201.6, 195.3, 189.4]
      EMISSION: 
        CO2:
          annual_emission_limit: [70,70,70,60,60,50]
          emission_penalty: [45, 45, 50, 65, 80, 95, 110, 125, 140, 155, 170]
      TECHS: 
        CCS01:
            capital_cost: 9999 # we can also prove a vector e.g. [xxx xxx ]
            total_annual_max_capacity: 0 #GW
            operational_life: 25
            total_annual_max_capacity_investment: [0]
        HDG01:
          total_annual_max_capacity: 0.2 #GW
          total_annual_max_capacity_investment: [0,0,0,0,0,1] # Represents values for year vectors e.g. 2021,2022,2023,2024,2025,2026
```

Example: If want to set a base scneario with default demand and emission axes but want to set-up technology attributes:

```python
    Base_CNZ:
      Demand: {}
      EMISSION: {}
      TECHS: 
        CCS01:
            capital_cost: 9999 # we can also prove a vector e.g. [xxx xxx ]
            total_annual_max_capacity: 0.2 #GW
            operational_life: 25
            total_annual_max_capacity_investment: [0,0,0,0,0,1]
        HDG01:
          total_annual_max_capacity: 0.2 #GW
          total_annual_max_capacity_investment: [0,0,0,0,0,1]
```