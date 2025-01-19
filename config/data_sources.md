## GADM

- **Data**: Global Administrative Regions (GADM)
- **Supply Chain Mode**: Automated via python package "pygadm"
- **Source**: [GADM Download](https://gadm.org/download_country.html)
- **Description**: Regional boundaries of the Province.
- **Instruction**: "Select 'Country', Check for the 'GeoJSON' type data and download 'level2'"
- **Remarks**: "Geopackage, Shapefile data works similarly. This tool has been designed to fit with GeoJSON data."

## CEEI

- **Data**: Community Energy and Emissions Inventory
- **Supply Chain Mode**: Datafile downloading automated.
- **Source**:
  - **Buildings**: [BC Utilities Energy and Emissions Data](https://www2.gov.bc.ca/assets/gov/environment/climate-change/data/ceei/bc_utilities_energy_and_emissions_data_at_the_community_level.xlsx)
  - **Transportation**: [BC On Road Transportation Data](https://www2.gov.bc.ca/assets/gov/environment/climate-change/data/ceei/bc_on_road_transportation_data_at_the_community_level.xlsx)
  - **Waste**: [BC Municipal Solid Waste Data](https://www2.gov.bc.ca/assets/gov/environment/climate-change/data/ceei/bc_municipal_solid_waste_data_at_the_community_level.xlsx)
- **Description**: Please check [CEEI Methodology](https://www2.gov.bc.ca/gov/content/environment/climate-change/data/ceei/methodology)
- **Instruction**: -
- **Remarks**: -

## NREL

- **Data**: Annual Technology Baseline (ATB) - 2024
- **Supply Chain Mode**: Datafile downloading automated.
- **Source**:
  - **CSV**: [ATB CSV](https://oedi-data-lake.s3.amazonaws.com/ATB/electricity/csv/2024/ATBe.csv)
  - **Parquet**: [ATB Parquet](https://oedi-data-lake.s3.amazonaws.com/ATB/electricity/parquet/2024/ATBe.parquet)
- **Description**: [ATB Technologies](https://atb.nrel.gov/electricity/2024/technologies)
- **Instruction**: -
- **Remarks**: -

## Statistics Canada

- **Data**: Population projection 2021-2046.
- **Supply Chain Mode**: Manual Download from the portal
- **Source**: [BC Stats Population Projection](https://bcstats.shinyapps.io/popApp/)
- **Description**: Historical data up to 2023 and projection for 2024-2046.
- **Instruction**: Manually download from the portal with mentioned steps.
  1. **Select Data**:
     - Region Type: Regional District
     - Regions: Select all regions under BC
     - Select years: 2021 to 2046
     - Select genders: Totals
  2. **Choose Static**:
     - Choose 'count'
  3. **Select age format**:
     - Choose "Totals"
  4. **Customize Layout**:
     - Choose "None"
  5. Generate output and download CSV.
  6. In the downloaded CSV file: Delete all the rows on top until you get the column names.
- **Remarks**: The data source can be replaced but may need to format the data to fit with the scripts.
- **Mapping**:
  - **Different Name Mapping**:
    - Columbia Shuswap: Columbia-Shuswap
    - Comox-Strathcona: Strathcona
    - Greater Vancouver: Metro Vancouver
    - Powell River: qathet
    - Skeena-Queen Charlotte: North Coast
    - Stikine: Stikine (Census Division)
    - Northern Rockies: Northern Rockies (Census Division)

## Emission Factors

- **Source**: [Emission Factors Reference Values](https://www.canada.ca/en/environment-climate-change/services/climate-change/pricing-pollution-how-it-will-work/output-based-pricing-system/federal-greenhouse-gas-offset-system/emission-factors-reference-values.html)
- **Instruction**: A CSV datafile will be created based on the values found in the source.
