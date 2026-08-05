# BCNexus Data Documentation Template

This template provides a standardized format for documenting datasets within the BC Nexus model. Following this structure ensures consistency and clarity across all data documentation.

---

## [Dataset Name]

Brief description of what this dataset represents and its purpose within the BCNexus model. Mention the source or tool used to generate/acquire the data.

**Notes**:
- Note about data year/temporal coverage (e.g., "The timeseries have been extracted for calendar year (YYYY) __2023__")
- Any special naming conventions or prefixes used in files
- Format requirements for downstream modelling tools
- Any coordinate system or timezone information (e.g., "Timeseries index represents local time of BC in [Etc/GMT+7](https://greenwichmeantime.com/time-zone/gmt-7)")
- Other important contextual information

## About Data Files

### A. [Primary Category] (e.g., Existing Resources, Historical Data)

#### A-1. [Sub-category] (e.g., Hydro Resources, Load Data)

##### `filename_example.csv`
   - **Records**: [Number/type of records, e.g., "8,760 hourly values", "50 power plants"]
   - **Description**: [Brief description of what this file contains]
   - **Columns**: [comma-separated list of column names]
   - **Content**: [Detailed explanation of what data is included, any special characteristics]
   - **Source**: [Original data source, tool, or reference]
   - **Processing**: [Any transformations or processing applied to raw data]
   - **Dependencies**: [Files or data this depends on]

##### `filename_timeseries.csv`
   - **Records**: [Temporal resolution and coverage]
   - **Description**: [What timeseries data this contains]
   - **Columns**: [time column + data columns]
   - **Content**: [Description of temporal patterns, starting date, etc.]
   - **Units**: [Specify units for all data columns]
   - **Source**: [Tool/source for timeseries generation]

#### A-2. [Another Sub-category]

##### `another_file.csv`
   - **Records**: [Record count/type]
   - **Description**: [File purpose]
   - **Columns**: [column names]
   - **Content**: [Detailed content description]

### B. [Secondary Category] (e.g., Future Scenarios, Candidate Sites)

> Optional: Add contextual information or links to related documentation
> For more information: [Link to relevant documentation or publication]

#### B-1. [Sub-category]

##### `scenario_data.csv`
   - **Records**: [Record information]
   - **Description**: [Scenario description]
   - **Columns**: [column names including IDs, parameters, etc.]
   - **Content**: [Technical and economic parameters included]
   - **Methodology**: [How scenarios were developed]
   - **Assumptions**: [Key assumptions in the data]

##### `scenario_timeseries.csv`
   - **Records**: [Temporal information]
   - **Description**: [Timeseries purpose and content]
   - **Content**: [Time-indexed data description]
   - **Relationship**: [Reference to parent scenario file if applicable]

#### B-2. [Another Sub-category]

##### `additional_scenario_file.csv`
   - **Records**: [Records description]
   - **Description**: [File description]
   - **Columns**: [column list with key identifiers]
   - **Content**: [Detailed content and parameter descriptions]

## Metadata

- **`Units_Reference.xlsx`**: [Description of units documentation file]
- **`Methodology_Summary.txt`**: [Description of methodology documentation]
- **`Data_Dictionary.csv`**: [Description of data dictionary if available]
- **`Processing_Log.md`**: [Description of processing history/changelog]

## Data Lineage

### Source Data
- **Original Sources**: [List of primary data sources]
- **Collection Date**: [When data was collected/downloaded]
- **Version/Release**: [Version information if applicable]

### Processing Pipeline
1. **Step 1**: [Description of first processing step]
   - Input: [Input files]
   - Output: [Output files]
   - Tools/Scripts: [Scripts or tools used]

2. **Step 2**: [Description of second processing step]
   - Input: [Input files]
   - Output: [Output files]
   - Tools/Scripts: [Scripts or tools used]

3. **Final Step**: [Description of final processing]
   - Input: [Input files]
   - Output: [Output files]
   - Tools/Scripts: [Scripts or tools used]

## Quality Assurance

- **Validation Checks**: [Description of validation performed]
- **Known Issues**: [Any known data quality issues or limitations]
- **Data Completeness**: [Information about missing data or gaps]
- **Uncertainty**: [Quantification of data uncertainty where applicable]

## Usage Guidelines

### Integration with BCNexus Model
- **Model Components**: [Which BCNexus components use this data]
- **Configuration**: [Related configuration files in `config/` directory]
- **Input Format**: [Expected format for model ingestion]

### Common Use Cases
1. **[Use Case 1]**: [Description and relevant files]
2. **[Use Case 2]**: [Description and relevant files]
3. **[Use Case 3]**: [Description and relevant files]

### Code Examples
```python
# Example of how to load and use this data
import pandas as pd

# Load the dataset
data = pd.read_csv('path/to/filename.csv')

# Basic operations
# ...
```

## Update History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| YYYY-MM-DD | v1.0 | Initial dataset creation | [Name] |
| YYYY-MM-DD | v1.1 | [Description of changes] | [Name] |

## References

1. [Reference to publication or documentation]
2. [Reference to data source]
3. [Reference to methodology paper]

## Contact & Support

- **Data Steward**: [Name and contact]
- **Issues**: [Link to issue tracker or contact method]
- **Related Documentation**: [Links to wiki pages, related docs]

---

## Template Usage Instructions

### When creating new data documentation:

1. **Copy this template** to your data folder with an appropriate name (e.g., `README.md`)
2. **Replace all bracketed placeholders** `[...]` with actual information
3. **Remove sections** that are not applicable to your dataset
4. **Add custom sections** if needed for specific data characteristics
5. **Include examples** where possible to aid understanding
6. **Link to related documentation** in the wiki or other docs folders
7. **Keep it updated** as data evolves or processing changes

### Documentation Best Practices:

- **Be specific**: Provide exact column names, units, and formats
- **Be complete**: Document all files in the directory
- **Be clear**: Write for users who may be unfamiliar with the data
- **Be organized**: Use consistent heading levels and structure
- **Be current**: Update documentation when data changes
- **Be helpful**: Include examples, visualizations, and use cases
- **Cross-reference**: Link to related config files, scripts, and wiki pages

### For Timeseries Data:

Always specify:
- Temporal resolution (hourly, daily, etc.)
- Start and end dates
- Timezone
- Missing data handling
- Units for all variables

### For Spatial Data:

Always specify:
- Coordinate reference system (CRS)
- Spatial resolution
- Coverage area/boundaries
- Any spatial aggregation applied

### For Economic/Technical Parameters:

Always specify:
- Units ($/kW, $/MWh, years, etc.)
- Reference year (for costs)
- Currency (CAD, USD)
- Source assumptions
- Uncertainty ranges if available

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-18  
**Template Maintainer**: BC Nexus Team
