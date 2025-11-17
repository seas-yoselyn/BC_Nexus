# RESource Results

The datafiles in this folder represents spatial, temporal and nameplate attributes of __Variable Renewable Energy (VRE) resource options for BC__. Resource options includes committed and candidate sites for utility scale solar photovoltaic (PV) and on-shore (land-based) wind projects only. __Candidate sites__ are extracted using BC instance of the __[RESource](https://deltae.github.io/RESource/index.html)__ tool and subjected to explicit version of the tool's instance. For __committed sites__, only the timeseries are extracted using RESource, using known project points' timeseries extraction feature from RESource.

__Notes__:
- The timeseries have been extracted using weather dataset for calendar year (YYYY) __2023__.
-  Files with __'BC_CFPXX'__ denotes representative dataset to model successful (contracted/announced) sites from Call For Power (CFP) by BC Hydro.
-  Files are formatted to be used for downstream modelling tools
   - __timeseries__: 
     -    Files with __'X_ts'__ represents timeseries datafiles. The _time_ column could be used as standard datetimestamp index. 
     -    Timeseries index represents local time of BC in [Etc/GMT+7](https://greenwichmeantime.com/time-zone/gmt-7). 
     -    Rest of the column names represents unique identifier for the sites.
   -  __resource attributes__ : 
      -  The __'project_name'__ columns represents the unique identifier for the committed sites. 
      -  'ERA5_cell' columns represents the unique identifiers for the candidate sites extracted via RESource tool.

## About Data Files (CSvs)

### A. Committed Resources

#### A-1. Solar Resources

##### `BC_CFP24_solar.csv`
   - **Records**: Utility scale solar PV projects
   - **Description**: Solar project details from BC Hydro's Clean Power Facility (CFP) 2024 call
   - **Columns**: ERA5_cell, project_name, longitude, latitude, regional_system, expected_cod, poi, potential_capacity, annual_energy_GWh, Region, resource_type, capex, Operational_life, vom, fom, start_year
   - **Content**: Contains the ShTSaQU Solar Project information with technical and economic parameters

##### `BCH_CFP24_solar_ts.csv`
  - **Records**: 8,760 hourly values (one year)
  - **Description**: Hourly solar capacity factor timeseries for CFP 2024 solar project
  - **Columns**: time, ShTSaQU Solar Project
  - **Content**: Hourly generation profile starting from YYYY-01-01
  
#### A-2. Wind Resources

##### `BC_CFP24_wind.csv`
   - **Records**: utility scale on-shore wind projects
   - **Description**: Wind project details from BC Hydro's Clean Power Facility (CFP) 2024 call
   - **Columns**: ERA5_cell, project_name, longitude, latitude, regional_system, expected_cod, poi, potential_capacity, annual_energy_GWh, Region, resource_type, capex, Operational_life, vom, fom, start_year
   - **Content**: Multiple wind projects with technical specifications and economic parameters

#### `BCH_CFP24_wind_ts.csv`
   - **Records**: 8,760 hourly values (one year)
   - **Description**: Hourly wind capacity factor timeseries for CFP 2024 wind projects
   - **Content**: Hourly generation profiles for each wind project starting from YYYY-01-01

### B. Candidate Sites as Future Resource Options
> For more about the study and publications : RESource - [BC Case Study](https://deltae.github.io/RESource/notes/case_BC.html)
> 
#### B-1. Solar Resources
##### `resource_options_solar_BC.csv`
   - **Records**: Cluster representation of utility sclae solar PV resource options in future. 
   - **Description**: Clustered solar resource options across BC regions
   - **Columns**: cluster_id, lcoe, capex, fom, vom, CF_mean, Cluster_No, potential_capacity, Region, nearest_station, nearest_station_distance_km, Rank, Operational_life, resource_type
   - **Content**: Technical and economic parameters for solar resources by region including LCOE, capacity factors, and potential capacity

#### `resource_options_solar_BC_timeseries.csv`
- **Records**: 8,760 hourly values (one year)
- **Description**: Hourly capacity factor timeseries for each solar resource cluster
- **Content**: Time-indexed generation profiles for all solar clusters identified in `resource_options_solar_BC.csv`

#### B-2. Wind Resources
##### `resource_options_wind_BC.csv`
  - **Records**: 8 wind resource clusters
  - **Description**: Clustered wind resource options across BC regions
  - **Columns**: cluster_id, lcoe, capex, fom, vom, CF_mean, Cluster_No, potential_capacity, Region, nearest_station, nearest_station_distance_km, Rank, Operational_life, resource_type
  - **Content**: Technical and economic parameters for wind resources by region including LCOE, capacity factors, and potential capacity

##### `resource_options_wind_BC_timeseries.csv`
  - **Records**: 8,760 hourly values (one year)
  - **Description**: Hourly capacity factor timeseries for each wind resource cluster
  - **Content**: Time-indexed generation profiles for all wind clusters identified in `resource_options_wind_BC.csv`

## Metadata

- **`Data_Units.xlsx`**: Documents the units and measurement standards used in the datasets
- **`Resource_options_summary.txt`**: Documents the brif summary of resource options and methodology
