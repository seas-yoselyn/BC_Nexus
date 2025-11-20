# BCNexus Processed Data - Hydro Systems

This dataset contains processed hydroelectric system data for British Columbia, including existing generation facilities, reservoir characteristics, and temporal profiles. The data has been processed from multiple sources including CODERS database, BC Hydro information, and hydrological basin data to support the BCNexus CLEWS model.

**Notes**:
- Timeseries data represents calendar year 2021-2022 with hourly resolution
- All coordinates are in WGS84 (EPSG:4326) geographic coordinate system
- Timeseries are in local BC time (Etc/GMT+7)
- Processing pipeline combines spatial analysis, capacity factor calculations, and inflow modeling
- Files are formatted for direct integration with OSeMOSYS/CLEWS modeling framework

## About Data Files

### A. Existing Hydro Resources

#### A-1. Hydroelectric Generation Facilities

##### `hydro_generation.csv`
   - **Records**: ~30 existing hydroelectric facilities in BC
   - **Description**: Comprehensive database of existing hydro generation assets including run-of-river and reservoir-based facilities
   - **Columns**: facility_id, facility_name, type, longitude, latitude, region, capacity_MW, annual_generation_GWh, commissioning_year, operator
   - **Content**: Contains technical specifications, geographical locations, and operational parameters for each facility. Includes both BC Hydro and Independent Power Producer (IPP) facilities.
   - **Source**: CODERS database, BC Hydro generation data
   - **Processing**: Spatial joining with regional boundaries, capacity verification against historical generation data
   - **Dependencies**: GADM regional boundaries, CODERS generators dataset

##### `bc_ext_ror_ts.csv`
   - **Records**: 8,760 hourly values (one year)
   - **Description**: Hourly capacity factor timeseries for run-of-river (RoR) hydroelectric facilities
   - **Columns**: time, [facility_id_1], [facility_id_2], ..., [facility_id_n]
   - **Content**: Normalized capacity factors (0-1) representing hourly generation potential based on hydrological modeling and historical flow patterns. Starting from 2021-01-01 00:00 local time.
   - **Units**: Dimensionless (capacity factor as fraction)
   - **Source**: Generated using atlite cutout data and HydroBASINS watershed analysis
   - **Processing**: Flow speed parameterization (flowspeed=1), height adjustment applied

#### A-2. Reservoir Systems

##### `hydro_reservoirs.csv`
   - **Records**: ~15 major reservoir facilities
   - **Description**: Storage reservoir characteristics including storage capacity, operating parameters, and physical constraints
   - **Columns**: reservoir_id, reservoir_name, longitude, latitude, region, capacity_MW, storage_capacity_GWh, max_storage_m3, min_storage_m3, efficiency, commissioning_year, associated_basins
   - **Content**: Physical and operational parameters for reservoir systems including storage capacity in both energy and volume units, efficiency factors, and linkages to hydrological basins
   - **Source**: BC Hydro reservoir data, custom WUP (Water Use Plan) feature datasets
   - **Processing**: Integration of generation and reservoir features from WUP data, basin assignment via spatial analysis
   - **Dependencies**: hydro_gen_wup_features.csv, hydro_res_wup_features.csv, HydroBASINS shapefiles

##### `bc_ext_reservoir_inflows.csv`
   - **Records**: 8,760 hourly values (one year)
   - **Description**: Hourly inflow timeseries for reservoir systems based on watershed modeling
   - **Columns**: time, [reservoir_id_1], [reservoir_id_2], ..., [reservoir_id_n]
   - **Content**: Volumetric inflow rates calibrated to mean annual inflow statistics. Includes seasonal variation and inter-annual patterns.
   - **Units**: m³/s (cubic meters per second)
   - **Source**: Derived from HydroBASINS Level 12 watershed analysis and historical inflow statistics
   - **Processing**: Mean inflow calibration method applied (inflow_method: "mean_inflow_calibrate"), height adjustment enabled
   - **Dependencies**: HydroBASINS shapefiles (NA and Arctic regions), inflow statistics tables

### B. Supporting Infrastructure

#### B-1. Cascade Relationships

##### `hydro_cascade.csv`
   - **Records**: ~20 cascade connections
   - **Description**: Upstream-downstream relationships between hydro facilities defining water flow paths
   - **Columns**: upstream_facility_id, downstream_facility_id, cascade_type, distance_km, time_lag_hours
   - **Content**: Defines the hydrological network structure for modeling water flow and generation interdependencies
   - **Source**: CODERS hydro_cascade dataset
   - **Processing**: Validation of connectivity, removal of invalid connections

## Metadata

- **`Data_Units.xlsx`**: Documents units and measurement standards for all hydro system parameters (MW, GWh, m³/s, etc.)
- **`inflow_stats/`**: Directory containing standardized inflow statistics tables by basin for calibration
- **`processing_log.txt`**: Detailed log of data processing steps and parameter choices

## Data Lineage

### Source Data
- **CODERS Database**: Canadian Open Data Energy Resource System (downloaded 2024-Q2)
- **BC Hydro**: Custom WUP features and generation statistics
- **HydroBASINS**: Level 12 watershed boundaries (v1c) for North America and Arctic regions
- **Inflow Statistics**: Historical streamflow data from BC Hydro and WSC (Water Survey of Canada)
- **Collection Date**: 2024-06-15 (CODERS), 2024-03 (WUP data)

### Processing Pipeline
1. **Spatial Integration**
   - Input: CODERS raw data, GADM boundaries, HydroBASINS
   - Output: Geo-located facilities with basin assignments
   - Tools/Scripts: `workflow/scripts/create_hydro_assets.py`

2. **Timeseries Generation**
   - Input: Atlite cutout (BC_2021_2022.nc), facility locations, basin geometry
   - Output: Capacity factor and inflow timeseries
   - Tools/Scripts: `workflow/scripts/reservoir_inflows.py`, `workflow/scripts/ror_ps.py`

3. **Calibration and Validation**
   - Input: Generated timeseries, historical generation/inflow statistics
   - Output: Calibrated timeseries matching observed patterns
   - Tools/Scripts: Calibration routines within timeseries scripts

## Quality Assurance

- **Validation Checks**: 
  - Annual generation totals verified against BC Hydro reported values (within ±5%)
  - Capacity factors checked for physical feasibility (0 ≤ CF ≤ 1)
  - Reservoir storage bounds validated against physical constraints
  - Cascade relationships verified for logical flow direction
  
- **Known Issues**: 
  - Some small RoR facilities (<10 MW) may have limited historical data for validation
  - Inflow timeseries for ungauged basins rely on regional approximations
  - Inter-annual variability not captured (using typical year approach)
  
- **Data Completeness**: 
  - All major facilities (>50 MW) are included with complete parameters
  - Minor facilities may have estimated efficiency values where measured data unavailable
  
- **Uncertainty**: 
  - Capacity factors: ±10% for well-documented facilities, ±20% for facilities with limited data
  - Inflow estimates: ±15-25% depending on watershed gauging coverage

## Usage Guidelines

### Integration with BCNexus Model
- **Model Components**: Energy system module (power generation), Water system module (reservoir operations)
- **Configuration**: Referenced in `config/data_sources.yaml` under `data.coders.hydro_existing` and `output.create_hydro_assets`
- **Input Format**: CSV format compatible with otoole/OSeMOSYS input processing pipeline

### Common Use Cases
1. **Scenario Development**: Use hydro generation parameters as baseline for future capacity expansion scenarios
2. **Water-Energy Nexus Analysis**: Combine reservoir operations with irrigation/municipal water demand
3. **Temporal Analysis**: Use hourly timeseries for time-slice aggregation or representative day selection

### Code Examples
```python
# Example: Load and analyze hydro generation capacity
import pandas as pd
import matplotlib.pyplot as plt

# Load hydro generation facilities
hydro_gen = pd.read_csv('data/processed_data/hydro/existing/hydro_generation.csv')

# Calculate total capacity by region
capacity_by_region = hydro_gen.groupby('region')['capacity_MW'].sum()
print(f"Total BC Hydro Capacity: {hydro_gen['capacity_MW'].sum():.1f} MW")

# Load and plot RoR timeseries for a facility
ror_ts = pd.read_csv('data/processed_data/hydro/existing/bc_ext_ror_ts.csv', 
                      index_col='time', parse_dates=True)

# Plot seasonal pattern
ror_ts['facility_001'].resample('M').mean().plot(
    title='Monthly Average Capacity Factor', 
    ylabel='Capacity Factor'
)
plt.show()
```

## Update History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-06-20 | v1.0 | Initial dataset creation from CODERS and BC Hydro sources | Elias, Pierre |
| 2024-08-15 | v1.1 | Added cascade relationships, updated inflow calibration | Bruno |
| 2024-10-10 | v1.2 | Refined timeseries processing with improved flow parameterization | Elias |

## References

1. CODERS Database: https://github.com/canoe-project/coders
2. HydroBASINS: Lehner, B., and Grill G. (2013). Global river hydrography and network routing
3. BC Hydro Water Use Plans: https://www.bchydro.com/energy-in-bc/operations/water-use-planning.html
4. OSeMOSYS Framework: Howells et al. (2011). Energy Policy, 39(10)

## Contact & Support

- **Data Steward**: Md Eliasinul Islam, Pierre McWhannel
- **Issues**: GitHub Issues at DeltaE/BC_Nexus
- **Related Documentation**: 
  - [BCNexus Wiki - Energy System](../BC_Nexus.wiki/Energy-System.md)
  - [BCNexus Wiki - Water System](../BC_Nexus.wiki/Water-and-Climate-System.md)
  - [Data Sources Configuration](../config/data_sources.yaml)

---

**Document Version**: 1.2  
**Last Updated**: 2024-10-10  
**Maintainer**: BC Nexus Data Team
