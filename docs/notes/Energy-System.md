This section reviews the data and assumptions used in creating the energy system for the BC Nexus model in the base model (reference scenario). Data within the energy system was divided into the power system portfolio and the demands for other types of fuels (imported and exported energy sources) within the province. In the base model, the limitations are solely the cost of technology and the maximum limit on the unused potential of energy sources for future growth (no policy constraint on carbon emission). The table below summarizes the main information gathered to calibrate the model with the energy system portfolio of BC. Most of the information on this wiki page is borrowed from the paper of the modelling team who developed the based model: "ELECTRIFICATION POLICY IMPACTS ON LAND SYSTEM IN BRITISH COLUMBIA, CANADA," published by Nastaran Arianpoo, Andrew S. Wright, and Taco Niet [[1]](#1)

> **Note that this document serves as a guide for using, recreating, and tracking assumptions and input data in the BC Nexus Model. It provides definitions and values for the base model's input data. The CSV files input data formatted to be readable for the model solver is available in [the Resources folder](https://github.com/DeltaE/BC-CLEWS-Model/tree/main/Resources) under the folder [Input-BCNexus-REF-LND Intensity Ave-N Arianpoo-Nov2022](https://github.com/DeltaE/BC-CLEWS-Model/tree/main/Resources/Input-BCNexus-REF-LND%20Intensity%20Ave-N%20Arianpoo-Nov2022).


| Collected data | Data analysis and assumptions |
|-- | -- |
**Power System**|
Components (each power generation station) | - Location, capacity, nominal annual generation, actual annual generation, operational life span | - Capacity factor<br> - Efficiency<br> - Residual capacity
Cost | - Capital, fixed, and variable costs. <br>    - Generic technology cost info  | - Due to the lack of information, generic cost data   assigned for each technology
Demand | - Hourly production loads from BC hydro and potential hourly load for wind and solar projects at each specific site location | - Availability factors<br>   - Time slices (daily) and year split (seasonal)<br>   - Specified annual demand for each time slice<br>  - Specified demand portfolio within each time slice<br>  - The specified power demand for each sector   (residential, commercial, industrial, transportation)
Other information | - Transmission loss (10%)<br>  - Reserve margin (varies by year)  | - Reference data was allocated
**Rest of the   energy system**
Non-electrical fuels | - Accumulated annual end-use fuel demand<br>    - Domestic fuel productions<br>    - Import/export fuel supplies | - For non-electrical fuels that can be stored, the demand is projected on an annual basis rather than for each time slice
Cost | - Fuel cost and annual forecast to 2050 | - The assumption has been made to project the fuel cost to 2050
Linkages data: energy on land and water systems | - Energy demand in agriculture (e.g., diesel used to run agricultural machinery) and water systems (e.g. water pumping, water treatment facilities, etc.) |

# 1. Residual Capacity
Residual capacity is defined as the capacity left in the operational life of a power plant and in the BC Nexus Model refers to the existing power generation facilities in BC. at the time of releasing the BC Nexus base model, BC has around 150 active power projects, mostly IPP (Independent Power Producer) projects, primarily small to medium-sized run-of-river stations. BC has generated its power energy from hydro, wind, solar, natural gas, and biomass. To simplify the model structure, the power projects were aggregated, when possible, into larger units. The aggregation was based on careful analysis of data. For hydro projects, The five largest generators (over 5% of total provincial hydro capacity) were singled out as they have a significant impact on the power system and are represented individually. The remaining hydro projects were grouped based on region, size, capacity factor, and generation technology. The hydro projects in the province were divided into 8 regions: Peace River, Northern BC, Prince Rupert & Graham Island, Prince George & Jasper, Vancouver Island, Lower Mainland & Pemberton, and Kamloops & Southeast BC. Due to missing data (capacity, lifespan, etc.) for some projects, assumptions were made based on similar projects. As a result, the hydro projects were grouped into 12 larger units in the model. The same approach was taken for natural gas and bioenergy power stations. However, for variable renewable power projects (wind and solar), all projects are represented individually in the model due to their location sensitivity and varying capacity factors. For each project, information such as nominal and actual capacity, availability or capacity factor were collected or calculated based on the available data from various sources. 

>**"ResidualCapacity.csv"** comprise of the residual capacity data used as input. 


# 2. Temporal Representation

In the BC Nexus model, the temporal representation is a user-defined feature that can be adjusted to suit the needs of the inquiry. This feature is particularly significant for variable renewable energy sources such as solar and wind, given the fluctuation in production patterns in various site locations at different times of the year. To reduce the computational complexity in the base model version, a simplified temporal resolution is used, dividing the year into four seasons (Spring, Summer, Fall, and Winter) and two-day splits as day and night. The temporal data structure employed is explained in detail in the "Home" chapter ([Here](https://github.com/DeltaE/BC-CLEWS-Model/wiki#23temporal-resolution)). Note that the modelling year is from 2020 to 2050.

<img src="https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Graphical%20Resources/Load%20Profile.svg" width="1100"> 

Although it looks like blocks due to high density of plots, but it is actually a bit different in representation. To explain the actual vs downscaled resolution of the load profile a **typical day (24hrs) load profile** has been shown (assume it as a zoomed in version of the plot above) below :    

<img src="https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Graphical%20Resources/Load%20Profile_day.svg" width="1000">


> The temporal representation in input file has been given vide **"TIMESLICE.csv"** and **"YearSplit.csv"**.

# 3. Energy Demand Profile of BC in the Base Model

## 3.1. Electricity Demand profile

The table below illustrates the power demand profile corresponding to the temporal structure presented in [Here](https://github.com/DeltaE/BC-CLEWS-Model/wiki#23temporal-resolution), and the hourly electrical load in BC in 2019 and 2018 (Source BC Hydro Historical Transmission Data, GROSS TELEMETERED LOAD, Hourly Data: [Click Here](https://www.bchydro.com/energy-in-bc/operations/transmission/transmission-system/balancing-authority-load-data/historical-transmission-data.html)). This demand profile represents the annual fraction of the total power demand required for each defined time slice.

|**Seasons**          | Spring: <br/>(Mar 20-Jun19) | | Summer:<br/>(Jun 20-Sep 21) || Fall: <br/> (Sep 22-Dec 20)| | Winter: <br/>(Dec 21-Mar19) ||
|  --------------------------------------| ----- | -------| ----  |------ | ------|------ | -----|------  |
|**Time slicing**                            | Day   | Night  | Day   | Night | Day   | Night | Day  | Night  |
|**Ave. Seasonal hrs.**                      | 13.90 | 10.10  | 15.36 | 8.64  | 10.00 | 14.00 | 8.75 | 15.25  |
|**Daylight hours<br/>[(]start (am), end (pm)]**| 6     | 20     | 6     | 21    | 8     | 18    | 8    | 17     |
|**Specified Demand (%)** | 0.15 | 0.08 | 0.16 | 0.07 | 0.12 | 0.13 | 0.13 | 0.16 |

  
> The BC's BC's demand portfolio data data given as input vide "SpecifiedDemandProfile.csv".


The electricity demand projection in residential, commercial, industrial and transportation sectors outlined in [Canada’s Energy Future report](https://www.cer-rec.gc.ca/en/data-analysis/canada-energy-future/archive/2019/), published in 2019 by Canada Energy Regulator, was selected to reflect the future electricity demand portfolio of BC in the base model. In this report, the demand is projected till 2040. To match the modelling period, the demand trends linearly extrapolated to 2050.

> The BC's electricity demand projection data has been given as input datafile "SpecifiedAnnualDemand.csv".

## 3.2. Non-electrical energy demand (import/export)
For non-electrical fuels that can be stored, the demand is projected on an annual basis rather than for each time slice. This means that the demand for non-electrical fuels, such as natural gas or oil, is estimated for the whole year rather than for each individual time period within the year. This includes non-electrical (fuels) annual provincial imports and export. 

> The BC's Non-electrical energy demand data data given as input vide "AccumulatedAnnualDemand.csv".

# 4. Capacity and Availability Factors

* The availability factor (AF) of a power plant refers to the proportion of time it is operational and capable of generating electricity over a specified period. In the model, the AF refers to the availability of non-renewable power generation within a year. All power plants exhibit availability factors, which vary depending on factors such as resources, technology, and intended purpose. Due to the absence of comprehensive data for all power plants in BC, some power plants were grouped together and represented as a single technology box, with the average availability factor being calculated. The table below shows the availability factor used in the base model for each non-renewable power generation unit. AF values stay constant through the years (2020-2050).


* Powerplant aggregation in the spatial region of BC :  
    
<img src="https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Graphical%20Resources/BC%20Nexus%20README.gif"> 

TECHNOLOGY | Availability Factor
:--: | :--:
PWRBIOB01 | 0.77
PWRBIOB02 | 0.67
PWRBIOB03 | 0.43
PWRBIOB04 | 0.62
PWRBIOB05 | 0.39
PWRBIOB06 | 0.39
PWRGEOB01 | 0.87
PWRGEOB02 | 0.87
PWRGEOB03 | 0.87
PWRHYDB01 | 0.55
PWRHYDB02 | 0.56
PWRHYDB03 | 0.41
PWRHYDB04 | 0.39
PWRHYDB05 | 0.4
PWRHYDB06 | 0.31
PWRHYDB07 | 0.47
PWRHYDB08 | 0.49
PWRHYDB09 | 0.45
PWRHYDB10 | 0.39
PWRHYDB11 | 0.5
PWRHYDB12 | 0.3
PWRHYDB13 | 0.3
PWRNGSB01 | 0.87
PWRURNB01 | 0.93

* The Capacity factor (CF) is defined as the proportion of actual energy produced over a given period to the theoretical maximum energy that could have been produced at max. The term CF in the model is used to represent the capacity of renewable energy generators within each defined timeslices. The results of the model are highly sensitive to the capacity factors of renewable energy sources, and as such, it is imperative to utilize accurate information whenever possible. For renewable energy sources that are dependent on weather conditions, such as solar and wind, the project relied on information from the [renewables.ninja](https://www.renewables.ninja/) to get the data for time slices used. 

>The capacity and availability factors data data given as input vide "CapacityFactor.csv" and "AvailabilityFactor.csv" files.

# 5. Costs
In the model, three types of cost information are associated with power generation technologies: **capital costs**, **fixed costs**, and **variable costs**. Due to the limited availability of information, generic cost data was assigned for each technology. The generic cost data was obtained from the "Capital Cost and Performance Characteristic Estimates for Utility Scale Electric Power Generating Technologies" report published by the U.S. Energy Information Administration (EIA) in 2020[[2]][def]

**Assumption**: The cost of technology remains unchanged throughout the entire modelling period.`

> The cost data data given as input vide "CapitalCost.csv", "FixedCost.csv", and "VariableCost.csv".


# 6. Operational Life
Due to the limited availability of information, generic operational lifespan data was assigned for each technology. The generic operational lifespan of technologies data was obtained from the "Capital Cost and Performance Characteristic Estimates for Utility Scale Electric Power Generating Technologies" report published by the U.S. Energy Information Administration (EIA) in 2020 [[Reference](https://www.eia.gov/analysis/studies/powerplants/capitalcost/pdf/capital_cost_AEO2020.pdf)].

**Assumption**: The operational life of aggregated technology units estimated from the average start operation date of aggregated projects.

> The operational life data given as input vide "OperationalLife.csv".


TECHNOLOGY |Operational life
-- | --
PWRBIOB01 | 40
PWRBIOB02 | 40
PWRBIOB03 | 40
PWRBIOB04 | 40
PWRBIOB05 | 40
PWRBIOB06 | 40
PWRGEOB01 | 40
PWRGEOB02 | 40
PWRGEOB03 | 40
PWRHYDB01 | 60
PWRHYDB02 | 60
PWRHYDB03 | 60
PWRHYDB04 | 60
PWRHYDB05 | 60
PWRHYDB06 | 60
PWRHYDB07 | 60
PWRHYDB08 | 60
PWRHYDB09 | 60
PWRHYDB10 | 60
PWRHYDB11 | 60
PWRHYDB12 | 60
PWRHYDB13 | 60
PWRNGSB01 | 22
PWRSOLB01 | 25
PWRURNB01 | 36
PWRWNDB01 | 25
PWRWNDB02 | 25
PWRWNDB03 | 25
PWRWNDB04 | 25
PWRWNDB05 | 25
PWRWNDB06 | 25
PWRWNDB07 | 25
PWRWNDB08 | 25

# 7. Reserve Margin and  Technology tags
Reserve margin refers to the extra available capacity that exceeds the maximum demand during peak periods. It acts as a cushion to ensure the reliability and stability of the power system. The Anticipated Reserve Margin is a metric used to evaluate the adequacy of available resources by comparing the projected capability of these resources to meet forecasted peak demand. Significant fluctuations in either the anticipated resources or forecasted peak demand can significantly impact the calculations of the Planning Reserve Margin [[Reference](https://www.wecc.org/_layouts/15/WopiFrame.aspx?sourcedoc=/Administrative/NERC_LTRA_2020_Errata.pdf&action=default&DefaultItemOpen=1)]. In 2020, the North American Electric Reliability Corporation (NERC) published the Long-Term Reliability Assessment report, which provides the projected reserve margin values for BC from 2021 to 2030. Bear in mind that the reserve margin we used in the base model is quite conservative (~13%), and the actual reserve (projected) margin can be as high as 24% in BC. 

> The reserve margin data given as input vide "ReserveMargin.csv", "ReserveMarginTagFuel.csv", and "ReserveMarginTagTechnology.csv". 


In the files mentioned above, the first file defines the reserve margin values through the years as shown in the table below. The second file defines the fuels, here electricity, that needed reserve margin consideration in optimization analysis by the solver, and the third one tags the energy generation technologies that can serve as a reserve margin provider. Note that the variable renewable energy sources are not baseload energy providers as such are not reliable to use as reserve margin providers. In the base model, geothermal, hydro, bioenergy, natural gas, and nuclear energy technologies are tagged.

YEAR | Reserve Margin Value
-- | --
2020 | 1.13
2021 | 1.138
2022 | 1.123
2023 | 1.138
2024 | 1.141
2025 | 1.141
2026 | 1.14
2027 | 1.139
2028 | 1.123
2029 | 1.137
2030 | 1.135
2031 | 1.135
2032 | 1.135
2033 | 1.135
2034 | 1.135
2035 | 1.135
2036 | 1.135
2037 | 1.135
2038 | 1.135
2039 | 1.135
2040 | 1.135
2041 | 1.134
2042 | 1.134
2043 | 1.134
2044 | 1.134
2045 | 1.134
2046 | 1.134
2047 | 1.134
2048 | 1.134
2049 | 1.134
2050 | 1.134

# 8. Transmission
The base model assumes a single transmission line for the entire BC power system with a constant of about 10% transmission loss over the modelling period, based on information provided on BC Hydro's website as illustrated below for various transmission lines in BC [[Reference:](https://www.bchydro.com/toolbar/about/accountability_reports/2011_gri/f2011_economic/f2011_economic_EU12.html)]

> The definition of transmission loss in the base model refers to the additional power that must be generated to meet 100% of the demand. This value is represented as a percentage and has been set at 1.11, indicating the extent of excess power required. This value defines in the model file explained in the Home chapter [[Link to the model file](https://github.com/DeltaE/BC-CLEWS-Model/wiki#step-two-model)].


Energy loss| Percentage Value estimated by BC Hydro for BC
-- | --
Transmission | %6.28
Distribution | %4-4.20
Total Energy   Losses | %10-10.48

# 9. Technology Activity Ratio

In the model, there are several parameters that measure how efficiently a unit's performance (e.g. technology box such as a coal mine operation, a power plant unit, etc.) is working. These parameters are as below:

* **CapacityToActivityUnit**: is utilized to establish the correlation between the energy production of a unit if it operates at its maximum capacity for one full year. This parameter determines the conversion factor between the capacity unit and the output unit of technology. For example, in the model, the capacity of power technology is defined in GW, while the power generation is in units of PJ. As a result, the Capacity to Activity Unit parameter for power technologies is defined as 31.536 in the model (1GW = 31.536 PJ/year). 

>The CapacityToActivityUnit data given as input vide "CapacityToActivityUnit.csv". 


* **InputActivityRatio**: Gives the rate of input (use) of fuel for technology as a ratio to the rate of activity. The "Efficiency in Electricity Generation" Report by EURELECTRIC in 2003 [[Reference](https://wecanfigurethisout.org/ENERGY/Web_notes/Bigger_Picture/Where_do_we_go_Supporting_Files/Efficiency%20in%20Electricity%20Generation%20-%20EURELECTRIC.pdf)] was used as a reference for calculating the generic efficiency values of the Input Activity Ratio in the absence of proper data for BC's specific technologies. Here is the list of energy conversion efficiency for various power plant technologies extracted from The "Efficiency in Electricity Generation" Report:

>  * Steam turbine fuel-oil power plant: 38% to 44%
>  * Coal:
 > > * Steam turbine coal-fired power plant: 39% to 47%
 > > * Pulverized coal boilers with ultra-critical steam parameters: up to 47%
 > > > * Atmospheric Circulating Fluidized Bed Combustion (CFBC)
 > > > * Pressurized Fluidized Bed Combustion (PFBC): > 40%
 > > > * Coal-fired IGCC: > 43%
>  * Natural Gas:
 > > > * Large gas turbine (MW range): up to 39%
 > > > * Large gas-fired CCGT power plant: up to 58%
>  * Biomass and Biogas:
 > > > * Biomass and biogas: 30-40%
 > > > * Biomass gasification combined cycle power plant: 40%
>  * Nuclear power plant: 33% to 36% [[Second Reference](https://www.world-nuclear.org/information-library/current-and-future-eneration/cooling-power-plants.aspx)]
>  * Geothermal power plant: up to 15% for 190°C
>  * Solar:
 > > > * Parabolic trough: 14% to 18%
 > > > * Power tower: 14% to 19%
 > > > * Dish Stirling: 18% to 23%
 > > > * Photovoltaic cells: up to 15%
>  * Wind turbine: up to 35%
>  * Hydro:
 > > > * Large hydro dam power plant: up to 95%
 > > > * Small hydro dam power plant: up to 90%
 > > > * Tidal power plant: up to 90%

>
The InputActivityRatio data given as input vide "InputActivityRatio.csv". 


* OutputActivityRatio: Output Activity Ratio gives the rate of output of fuel as a ratio to the rate of activity in which technology is operating. The Output Activity Ratio for all power technology is assumed to be 1 in the model.

> The Output Activity Ratio data given as input vide "OutputActivityRatio.csv". 


# 10. Defined Constraints parameters

The following parameters are used to define constraints for the modelling optimization analysis of the energy system. 

## 10.1. Total Annual Max Capacity
It is the upper limit of the capacity level of the sum of all technology investments in each year of the modelling period. In BC, despite having the potential for the development of various renewable energy technologies, available information and data on their technical and commercial viability are limited. No significant advancements or research has been carried out on geothermal or ocean energy sources in BC. In 2018, a report was published by the University of Alberta called "British Columbia Energy Market
Profile" [[Reference](https://www.futureenergysystems.ca/public/download/documents/70220#:~:text=Today%20several%20large%20wind%20projects,MW%20by%2020205%20(CanWEA).)], estimated the geographical potential of renewable energy sources in the region. The information in this report is used to define the upper limit of the capacity level for renewable power technologies in BC. for more information check [1].

> The Total Annual Max Capacity data used as input vide "TotalAnnualMaxCapacity.csv". 


## 10.2. Total Annual Max Capacity Investment
To better represent the untapped potential of new and future technologies, and prevent the model to reinvest in existing facilities to expand the capacity of power generation, a new set of technology units are created in the models to represent future developments. As illustrated below, the Total Annual Max Capacity Investment parameter is used to block the new investment into existing facilities and force the model to invest in new facilities for future developments. Also, as shown this parameter was used to delay investing in geothermal technology till 2025 to portray a more realistic investment projection.

> The Total Annual Max Capacity Investment data given as inputdata vide "TotalAnnualMaxCapacityInvestment.csv". 


## 10.3. Total Annual Min Capacity Investment
This parameter is used to ensure the model invests in under-construction power capacities that are expected to coming one on a certain date. In the base model, a total annual min capacity investment was set for 1.1 GW in one of the hydro technology units (PWRHYDB13). The expected 1.1 GW increase in hydropower capacity in 2025 is due to the completion of the Site C dam project on Peace River. This project is under construction at the moment. 

> The Total Annual Min Capacity Investment data given as input vide "TotalAnnualMinCapacityInvestment.csv". 


# 11. Limitations
The absence of storage technologies in the model is a major limitation of this version.

# About Other Systems of this Model
* [Climate & Water](https://github.com/DeltaE/BC-CLEWS-Model/wiki/Water-and-Climate-System) 
* [Land](https://github.com/DeltaE/BC-CLEWS-Model/wiki/Land-System)

## References
<a id="1">[1]</a> 
"ELECTRIFICATION POLICY IMPACTS ON LAND SYSTEM IN BRITISH COLUMBIA, CANADA," published by Nastaran Arianpoo, Andrew S. Wright, and Taco Niet

<a id="2">[2]</a> 
[EIA 2020](https://www.eia.gov/analysis/studies/powerplants/capitalcost/pdf/capital_cost_AEO2020.pdf).

[def]: #1