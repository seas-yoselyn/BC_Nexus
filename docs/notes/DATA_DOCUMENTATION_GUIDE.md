# BCNexus Data Documentation Guide

This guide helps you create comprehensive data documentation for the BCNexus project, following best practices inspired by the RESource documentation structure.

## Quick Start

1. **Copy the template**: Use `DATA_DOCUMENTATION_TEMPLATE.md` as your starting point
2. **Review the example**: Check `EXAMPLE_DATA_README.md` to see a completed documentation
3. **Place your README**: Create a `README.md` in your data folder (e.g., `data/processed_data/hydro/README.md`)
4. **Fill in details**: Replace all bracketed placeholders with actual information
5. **Keep it updated**: Update documentation when data changes

## Documentation Checklist

### Essential Information
- [ ] Dataset name and purpose
- [ ] Description of all files in the directory
- [ ] Column definitions for each CSV/data file
- [ ] Data sources and collection dates
- [ ] Units for all numerical values
- [ ] Temporal resolution and coverage (for timeseries)
- [ ] Spatial reference system (for spatial data)
- [ ] Processing steps applied
- [ ] Known limitations or issues

### Recommended Information
- [ ] Example code for loading/using the data
- [ ] Relationship to BCNexus model components
- [ ] Quality assurance checks performed
- [ ] Update history table
- [ ] Contact information
- [ ] Links to related documentation
- [ ] References to publications or methodologies

### Optional but Valuable
- [ ] Data lineage diagram
- [ ] Visualizations of key patterns
- [ ] Validation results
- [ ] Comparison with alternative data sources
- [ ] Future enhancement plans

## File Organization

```
data/
├── RESource/
│   └── README.md  ✓ (existing, good example)
├── processed_data/
│   ├── hydro/
│   │   ├── existing/
│   │   │   ├── README.md  (create this)
│   │   │   ├── hydro_generation.csv
│   │   │   └── bc_ext_ror_ts.csv
│   │   └── future/
│   │       └── README.md  (create this)
│   ├── wind/
│   │   └── README.md  (create this)
│   ├── solar/
│   │   └── README.md  (create this)
│   └── load/
│       └── README.md  (create this)
├── downloaded_data/
│   ├── CODERS/
│   │   └── README.md  (create this)
│   └── load/
│       └── README.md  (create this)
└── clews_data/
    └── README.md  (update existing)
```

## Documentation by Data Type

### Timeseries Data
Always document:
- Temporal resolution (hourly, daily, monthly)
- Start and end dates
- Timezone
- Missing data strategy
- Interpolation methods used
- Units for all variables
- Normalization applied (if any)

Example:
```markdown
##### `wind_generation_ts.csv`
   - **Records**: 8,760 hourly values (one year)
   - **Description**: Hourly wind generation capacity factors
   - **Columns**: time, site_001, site_002, ..., site_020
   - **Content**: Normalized capacity factors (0-1) starting from 2021-01-01 00:00 in BC local time (GMT-7)
   - **Units**: Dimensionless (fraction of nameplate capacity)
   - **Source**: RESource tool with ERA5 weather data
```

### Spatial Data
Always document:
- Coordinate reference system (e.g., WGS84, UTM Zone 10N)
- Spatial resolution
- Coverage area/boundaries
- Spatial aggregation method
- Topology (points, lines, polygons)

Example:
```markdown
##### `facility_locations.csv`
   - **Records**: 50 facility locations
   - **Description**: Geographic coordinates of generation facilities
   - **Columns**: facility_id, longitude, latitude, region, elevation_m
   - **Content**: Point locations in WGS84 (EPSG:4326), elevations from SRTM DEM
   - **Spatial Coverage**: British Columbia (48°N-60°N, 114°W-139°W)
   - **Source**: CODERS database with manual validation
```

### Economic/Technical Parameters
Always document:
- Units ($/kW, $/MWh, years)
- Reference year (for monetary values)
- Currency (CAD, USD)
- Inflation adjustment method
- Discount rate (if applicable)
- Source of assumptions
- Uncertainty ranges

Example:
```markdown
##### `technology_costs.csv`
   - **Records**: 15 technology types
   - **Description**: Capital and operating costs for generation technologies
   - **Columns**: tech_id, capex_per_kW, fom_per_kW_yr, vom_per_MWh, lifetime_years
   - **Content**: Cost parameters in 2024 CAD
   - **Units**: CAPEX (CAD/kW), FOM (CAD/kW/year), VOM (CAD/MWh), Lifetime (years)
   - **Source**: NREL ATB 2024, adjusted for Canadian context
   - **Uncertainty**: ±15-30% based on technology maturity
```

### Scenario Data
Always document:
- Scenario name and description
- Key assumptions
- Parameter variations from baseline
- Time horizon
- Related scenarios
- Policy context

Example:
```markdown
##### `scenario_CNZ2050.csv`
   - **Records**: Policy parameters for Carbon Neutral by 2050 scenario
   - **Description**: Emission constraints and technology deployment targets
   - **Columns**: year, emission_cap_MtCO2, renewable_min_pct, electrification_target
   - **Content**: Annual trajectory from 2025-2050 aligned with BC CleanBC policy
   - **Assumptions**: 
     - Linear emission reduction path
     - 100% clean electricity by 2030
     - 80% electrification of transport by 2050
   - **Source**: BC CleanBC Roadmap to 2030
```

## Best Practices

### 1. Use Consistent Terminology
- Follow BCNexus conventions (e.g., "capacity factor" not "CF" in documentation)
- Define acronyms on first use
- Use standard units consistently

### 2. Link to Related Documentation
```markdown
## Related Documentation
- [BCNexus Wiki - Energy System](../BC_Nexus.wiki/Energy-System.md)
- [Configuration File](../config/data_sources.yaml)
- [Processing Script](../workflow/scripts/process_hydro.py)
```

### 3. Provide Working Examples
Include copy-paste-ready code snippets:
```python
# Good example - specific and complete
import pandas as pd
data = pd.read_csv('data/processed_data/hydro/existing/hydro_generation.csv')
total_capacity = data['capacity_MW'].sum()
print(f"Total: {total_capacity:.1f} MW")
```

### 4. Document Data Quality
Be transparent about limitations:
```markdown
## Known Issues
- Small facilities (<10 MW) have estimated efficiency values
- Inflow data for ungauged basins uses regional approximations
- 2020 data incomplete due to COVID-19 reporting gaps
```

### 5. Maintain Version History
Track changes clearly:
```markdown
## Update History
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2024-11-18 | v1.0 | Initial creation | Team |
| 2024-11-20 | v1.1 | Added new facilities | Elias |
```

## Integration with BCNexus Workflow

### Link to Configuration Files
Reference your data in `config/data_sources.yaml`:
```yaml
hydro:
  generation_file: "data/processed_data/hydro/existing/hydro_generation.csv"
  timeseries_file: "data/processed_data/hydro/existing/bc_ext_ror_ts.csv"
```

### Document Processing Scripts
Reference the scripts that create/process your data:
```markdown
### Processing Pipeline
1. **Data Download**: `workflow/scripts/download_coders.py`
2. **Spatial Processing**: `workflow/scripts/create_hydro_assets.py`
3. **Timeseries Generation**: `workflow/scripts/ror_ps.py`
```

### Cross-Reference Wiki Pages
Link to relevant wiki documentation:
- [How to Update Input Files](../BC_Nexus.wiki/How-to-Update-the-Input-Files.md)
- [Model Structure](../BC_Nexus.wiki/Model-Structure.md)

## Templates by Data Category

### For Downloaded/Raw Data
Focus on:
- Original source and download method
- License and usage restrictions
- Download date and version
- No processing applied

### For Processed/Derived Data
Focus on:
- Source data used as input
- Processing pipeline details
- Validation performed
- Relationship to model components

### For Model Inputs
Focus on:
- Format requirements for model
- Parameter definitions aligned with OSeMOSYS/CLEWS
- Relationship to other input files
- How to update for scenarios

### For Results/Outputs
Focus on:
- Model run parameters
- Scenario description
- Result interpretation
- Visualization options

## Review Checklist

Before finalizing documentation, check:
- [ ] Can someone unfamiliar with the data understand it?
- [ ] Are all files in the directory documented?
- [ ] Are column names explained?
- [ ] Are units clearly specified?
- [ ] Can someone reproduce the processing?
- [ ] Are there working code examples?
- [ ] Are limitations honestly stated?
- [ ] Is contact information current?
- [ ] Are links to related docs working?
- [ ] Is the update history complete?

## Getting Help

- **Questions**: Ask the BCNexus team on the project channel
- **Examples**: Review `data/RESource/README.md` and `docs/EXAMPLE_DATA_README.md`
- **Template**: Use `docs/DATA_DOCUMENTATION_TEMPLATE.md`
- **Wiki**: Check [BCNexus Wiki](../BC_Nexus.wiki/Home.md) for model context

---

**Guide Version**: 1.0  
**Last Updated**: 2025-11-18  
**Maintainer**: BC Nexus Data Team
