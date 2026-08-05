# 1. Project Overview
The model will identify technological pathways to meet BC's energy decarbonization targets through electrification and utilization of alternate energy carriers (e.g. hydrogen) while considering the water, food and land-use implications of expanding the electricity supply in British Columbia (BC), Canada. The BC CLEWS model comprises three major components: water, food, energy (WFE), and their interactions with the BC climate (CO2 emissions). Most of the information on this wiki page is borrowed from the paper of the modelling team who developed the based model. Related publications related to this model are [[1]](#1),[[2]](#2).

<img src="https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Graphical%20Resources/Nexus%20Overview.svg" width="1100"> 

# 2. Model Overview
This section provides general background information on the model's framework, the temporal and spatial resolution, and the technologies and commodities (fuels) used in the structure of the model.

> an upgraded version of this model is under development to incorporate the following features:    
> * automate and streamline the input data supply chain and preparation.
> * automate the temporal resolution scaling with temporal clustering approach.
> * advancing hydropower and storage modelling.
> Updates could be tracked via [BC_Combined_Modelling](https://github.com/DeltaE/BC_Combined_Modelling)

## 2.1 Modelling Framework
The BC Nexus Model is built using the CLEWS (Climate, Land, Energy, Water Systems) framework and platform, which is an extension of the OSeMOSYS (the Open-Source energy MOdelling SYStem) energy modelling system. OSeMOSYS is a bottom-up linear modelling framework designed for long-term energy system cost optimization in specific regions. More information can be found at [CLEWS GitHub page](https://github.com/OSeMOSYS/CLEWs) and [OSeMOSYS page](https://github.com/OSeMOSYS).

## 2.2 Spatial Resolution
Currently, the model spatial resolution is limited to British Columbia (BC)'s geographical borders.

Example: Powerplant aggregation in the spatial region of BC  
    
<img src="https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Graphical%20Resources/BC%20Nexus%20README.gif"> 

## 2.3 Temporal Resolution
"In the BC Nexus model, temporal representation is a user-defined option and can be changed based on inquiry. This is especially important in the case of variable renewable energy (VRE) sources such as solar and wind, where the production at different times of the year and site locations are diverse" [1]. To represent the energy demand and supply, temporal resolution defines by two elements of "time slices" and "seasons" in the model. The demand and supply for other systems, e.g. agriculture and water, are on an annual basis.

In the reference version of the model (BASE Model), for the energy system, "temporal resolutions are simplified to the four seasons per year (Spring, Summer, Fall and Winter) and two day-splits of day and night to reduce computational complexity," as summarized below [[1]](https://emi-ime.ca/wp-content/uploads/2021/04/EMI-2020-Arianpoo_report_BC-CLEWs.pdf). 

|Seasons          | Spring<br />(Mar 20-Jun19)| Summer<br />(Jun 20-Sep 21)| Fall<br />(Sep 22-Dec 20)| Winter<br />(Dec 21-Mar 19)|
|-----------------|----------------------|-----------------------|---------------------|----------------------|
|**Seasonal days**| 93.00                | 93.00                 | 90.00               | 89.00                |

To better capture time-sensitive parameters such daily fluctuation of renewable energy sources, each season presents as a single 24-hour day in the model, as shown below. Note that the information below is based on BC's specification in the base model and can be revised by a user based on their specific inquiries and assumptions:


|Time slicing                            | Day   | Night  | Day   | Night | Day   | Night | Day  | Night  |
|  --------------------------------------| ----- | -------| ----  |------ | ------|------ | -----|------  |
|Ave. Seasonal hrs.                      | 13.90 | 10.10  | 15.36 | 8.64  | 10.00 | 14.00 | 8.75 | 15.25  |
|Daylight hours <br />start (a.m.), end (p.m.)| 6     | 20     | 6     | 21    | 8     | 18    | 8    | 17     |


<img src="https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Graphical%20Resources/Load%20Profile.svg" width="900"> 

Although it looks like blocks due to high-density of datapoints in plots, but it is actually a bit different in representation. To explain the actual vs downscaled resolution of the load profile a **typical day (24hrs) load profile** has been shown (assume it as a zoomed in version of the plot above)  below :      

<img src="https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Graphical%20Resources/Load%20Profile_day.svg" width="750">  

__VRE Site Timeslice__:

<img src="https://github.com/DeltaE/BC-CLEWS-Model/blob/home_test/Graphical%20Resources/solar_%20(1).png" width="90%">  

<img src="https://github.com/DeltaE/BC-CLEWS-Model/blob/home_test/Graphical%20Resources/wind.png" width="90%">  

## 2.4 Naming Conventions
The following abbreviation and naming conventions are used to represent the commodities (e.g. fuels) and technologies in the model.

| Abbreviation/<br/>naming conventions| Description|
|-- | --|
IND | 'Industry',
RES | 'Residential',
COM | 'Commercial',
AGR | 'Agricultural',
TRA | 'Transport',
OTH | 'Other',
BIO | 'Biomass',
COA | 'Coal',
CRU | 'Crude oil',
DSL | 'Diesel',
ELC| 'Electricity'
ELC001 | 'Electricity from power plants',
ELC002 | 'Electricity from transmission',
ELCB01 | 'Electricity from power plants in   region B',
ELCB02 | 'Electricity from transmission in   region B',
GSL | 'Gasoline',
HFO | 'Heavy fuel oil',
NGS | 'Natural gas',
KER | 'Kerosene',
LPG | 'Liquefied petroleum gas',
OHC | 'Other hydrocarbons',
GEO | 'Geothermal',
HYD | 'Hydropower',
SOL | 'Solar',
WND | 'Wind',
CHC | 'Charcoal',
PCK | 'Petroleum coke',
JFL | 'Jet fuel',
URN | 'Uranium',
ALF | 'Alfalfa',
WHE | 'Wheat',
RAP | 'Rapeseed',
OAT | 'Oat',
BRL | 'Barley',
PEA | 'Dry pea',
MAI | 'Maize',
RYE | 'Rye',
PWT | 'White potato'
RYE | Rye'
PWT | 'White potato'
DEM| 'Demand'
PWR|'Power plant'
LND|'Land'
GWT|'Groundwater'
SUR|'Surface water'
IMP|'Import'
EXP|'Export'
MIN|'Represent non-renewable <br/>resource mining technologies (e.g. coal, uranium)'
RNW|'Represent renewable <br/>resource mining technologies (e.g. solar, water)'
RPP|'Refined Petroleum Products' 

## 2.5 Commodities (Fuels)
Any input element (such as fuels, water, and land) is going to be consumed by technology or if they feed a final demand. Also, demands for energy services are defined as fuels; e.g., a heating demand would be defined as a fuel. The list of commodities included in the base model is as follows and also can be located in the [Resources](https://github.com/DeltaE/BC-CLEWS-Model/tree/main/Resources) folder under the file name **FUEL.csv**:

Commodity (Fuel)|Description
-- | --
AGRDSL | DSL   input in AGR
AGRELCB02 | ELC input in AGR
AGRNGS | NGS input in AGR
AGRWATBC1 | Agricultural water for irrigation.
BIO | Biomass
COA | Coal
COMBIO | BIO input in COM
COMELCB02 | ELC input in COM
COMKER | KER input in COM
COMNGS | NGS input in COM
CRPALF | Crop ALF
CRPBRL | Crop BRL
CRPMAI | Crop MAI
CRPOAT | Crop OAT
CRPOTH | Crop OTH
CRPPEA | Crop PEA
CRPPTW | Crop PTW
CRPRAP | Crop RAP
CRPRYE | Crop RYE
CRPWHE | Crop WHE
CRU | Cruel oil
DSL | Diesel
ELCB01 | Electricity from power plants
ELCB02 | Electricity from the transmission
GEO | Geothermal
GSL | Gasoline
HFO | Heavy fuel oil
HYD | Hydro
INDBIO | BIO input in IND
INDDSL | DSL input In IND
INDELCB02 | ELC input in IND
INDNGS | NGS input in IND
JFL | Jet Fuel
KER | Kerosene
LALFHIBC1 | Land resource commodity for crop combo ALF Irrigation
LALFHRBC1 | Land resource commodity for crop combo ALF Rain-fed
LALFIIBC1 | Land resource commodity for crop combo ALF Irrigation
LALFIRBC1 | Land resource commodity for crop combo ALF Rain-fed
LALFLRBC1 | Land resource commodity for crop combo ALF Rain-fed
LBARBC1 | Barren and sparsely vegetated land commodity in BC
LBC1 | Land resource in BC1.
LBLTBC1 | Built-up land commodity in BC1.
LBRLHIBC1 | Land resource commodity for crop combo BRL Irrigation
LBRLHRBC1 | Land resource commodity for crop combo BRL Rain-fed
LBRLIIBC1 | Land resource commodity for crop combo BRL Irrigation
LBRLIRBC1 | Land resource commodity for crop combo BRL Rain-fed
LBRLLRBC1 | Land resource commodity for crop combo BRL Rain-fed
LFORBC1 | Forest land commodity in BC1.
LGRSBC1 | Grassland & woodland commodity in BC1.
LMAIHIBC1 | Land resource commodity for crop combo MAI Irrigation
LMAIHRBC1 | Land resource commodity for crop combo MAI Rain-fed
LMAIIIBC1 | Land resource commodity for crop combo MAI Irrigation
LMAIIRBC1 | Land resource commodity for crop combo MAI Rain-fed
LMAILRBC1 | Land resource commodity for crop combo MAI Rain-fed
LND4PWR | Land density used for power generation based on technology
LOATHIBC1 | Land resource commodity for crop combo OAT Irrigation
LOATHRBC1 | Land resource commodity for crop combo OAT Rain-fed
LOATIIBC1 | Land resource commodity for crop combo OAT Irrigation
LOATIRBC1 | Land resource commodity for crop combo OAT Rain-fed
LOATLRBC1 | Land resource commodity for crop combo OAT Rain-fed
LOTHBC1O | the agricultural land commodity in BC1.
LOTHHIBC1 | Land resource commodity for crop combo OTH Irrigation
LOTHHRBC1 | Land resource commodity for crop combo OTH Rain-fed
LOTHIIBC1 | Land resource commodity for crop combo OTH Irrigation
LOTHIRBC1 | Land resource commodity for crop combo OTH Rain-fed
LOTHLRBC1 | Land resource commodity for crop combo OTH Rain-fed
LPEAHIBC1 | Land resource commodity for crop combo PEA Irrigation
LPEAHRBC1 | Land resource commodity for crop combo PEA Rain-fed
LPEAIIBC1 | Land resource commodity for crop combo PEA Irrigation
LPEAIRBC1 | Land resource commodity for crop combo PEA Rain-fed
LPEALRBC1 | Land resource commodity for crop combo PEA Rain-fed
LPTWHIBC1 | Land resource commodity for crop combo PTW Irrigation
LPTWHRBC1 | Land resource commodity for crop combo PTW Rain-fed
LPTWIIBC1 | Land resource commodity for crop combo PTW Irrigation
LPTWIRBC1 | Land resource commodity for crop combo PTW Rain-fed
LPTWLRBC1 | Land resource commodity for crop combo PTW Rain-fed
LRAPHIBC1 | Land resource commodity for crop combo RAP Irrigation
LRAPHRBC1 | Land resource commodity for crop combo RAP Rain-fed
LRAPIIBC1 | Land resource commodity for crop combo RAP Irrigation
LRAPIRBC1 | Land resource commodity for crop combo RAP Rain-fed
LRAPLRBC1 | Land resource commodity for crop combo RAP Rain-fed
LRYEHIBC1 | Land resource commodity for crop combo RYE Irrigation
LRYEHRBC1 | Land resource commodity for crop combo RYE Rain-fed
LRYEIIBC1 | Land resource commodity for crop combo RYE Irrigation
LRYEIRBC1 | Land resource commodity for crop combo RYE Rain-fed
LRYELRBC1 | Land resource commodity for crop combo RYE Rain-fed
LWATBC1 | Water bodies commodity in BC1.
LWHEHIBC1 | Land resource commodity for crop combo WHE Irrigation
LWHEHRBC1 | Land resource commodity for crop combo WHE Rain-fed
LWHEIIBC1 | Land resource commodity for crop combo WHE Irrigation
LWHEIRBC1 | Land resource commodity for crop combo WHE Rain-fed
LWHELRBC1 | Land resource commodity for crop combo WHE Rain-fed
NGS | Natural gas
PUBWATBC1 | Water lost to evapotranspiration.
PWRBIO | BIO input to PWR
PWRGEO | GEO input to PWR
PWRHYD | HYD input to PWR
PWRNGS | NGS input to PWR
PWRSOL | SOL input to PWR
PWRURN | URN input to PWR
PWRWATBC1 | WAT input to PWR
PWRWND | WND input to PWR
RESBIO | BIO
RESELCB02 | ELC input in RES
RESKER | KER input in RES
RESNGS | NGS input in RES
SOL | Solar
TRABIO | BIO input in the Transportation sector
TRADSL | DSL input in the Transportation sector
TRAELCB02 | ELC input in the Transportation sector
TRAGSL | GSL input in the Transportation sector
TRAHFO | HFO input in the Transportation sector
TRAJFL | JFL input in the Transportation sector
TRALPG | LPG input in the Transportation sector
TRANGS | NGS input in the Transportation sector
URN | Uranium
WND | Wind
WTREVTBC1 | Water lost to evapotranspiration.
WTRGRCBC1 | Water lost to evapotranspiration.
WTRPRCBC1 | Agricultural water for irrigation.
WTRSURBC1 | Agricultural water for irrigation.

## 2.6 Technologies
In CLEWS, technology includes any element that converts or consumes an input commodity (e.g. fuels or land) into another form (output), such as electricity or crops.

```
The list of technologies defined in the model can be located in the "Resources" folder under the file name "TECHNOLOGY.csv".
```

|Name (Abbreviation)|Description|
|----|----------|
|DEMAGRDSL|Demand technology for DSL in Agriculture|
|DEMAGRELCB02|Demand technology for electricity in Agriculture|
|DEMAGRGWTBC1|Agricultural groundwater supply.|
|DEMAGRNGS|Demand technology for NGS in Agriculture|
|DEMAGRSURBC1|Agricultural groundwater supply|
|DEMCOMBIO|Demand technology for BIO in the Commercial sector|
|DEMCOMELCB02|Demand technology for electricity in the Commercial sector|
|DEMCOMKER|Demand technology for KER in the Commercial sector|
|DEMCOMNGS|Demand technology for NGS in the Commercial sector|
|DEMINDBIO|Demand technology for BIO in the industry sector|
|DEMINDDSL|Demand technology for DSL in the industry sector|
|DEMINDELCB02|Demand technology for electricity in the industry sector|
|DEMINDNGS|Demand technology for NGS in the industry sector|
|DEMPUBGWTBC1|Public demand for groundwater|
|DEMPUBSURBC1|Public demand for surface water|
|DEMPWRBIO|Demand technology for BIO in the power sector|
|DEMPWRGEO|Demand technology for GEO in the power sector|
|DEMPWRHYD|Demand technology for HYD in the power sector|
|DEMPWRNGS|Demand technology for NGS in the power sector|
|DEMPWRSOL|Demand technology for SOL in the power sector|
|DEMPWRSURBC1|Demand technology for surface water in the power sector|
|DEMPWRURN|Demand technology for URN in the power sector|
|DEMPWRWND|Demand technology for WND in the power sector|
|DEMRESBIO|Demand technology for BIO in the Residential sector|
|DEMRESELCB02|Demand technology for electricity in the Residential sector|
|DEMRESKER|Demand technology for KER in the Residential sector|
|DEMRESNGS|Demand technology for NGS in the Residential sector|
|DEMTRABIO|Demand technology for BIO in the transportation sector|
|DEMTRADSL|Demand technology for DSL in the transportation sector|
|DEMTRAELCB02|Demand technology for electricity in the transportation sector|
|DEMTRAGSL|Demand technology for GSL in the transportation sector|
|DEMTRAHFO|Demand technology for HFO in the transportation sector|
|DEMTRAJFL|Demand technology for JFL in the transportation sector|
|DEMTRALPG|Demand technology for LPG in the transportation sector|
|DEMTRANGS|Demand technology for NGS in the transportation sector|
|EXPBIO|Export BIO|
|EXPCOA|Export COA|
|EXPCRU|Export CRU|
|EXPNGS|Export NGS|
|IMPCOA|Import COA|
|IMPCRU|Import CRU|
|IMPDSL|Import DSL|
|IMPGSL|Import GSL|
|IMPHFO|Import HFO|
|IMPJFL|Import JFL|
|IMPKER|Import KER|
|IMPLPG|Import LPG|
|LNDAGRBC1C01|Land resource in BC1.|
|LNDAGRBC1C02|Land resource in BC1.|
|LNDAGRBC1C03|Land resource in BC1.|
|LNDAGRBC1C04|Land resource in BC1.|
|LNDAGRBC1C05|Land resource in BC1.|
|LNDAGRBC1C06|Land resource in BC1.|
|LNDAGRBC1C07|Land resource in BC1.|
|LNDALFHIBC1|Land resource technology for crop combo ALF Irrigation|
|LNDALFHRBC1|Land resource technology for crop combo ALF Rain-fed|
|LNDALFIIBC1|Land resource technology for crop combo ALF Irrigation|
|LNDALFIRBC1|Land resource technology for crop combo ALF Rain-fed|
|LNDALFLRBC1|Land resource technology for crop combo ALF Rain-fed|
|LNDBARBC1|Barren and sparsely vegetated land technology in BC|
|LNDBLTBC1|Built-up land technology in BC1.|
|LNDBRLHIBC1|Land resource technology for crop combo BRL Irrigation|
|LNDBRLHRBC1|Land resource technology for crop combo BRL Rain-fed|
|LNDBRLIIBC1|Land resource technology for crop combo BRL Irrigation|
|LNDBRLIRBC1|Land resource technology for crop combo BRL Rain-fed|
|LNDBRLLRBC1|Land resource technology for crop combo BRL Rain-fed|
|LNDFORBC1|Forest land technology in BC1.|
|LNDGRSBC1|Grassland & woodland technology in BC1.|
|LNDMAIHIBC1|Land resource technology for crop combo MAI Irrigation|
|LNDMAIHRBC1|Land resource technology for crop combo MAI Rain-fed|
|LNDMAIIIBC1|Land resource technology for crop combo MAI Irrigation|
|LNDMAIIRBC1|Land resource technology for crop combo MAI Rain-fed|
|LNDMAILRBC1|Land resource technology for crop combo MAI Rain-fed|
|LNDOATHIBC1|Land resource technology for crop combo OAT Irrigation|
|LNDOATHRBC1|Land resource technology for crop combo OAT Rain-fed|
|LNDOATIIBC1|Land resource technology for crop combo OAT Irrigation|
|LNDOATIRBC1|Land resource technology for crop combo OAT Rain-fed|
|LNDOATLRBC1|Land resource technology for crop combo OAT Rain-fed|
|LNDOTHBC1O|agricultural land technology in BC1.|
|LNDOTHHIBC1|Land resource technology for crop combo OTH Irrigation|
|LNDOTHHRBC1|Land resource technology for crop combo OTH Rain-fed|
|LNDOTHIIBC1|Land resource technology for crop combo OTH Irrigation|
|LNDOTHIRBC1|Land resource technology for crop combo OTH Rain-fed|
|LNDOTHLRBC1|Land resource technology for crop combo OTH Rain-fed|
|LNDPEAHIBC1|Land resource technology for crop combo PEA Irrigation|
|LNDPEAHRBC1|Land resource technology for crop combo PEA Rain-fed|
|LNDPEAIIBC1|Land resource technology for crop combo PEA Irrigation|
|LNDPEAIRBC1|Land resource technology for crop combo PEA Rain-fed|
|LNDPEALRBC1|Land resource technology for crop combo PEA Rain-fed|
|LNDPTWHIBC1|Land resource technology for crop combo PTW Irrigation|
|LNDPTWHRBC1|Land resource technology for crop combo PTW Rain-fed|
|LNDPTWIIBC1|Land resource technology for crop combo PTW Irrigation|
|LNDPTWIRBC1|Land resource technology for crop combo PTW Rain-fed|
|LNDPTWLRBC1|Land resource technology for crop combo PTW Rain-fed|
|LNDRAPHIBC1|Land resource technology for crop combo RAP Irrigation|
|LNDRAPHRBC1|Land resource technology for crop combo RAP Rain-fed|
|LNDRAPIIBC1|Land resource technology for crop combo RAP Irrigation|
|LNDRAPIRBC1|Land resource technology for crop combo RAP Rain-fed|
|LNDRAPLRBC1|Land resource technology for crop combo RAP Rain-fed|
|LNDRYEHIBC1|Land resource technology for crop combo RYE Irrigation|
|LNDRYEHRBC1|Land resource technology for crop combo RYE Rain-fed|
|LNDRYEIIBC1|Land resource technology for crop combo RYE Irrigation|
|LNDRYEIRBC1|Land resource technology for crop combo RYE Rain-fed|
|LNDRYELRBC1|Land resource technology for crop combo RYE Rain-fed|
|LNDWATBC1|Water bodies technology in BC1.|
|LNDWHEHIBC1|Land resource technology for crop combo WHE Irrigation|
|LNDWHEHRBC1|Land resource technology for crop combo WHE Rain-fed|
|LNDWHEIIBC1|Land resource technology for crop combo WHE Irrigation|
|LNDWHEIRBC1|Land resource technology for crop combo WHE Rain-fed|
|LNDWHELRBC1|Land resource technology for crop combo WHE Rain-fed|
|MINCOA|Mining supply COA|
|MINCRU|Mining supply CRU|
|MINLNDBC1|Land supply in BC|
|MINNGS|Mining supply NGS|
|MINPRCBC1|Agricultural groundwater supply|
|MINURN|Mining supply URN|
|PWRBIOB01|Bio plant on B grid, PR Region (49 MW).|
|PWRBIOB02|Bio plant on B grid, PG-J Region (184 MW).|
|PWRBIOB03|Bio plant on B grid, VI Region (55 MW).|
|PWRBIOB04|Bio plant on B grid, K-SE Region (270 MW).|
|PWRBIOB05|Bio plant on B grid, LM Region (160 MW).|
|PWRBIOB06|Bio plant on B grid for future expansions, (? MW).|
|PWRGEOB01|Geothermal plant (Steam technology) on B grid, (? M)|
|PWRGEOB02|Geothermal plant (Steam technology) on B grid, (? M)|
|PWRGEOB03|Geothermal plant (Steam technology) on B grid, (? M)|
|PWRHYDB01|Large hydro plant on B grid, PR Region (2730 MW).|
|PWRHYDB02|Meduim-size hydro plant on B grid, PR Region (694)|
|PWRHYDB03|Aggregated hydro plants on B grid, N Region (312 M)|
|PWRHYDB04|Large hydro plant on B grid, PR-G Region (960 MW)|
|PWRHYDB05|Aggregated hydro plants on B grid, PR_G Region (58|
|PWRHYDB06|Large hydro plant on B grid, PG-J Region (2746 MW)|
|PWRHYDB07|Aggregated hydro plants on B grid, PG-J Region (36|
|PWRHYDB08|Aggregated hydro plants on B grid, VI Region (595.5|
|PWRHYDB09|Aggregated hydro plants on B grid, LM Region (2363|
|PWRHYDB10|Large hydro plant on B grid, K-SE Region (2480 MW)|
|PWRHYDB11|Large hydro plant on B grid, K-SE Region (805 MW)|
|PWRHYDB12|Aggregated hydro plants on B grid, K-SE Region (27|
|PWRHYDB13|Hydro plants on B grid for future expansions, (? MW)|
|PWRNGSB01|Aggregated Natural gas power stations on grid B.|
|PWRSOLB01|Solar plant on B grid, K-Se Region (1 MW).|
|PWRTRNB01|Power transmission grid B|
|PWRURNB01|Nuclear plant (OT technology) on B grid, (? MW).|
|PWRWNDB01|wind plant on B grid, PR Region (144 MW).|
|PWRWNDB02|wind plant on B grid, PR Region (102 MW).|
|PWRWNDB03|wind plant on B grid, PR Region (142 MW).|
|PWRWNDB04|wind plant on B grid, PR Region (180 MW).|
|PWRWNDB05|wind plant on B grid, PR Region (15 MW).|
|PWRWNDB06|wind plant on B grid, VI Region (99 MW).|
|PWRWNDB07|wind plant on B grid, K-SE Region (15 MW).|
|PWRWNDB08|wind plant on B grid, K-SE Region (15 MW).|
|PWRWNDB09|Wind plant on B grid for future expansions, (? MW).|
|PWRWNDB10|Wind plant on B grid for future expansions, (? MW).|
|PWRWNDB11|Wind plant on B grid for future expansions, (? MW).|

## 2.7 Units
The following table summarizes the unit values used to specify each element in the model:

Parameter | Units in Model
-- | --
energy(demand, use, and production)| Petajoules(PJ)
Residual capacity (existing capacity)| Gigawatts (GW)
Capital costs| '$/Kilowatt(kW)  
Fixed costs|  '$/Kilowatt(kW)  per year 
Variable costs| '$/Gigajoules(GJ) 
Availability factor| %
Capacity factor| %
Capacity to activity Unit| $PJ\over(PJ/yr)$
Emissions| tons
Emission activity ratio| kg/GJ   = tons/PJ
Emission penalty| '$/kg = million $/tons
Land| 1000 square kilometres
Water| billion cubic meter
Land-use intensity| (1000 square kilometre)/PJ 
Reserve margin| %


# 2.8 Mode of Operation

The modes of operation refer to the different ways a technology can operate, determined by the mix of input fuels it can use and output products it can provide. For instance, a CHP power plant may switch from generating heat to generating electricity or both under different modes of operation.

>The mode of operation has been defined vide the input datafile "[MODE_OF_OPERATION.csv](https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Resources/Input-BCNexus-REF-LND%20Intensity%20Ave-N%20Arianpoo-Nov2022/datapackage/data/MODE_OF_OPERATION.csv)".


|Mode of Operation| Description|
-- | --
1 | ALFHI <br />and technology activities in the energy sector
2 | ALFII
3 | ALFHR
4 | ALFIR
5 | ALFLR
6 | BARHI
7 | BARII
8 | BARHR
9 | BARIR
10 | BARLR
11 | MAIHI
12 | MAIII
13 | MAIHR
14 | MAIIR
15 | MAILR
16 | OATHI
17 | OATII
18 | OATHR
19 | OATIR
20 | OATLR
21 | OTHHI
22 | OTHII
23 | OTHHR
24 | OTHIR
25 | OTHLR
26 | PEAHI
27 | PEAII
28 | PEAHR
29 | PEAIR
30 | PEALR
31 | PTWHI
32 | PTWII
33 | PTWHR
34 | PTWIR
35 | PTWLR
36 | RAPHI
37 | RAPII
38 | RAPHR
39 | RAPIR
40 | RAPLR
41 | RYEHI
42 | RYEII
43 | RYEHR
44 | RYEIR
45 | RYELR
46 | WHEHI
47 | WHEII
48 | WHEHR
49 | WHEIR
50 | WHELR
51 | Barren and sparsely vegetated land
52 | Forest land
53 | Grassland & woodland
54 | Built-up land
55 | Water bodies
56 | Other agricultural lands

Note for Abbreviation in the agriculture sector:  
* __HI__ – High Irrigation 
* __HR__ – High Rainfall
* __II__ – Intermediate Irrigation
* __IR__ - Intermediate Rainfall
* __LR__ - Low Rainfall

# Model Structure
Model structure explained [here](https://github.com/DeltaE/BC-CLEWS-Model/wiki/Model-Structure).  

![Model Shell](https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Graphical%20Resources/Model%20Shell.svg)

# How to Run the Model
**Step-by-Step guideline** [here](https://github.com/DeltaE/BC-CLEWS-Model/wiki/How-to-Run-the-Model)   

![BC Nexus Workflow](https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Graphical%20Resources/BC%20Nexus%20Workflow-Inouts2BCNexus.drawio.svg)


* **Next recommended Read** > 
* Systems - [Climate & Water](https://github.com/DeltaE/BC-CLEWS-Model/wiki/Water-and-Climate-System) | [Land](https://github.com/DeltaE/BC-CLEWS-Model/wiki/Land-System) | [Energy](https://github.com/DeltaE/BC-CLEWS-Model/wiki/Energy-System)
* [Model Structure](https://github.com/DeltaE/BC-CLEWS-Model/wiki/Model-Structure) | [Modell Shell Building](https://github.com/DeltaE/BC-CLEWS-Model/tree/main/Create%20the%20Input%20Datafiles)

# References

<a id="1">[1]</a>
*[Electrification Policy Impacts on Land System in British Columbia, Canada](https://doi.org/10.1016/j.rset.2024.100080)*; Nastaran Arianpoo, Md Eliasinul Islam, Andrew S. Wright, and Taco Niet, Aug 2024

<a id="2">[2]</a> 
*[ELECTRIFICATION POLICY IMPACTS ON LAND SYSTEM IN BRITISH COLUMBIA, CANADA](https://emi-ime.ca/wp-content/uploads/2021/04/EMI-2020-Arianpoo_report_BC-CLEWs.pdf)*; Nastaran Arianpoo, Andrew S. Wright, and Taco Niet, March 2021



<!--EndFragment-->
</body>

</html>