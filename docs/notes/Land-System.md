The BC Nexus Model's land-use representation was built based on two main categories of data: the availability and allocation of land and the current utilization of land to fulfill food and energy needs. Most of the information on this wiki page is borrowed from the paper of the modelling team who developed the based model [[1]](#1).

![Land Clustering Workflow](https://github.com/DeltaE/BC-CLEWS-Model/blob/main/Graphical%20Resources/Land%20Clustering%20Workflow.svg)

The table below summarizes the main data used to calibrate the land system in the base version of the BC Nexus Model [[1]](#1).

| Description |Collected data | Data analysis and assumptions |
|-------------|---------------|-------------------------------|
|Type of land available in BC |- Sizes of agriculture, forests, barren, water body,   and built-up lands in BC. |  
|Agriculture | - Type of crops in BC per hectares<br> Annual demand for primary crops grown in BC <br>- Clustered   data for crop yield (Unit: t/ha): <br> > crop-specific   agro-climatic assessment  <br> >  soil/terrain   limitations   <br> >  Water   use (rain-fed vs irrigated)  <br> > Agricultural   intensity (low, intermediate, high input level)| - Future growth in land use for built-up and   agricultural land based on population growth and historical trends <br>  -     Choosing ten crops that cover more than 90% of   agricultural lands for clustering and analysis of future growth <br>  -     The majority of the data was collected using the GAEZ   model (Global Agro-Ecological Zoning) [[Ref.](https://pure.iiasa.ac.at/id/eprint/13290/)]
Linkage’s data:   Land-use on energy and water systems | - Land needed for biofuel production<br> - The land-use intensity of the power generation   technologies <br> - A unit of water is required to grow a unit of each main   crop type in BC | -  A sensitivity analysis scenario was conducted to   explore the impact of power technology choices on land transformation

> * **Note**: This document serves as a guide for using, recreating, and tracking assumptions and input data in the BC Nexus Model. It provides definitions and values for the base model's input data. The CSV files input data formatted to be readable for the model solver is available in [Resources ](https://github.com/DeltaE/BC-CLEWS-Model/tree/main/Resources) > [Input-BCNexus-REF-LND Intensity Ave-N Arianpoo-Nov2022](https://github.com/DeltaE/BC-CLEWS-Model/tree/main/Resources/Input-BCNexus-REF-LND%20Intensity%20Ave-N%20Arianpoo-Nov2022) directory.<br/> 
> * Raw data collected from various sources to create the input files for modelling can be located in [Resources](https://github.com/DeltaE/BC-CLEWS-Model/tree/main/Resources) directory.

# 1. Clustering
* To simplify the agriculture system analysis, the BC Nexus Model uses an approach in which groups lands with similar agricultural suitability into clusters using the GAEZ (Global Agro-Ecological Zoning) model [[Ref.](https://pure.iiasa.ac.at/id/eprint/13290/)]. 
* This model clusters data based on general agro-climatic factors, crop-specific conditions, and soil/terrain limitations. The clustering method used by the GAEZ model is called **agglomerative hierarchical clustering** and it groups lands with similar yield potential.
* The base model version comprises of a total of **seven clustered zones**, which are defined for BC based on similar achievable crop yields due to irrigation and intensity similarities. 
  - Each cluster indicates the area in which there is a similar possible crop yield due to similar irrigation and intensity combinations. 
  - **Nine main crops** that make up 90% of the province's production (*alfalfa, barley, maize, oat, pea, potato, rapeseed, rye, and wheat*) were identified and the rest were grouped under "*other*". For more information check "[[1](#1)]. 

> The clustering data, from the GAEZ model, used as input can be located in the "Raw Material Resources" under the Folder named "Land" and then under the folder name "main-clustering-Canada". Abbreviations and naming conventions, [here](https://github.com/DeltaE/BC-CLEWS-Model/wiki#24-naming-conventions).

# 2. Crop Demand 
Data accessibility is one of the main challenges of including BC's agriculture sector in the model especially the future growth and irrigation water demand for different crop types. Historical data was used to project crop production growth. However, due to significant variations in the dataset, extrapolating growth from the last 5-10 vide a linear method has been used to predict slow growth for most crops, which aligns with the low estimated **population growth rate of 1.1%** in BC [[Ref.]](https://www2.gov.bc.ca/gov/content/data/statistics/people-population-community/population/population-projections).

> * The crop demand trajectory data calculated as been given as input vide "AccumulatedAnnualDemand.csv"file.
> * The historical crop data used as input to estimate future growth in the base model can be located in the "Raw Material Resources" folder under the Folder name "Land" and then under the folder name "Basic Land data".

# 3. Land-use Intensity
Land-use intensity metric is a measure of the amount of land needed to generate one unit of energy from a specific technology over its lifetime. It is calculated by dividing the direct footprint area of a technology used for power generation by the yearly production of the technology and the asset lifetime (expressed in standard units such as m<Sup>2</Sup> per MWh). The study by Lovering et al. in 2021 [Paper named: Land-use intensity of electricity production and tomorrow’s energy landscape [[Ref.](https://www.researchgate.net/publication/350358598_Land-use_intensity_of_electricity_production_and_tomorrow%27s_energy_landscape?channel=doi&linkId=605bc60c458515e8346c6ff7&showFulltext=true)] used this method to calculate the land-use intensity of various power generation technologies, and their findings and the research conducted by UN & IRENA [Paper called ENERGY AND LAND USE - GLOBAL LAND OUTLOOK WORKING PAPER [[Ref.](https://www.researchgate.net/publication/319715882_ENERGY_AND_LAND_USE_-_GLOBAL_LAND_OUTLOOK_WORKING_PAPER)] was used in a sensitivity analysis of the impact of electrification policies in the base model version of the BC Nexus Model.

|Type |Minimum<br/>(Km<Sup>2</Sup>/PJ) | Average<br/>(Km<Sup>2</Sup>/PJ) | Maximum<br/>(Km<Sup>2</Sup>/PJ)|
|--|--|--|--|
Nuclear | 0.01 | 0.03 | 0.04
Geothermal | 0.05 | 0.54 | 0.69
Wind | 0.23 | 0.38 | 0.56
biomass | 117 | 293 | 447
Natural gas | 0.06 | 0.60 | 1.28
Hydroelectric<br/>(single purpose dams) | 0.28 | 21.8 | 40.8
Coal | 0.17 | 0.78 | 6.24
Solar PV | 2.78 | 4.35 | 6.55


# 4. Operational Life
Due to the limited availability of information, the average generic ***operational lifespan of 15 years*** was assigned to all farmlands.

>The operational life data used as input vide "***OperationalLife.csv***" file.

# 5. Land Allocation in BC (Current portfolio)

## 5.1. Total Land area: 
adding total land available in BC using "Total Technology Annual Activity Upper Limit":
* BC Total land area = 925,186 sq. km 
* Note unit of land = 1000 sq. km
* BC = 925 units of land

## 5.2. Other land areas
GAEZ provides the basic current land allocation areas as part of the clustering process including the data for build-up land, waterbody, forest area, Barren and sparsely vegetated land, Forest land, Grassland & woodland, and agricultural lands. 

>The land allocation areas data used as input vide "***ResidualCapacity.csv***" file


# About Other Systems of this Model
* [Climate & Water](https://github.com/DeltaE/BC-CLEWS-Model/wiki/Water-and-Climate-System) 
* [Energy](https://github.com/DeltaE/BC-CLEWS-Model/wiki/Energy-System)

# References
<a id="1">[1]</a> 
"[ELECTRIFICATION POLICY IMPACTS ON LAND SYSTEM IN BRITISH COLUMBIA, CANADA](https://emi-ime.ca/wp-content/uploads/2021/04/EMI-2020-Arianpoo_report_BC-CLEWs.pdf)," published by Nastaran Arianpoo, Andrew S. Wright, and Taco Niet