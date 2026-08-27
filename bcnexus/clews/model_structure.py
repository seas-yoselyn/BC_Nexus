#  M Eliasinul Islam (EL), 2024

# ____________________________________________
# This file defines the constants of clews model building script.
# Based on the data in this file, clewsy builds the SETS, InputActivityRatio and OutputActivityRatio

Model= 'BC Clews Model V2.1' # 20250606, v.2 + With YOSE's work
clews_builder_cfg_path='config/clews_builder.yaml'
clews_scenario_cfg_path='config/scenarios_bcnexus.yaml'

# The OSeMOSYS regions in the model.  
# For most models, leave this as REGION1 as CLEWs regions are built with technologies and commodities rather than OSeMOSYS regions.
Regions= {'REGION1': ['BC','#000000']}

# Add or reduce the model time horizon as needed.
snapshot={ 
  'start': 2021,
  'end':2026
  }

HYDRO_GENERATION= {
    "cascade_group_1": [
      "Mica/Columbia",
      "Peace",
      "Stave",
      "Bridge",
      "Campbell",
      "Seven Mile"
    ]
  }


# The labels for the land regions being represented in the model.
# These must match the file names in the clustered land use data in the data directory.
# The land regions are usually two or three letter codes.
LandRegions= ['BC1']
  

# Connecting the land use (and thereby the energy needs) from a given land region to an electrical grid.
# Each land region must have an associated electrical grid.  Grids have a single letter code.
LandToGridMap={
  'BC1': 'B'  # Region BC1 is connected to grid B (in this version of the model, the assumption is, we only have one grid in BC)
}

# Data directory and file names for the land use data for the model.
NamingConvention = {
  'AGR': 'Agricultural',
  'ALF': 'Alfalfa',
  'BAR': 'Barley',
  'BIO': 'Biomass',
  'CHC': 'Charcoal',
  'COA': 'Coal',
  'COM': 'Commercial',
  'CRU': 'Crude oil',
  'CRP': 'Crop production',
  'DSL': 'Diesel',
  'ELCB01': 'Electricity from power plants', # in Grid (B) for region (BC1)
  'ELCB02': 'Electricity from transmission',  # in Grid (B) for region (BC1)
  'GSL': 'Gasoline',
  'HFO': 'Heavy fuel oil',
  'HDG': 'Hydrogen',
  'HYD': 'Hydropower',
  'IND': 'Industry',
  'JFL': 'Jet fuel',
  'KER': 'Kerosene',
  'LPG': 'LPG',
  'MAI': 'Maize',
  'NGS': 'Natural gas',
  'OAT': 'Oat',
  'OHC': 'Other hydrocarbons',
  'OTH': 'Other',
  'PEA': 'Dry pea',
  'PTW': 'White potato',  # corrected from 'PWT'
  'RAP': 'Rapeseed',
  'RPP': 'Refined petroleum products', # Defined in Canada Energy Future Report
  'RES': 'Residential',
  'RYE': 'Rye',
  'SOL': 'Solar',
  'TRA': 'Transport',
  'URN': 'Uranium',
  'WHE': 'Wheat',
  'WND': 'Wind',
  'CCS' :'Carbon Capture and Storage',
  #'BEF': 'Beef', # EL_20250606, for YOSE
  #'MIL': 'Milk',# EL_20250606, for YOSE
  #'PIG': 'Swine', 
  #'SHP': 'Sheep',
}

# The data for region RG1 will be in file data/clustering_results_RG1.csv
LandCluster_data ={
  'root': "data/clews_data/LandClusterData",
  'ClusterBaseFileName': 'clustering_results_',
  'PrecipitationClusterBaseFileName': 'clustering_results_prc_',
  'EvapotranspirationClusterBaseFileName': 'clustering_results_evt_',
  'IrrigationWaterDeficitClusterBaseFileName': 'clustering_results_cwd_'
}


## Irrigation types - generally do not change.
#IrrigationTypeList=self.cfg['IrrigationTypeList']  
IrrigationTypeList : dict= {
'R': 'Rain-fed',
'I': 'Irrigation'
}

## Agricultural intensities - generally do not change.
# IntensityList :dict= self.cfg['IntensityList']
IntensityList= {
    'L': 'Low',
    'I': 'Intermediate',
    'H': 'High'
    }



# Land use codes for other lands not included in croplands.
LandUseCodes= {
  'BAR': 'Barren and sparsely vegetated land',
  'FOR': 'Forest land',
  'GRS': 'Grassland & woodland',
  'BLT': 'Built-up land',
  'WAT': 'Water bodies',
  'OTH': 'Other agricultural land',
  #'PSN': 'Natural pasture',
  #'PSC': 'Cultivated pasture',
  #'PCF': 'Confined livestock operations',
}

# Evapotranspiration values for water balances for other land uses.
    # Values given in this sample were taken from the Bolivia model by Abhishek Shivakumar.
    # Generally no need to edit these values.
# -------->>>>>>>>>>>>>>>>>>> needs to be automated from an Open-source
EvapotranspirationPercentPRCOtherLandUse= {  
  'BAR': 0.773,
  'FOR': 0.691,
  'GRS': 0.694,
  'BLT': 0.631,
  'WAT': 0.571,
  'OTH': 0.694,
  # 'PAS': 0.694,#This needs to be corrected, this value is a test ;# 20250606, for YOSE's work
  # 'AGV': 0.694 #This needs to be corrected, this value is a test ;# 20250606, for YOSE's work
}

# Ratios for how much excess water goes to groudwater vs surface runoff.
    # Values given in this sample were taken from the Bolivia model by Abhishek Shivakumar.
    # Generally no need to edit these values.
# -------->>>>>>>>>>>>>>>>>>> needs to be automated from an Open-source
GroundwaterPercentofExcessOtherLandUse= {  
  'BAR': 0.009,
  'FOR': 0.077,
  'GRS': 0.051,
  'BLT': 0.072,
  'WAT': 0.017,
  'OTH': 0.051,
  # 'PAS': 0.051, #This needs to be corrected, this value is a test # 20250606, for YOSE's work
  # 'AGV': 0.694 #This needs to be corrected, this value is a test # 20250606, for YOSE's work
}

# Percent of excess water (Irrigation + Precipitation - Evapotranspiration) that returns as groundwater.
# for croplands.  Rest returns as Runoff.
GroundwaterPercentofExcess= 0.051

# Defines the final demand fuels in the model, and the sectors they are used in.
# Defines the final demand fuels in the model, and the sectors they are used in.
EndUseFuels= {
  'IND': ['DSL', 'BIO', 'NGS', 'ELCB02', 'HDG'],
  'RES': ['BIO', 'NGS', 'ELCB02','RPP','HDG'],
  'COM': ['BIO', 'NGS', 'ELCB02','RPP','HDG'],
  # 'AGR': ['DSL', 'NGS', 'ELCB02'], # 'AGR' is not used in the model due to data availability
  'TRA': ['GSL', 'DSL', 'HFO', 'JFL', 'BIO', 'NGS', 'LPG', 'ELCB02','HDG']
}

# Imports and exports - add and remove fuels as needed to represent a given region.
ImportFuels= ['JFL', 'LPG', 'GSL', 'DSL', 'HFO','CRU', 'COA','RPP' ] # EL_20251115 added 'KER''CRU','COA' to harmonize with Canada Energy Future Report 2024 data
ExportFuels= ['NGS',  'BIO','CRU', 'COA'] #EL_20251115 added 'CRU', 'COA'
CarbonCaptureFuels= ['CO2CCS']  # Fuels associated with carbon capture and storage.

# Domestically available fuels.
DomesticMining= ['NGS', 'URN','CRU', 'COA'] #EL_20251115 added 'CRU', 'COA'
DomesticRenewables= ['WND', 'HYD', 'BIO', 'SOL', 'GEO']


LandUseIntensity_FUEL='LND4PWR'
# Transformation technologies that connect parts of the CLEWs model together.  
    # For example, power transmission between grids, oil refineries, biofuel plants, etc.
    # Note:  These technologies cannot create fuels but assume that their fuels are created elsewhere (either in the DomesticMining, DomesticRenewables or ImportFuels).

"""
______________________________________________________________________________________________
>>>>>>>>>>>>>>>>>>>>>>>>>>>> Structure: <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
['TECHNOLOGY', 'INPUTFUEL', 'IAR', 'OUTPUTFUEL', 'OAR', 'Name', 'ModeOfOperation']

# One can use multiple lines for a single technology to create additional input or output activity ratios for a given technology (such as the refinery example below).

"""
TransformationTechnologies_schema= [
  'TECHNOLOGY',          # Technology code
  'FUEL_input',          # Input fuel code
  'InputActivityRatio',  # Input activity ratio (for 1 PJ of output, how much input fuel is needed)
  'FUEL_output',         # Output fuel code
  'OutputActivityRatio', # Output activity ratio (for 1 PJ of input, how much output fuel is produced)
  'Name',                # Description of the technology
  'MODE_OF_OPERATION'      # Mode of operation code (usually 1)
  ]
TransformationTechnologies= [
# 90% efficient grid distribution system:
 ['PWRTRNB01', 'ELCB01', '1.11', 'ELCB02', '1', 'Power transmission grid B', '1'],
  
# Example of land use impact of a power generation technology:
# ['power plant name and discription', 'input fuel', 'input activity ratio: for 1PJ of output how much land will be needded', 'output fuel- leave it blank', 'output activity raio- leave it blank', 'discription-leave it blank', 'Mode of operation'],
 
 # CCS technology
 ['CCS', '', '', 'CO2CCS', '1', 'Carbon Capture and Storage', '1'],
  
# Hydrogen production technology
 ['HDG', '', '','HDG', '1',  'Hydrogen production', '1'],
 
 # lands needed for Livestock
 
 
 # Lands that needed for Powerplants
 ['LNDAGRBC1C01', '', '', 'LND4PWR', '1', '', '54'], #seven times for all land clusters from GEAZ clustering
 ['LNDAGRBC1C02', '', '', 'LND4PWR', '1', '', '54'], # connection between LND4PWR with Built-up land in LNDAGRBC
 ['LNDAGRBC1C03', '', '', 'LND4PWR', '1', '', '54'],
 ['LNDAGRBC1C04', '', '', 'LND4PWR', '1', '', '54'],
 ['LNDAGRBC1C05', '', '', 'LND4PWR', '1', '', '54'],
 ['LNDAGRBC1C06', '', '', 'LND4PWR', '1', '', '54'],
 ['LNDAGRBC1C07', '', '', 'LND4PWR', '1', '', '54'],
 
 # Thermal
 ['PWRNGSB', 'LND4PWR', '0.0006', '', '', '', '1'], 
 ['PWRBIOB', 'LND4PWR', '0.293', '', '', '', '1'],
 
 # Hydro
 ['PWRHYDB', 'LND4PWR', '0.022', '', '', '', '1'],
 
 # VREs
 ['PWRWNDB', 'LND4PWR', '0.00038', '', '', '', '1'],
 ['PWRSOLB', 'LND4PWR', '0.0044', '', '', '', '1'],

## Geothermal
 ['PWRGEOB', 'LND4PWR', '0.00054', '', '', '', '1'],

## Nuclear
 ['PWRURNB', 'LND4PWR', '0.00003', '', '', '', '1'],

# Example of a crude oil refinery that produces a number of output products.
# ['UPSCRU001', 'CRU', '1.0', 'LPG', '0.0081', 'Crude oil refinery', '1'],
# ['UPSCRU001', '', '', 'GSL', '0.1694', 'Crude oil refinery', '1'],
# ['UPSCRU001', '', '', 'KER', '0.0694', '', '1'],
# ['UPSCRU001', '', '', 'DSL', '0.3221', '', '1'],
# ['UPSCRU001', '', '', 'HFO', '0.1429', '', '1'],
# ['UPSCRU001', '', '', 'OHC', '0.0816', '', '1'],
  
  # Biofuel Processing
  # ['UPSPLM001', 'CRPPLM', '1.0', 'PLMKER', '0.2', 'Palm oil mill.', '1'],
  # ['UPSPLM001', '', '', 'PLMPOM', '0.3', '', '1'],
  # ['UPSPLM001', '', '', 'PLMCRU', '0.5', '', '1'],
  
  # Palm Oil Refinery
  
  # Palm oil blending plant
  # SwitchGrass Biofuel Powerplants  # EL_20251125 added
  ['PWRBSWB', 'LND4PWR', '0.293', '', '', 'Powerplant for Switchgrass Biofuel', '1'],
  ['PWRBCWB', 'LND4PWR', '0.293', '', '', 'Powerplant for Clearwood Biofuel', '1']
  ]

Powertech_attributes = {
    'Power plant description.': {},
    'InputActivityRatio': {}, 
    'WaterWithdrawals': {},
    'WaterReturnedAsSurfaceWater': {}
}

# List of power plants.
""" 
PLANTCODE:  ['Power plant description.', InputActivityRatio, WaterWithdrawals, WaterReturnedAsSurfaceWater]
"""
PowerPlants= {
  'PWRNGSB': ['Aggregated Natural gas power stations on grid B.', 2.7, 0.0227, 0.0225],
  'PWRWNDB':  ['wind plant on B grid, PR Region (144 MW).', 3.33, 0, 0], 
  'PWRBIOB':  ['Bio plant on B grid, PR Region (49 MW).', 2.85, 0.0291, 0.0288],
  'PWRSOLB':  ['Solar plant on B grid, K-Se Region (1 MW).', 4.34, 0, 0],
  'PWRGEOB':  ['Geothermal plant (Steam technology) on B grid, (? MW).', 6.67, 0.0021, 0.0006],
  'PWRURNB':  ['Nuclear plant (OT technology) on B grid, (? MW).', 3.0, 0.0378, 0.0375],
  'PWRHYDB':  ['Hydro Plants on B grid, (? MW).', 1.0, 0, 0],
  'PWRBSWB':  ['Switchgrass Biofuel Powerplant on B grid.', 3.72, 0.0291, 0.0288], # EL_20251125 added
  'PWRBCWB':  ['Switchgrass Biofuel Powerplant on B grid.', 3.72, 0.0291, 0.0288] # EL_20251125 added
}


# Emissions to be tracked in the model.
Emissions= {
  'CO2': ['Carbon dioxide emissions.','#00cc66'],
  'CH4_FER': ['Methane emissions from enteric fermentation', '#ff6600'],#Given in MtonCH4 will fix
  'CH4_MAN': ['Methane emissions from manure management', '#9933cc'],#Given in MtonCH4 will fix
  'N2O_MAN': ['Nitrous oxide emissions from manure management', '#9933cc'],#Given in MtonN2O will fix
  'N2O_DIR': ['Direct nitrous oxide emissions from agricultural soils', '#9933cc'], #Given in MtonCO2e
  'N2O_IND': ['Indirect nitrous oxide emissions from agricultural soils', '#9933cc'], #Given in MtonCO2e
}


# Crop yield factors for calibrating the model.  Codes here must match crop codes in the land use data.
# -------->>>>>>>>>>>>>>>>>>> needs to be automated
CropYieldFactors= {
  'ALF': 0.95,
  'BAR': 0.95,
  'MAI': 0.95,
  'OAT': 0.95,
  'OTH': 0.95,
  'PEA': 0.95,
  'PTW': 0.95,
  'RAP': 0.95,
  'RYE': 0.95,
  'WHE': 0.95,
  'SWI': 0.95 # EL_20251125 added
}

Limitations={
  'FUEL': "'INFLOW' fuel and the associated activity ratios are handled separately.",
  'STORAGE_SETS': "Storage algorithm associated explicit sets are handled separately."
}

units= {
    "capacity": "Capacity (Gigawatts)",
    "energy_pj": "Generation (Petajoules)",
    "energy_gwh": "Generation (GWh)",
    "emission": "Million Tonnes of CO2",
    "landuse": "Thousand Sq. Km per Petajoules",
    "demand": "Petajoules",
    "consumption_pj": "Petajoules",
    "consumption_gwh": "GWh"
}

plot_technologies = {
    "capacity": ["PWRWND", "PWRNGS", "PWRBIO", "PWRHYD", "PWRSOL", "PWRGEO", "PWRURN", "CCS", "HDG", "IMPPWR"],
    "emission": ["DEMAGR", "DEMCOM", "DEMIND", "DEMRES", "DEMTRA", "CCS"],
    "energy": ["PWRBIO", "PWRHYD", "PWRNGS", "PWRSOL", "PWRWND", "PWRGEO", "PWRURN", "CCS", "IMPPWR"],
    "landuse": ["LNDAGRBC1C01", "LNDAGRBC1C02", "LNDAGRBC1C03", "LNDAGRBC1C04", "LNDAGRBC1C05", "LNDAGRBC1C06", "LNDAGRBC1C07"]
}

# --------------------------------------------------------------------------
# Livestock Modelling
# --------------------------------------------------------------------------

Livestock_code: str = 'LVS'

LivestockProduce: dict = {
    'BEF': 'Beef',
    'MIL': 'Milk',
    'PIG': 'Swine',
    'SHP': 'Sheep',
}

LivestockPathways = {
    'BEFN': {'label': 'Beef (natural pasture)',    'produce': 'BEF', 'pasture': 'N'},
    'BEFC': {'label': 'Beef (cultivated pasture)', 'produce': 'BEF', 'pasture': 'C'},
    'MIL':  {'label': 'Dairy', 'produce': 'MIL', 'pasture': None},
    'PIG':  {'label': 'Swine', 'produce': 'PIG', 'pasture': None},
    'SHP':  {'label': 'Sheep', 'produce': 'SHP', 'pasture': None},
}

# Stocking density (1000 heads per 1000 sq km)
LivestockStockingDensity = {
    'BEFN': 36.51,    
    'BEFC': 48.77,    
    'MIL':  224.817,  
    'PIG':  7126.02,  #intensive
    'SHP':  419.22
    ,   
}

# Commodity yield: ktons per 1000 heads
LivestockCommodityYield = {
    'BEF': 0.3888,   
    'MIL': 5.472,
    'PIG': 0.885,
    'SHP': 0.089,
}

# Land area: 1000 sq km, fixed at base year
LivestockLandArea = {
    'BEFN': 7.102,
    'BEFC': 1.013,
    'MIL':  0.709,
    'PIG': 0.0124,
    'SHP':  0.153,
}

# Water-balance parameters for livestock land use from GeoCLEWs
LivestockEvapotranspirationPercent = {
    'BEFN': 0.694,   
    'BEFC': 0.694,   
    'MIL':  0.694,   
    'PIG':  0.694,   
    'SHP':  0.694,   
}

# Fraction of excess water
# Taken from Geoclews, values for grassland
LivestockGroundwaterPercentofExcess = {
    'BEFN': 0.051,   # GRS proxy
    'BEFC': 0.051,   # GRS proxy
    'MIL':  0.051,   # GRS proxy
    'PIG':  0.072,   # BLT proxy
    'SHP':  0.051,   # GRS proxy
}

# BC1 area weighted precipitation from Geoclews
LivestockRegionalPrecipitation = {
    'BC1': 0.9682,  
}


# --------------------------------------------------------------------------
# Agrivoltaic Modelling
# --------------------------------------------------------------------------
#

Agrivoltaic_code: str = 'AGV'

# One entry per agrivoltaic pathway. Pathway key is the short code used
# in tech/fuel identifiers (e.g. LNDAGV{pathway}{region}). Keep it short
# — typically the crop code unless multiple pathway variants per crop are
# needed (e.g. fixed vs. tracking panels).
AgrivoltaicPathways = {
    'MAI': {'label': 'Agrivoltaic Maize',        'crop': 'MAI'},
    'WHE': {'label': 'Agrivoltaic Wheat',        'crop': 'WHE'},
    'PTW': {'label': 'Agrivoltaic White Potato', 'crop': 'PTW'},
}

# Crop yield derate under moderate-shade agrivoltaic geometry.
# Per-crop values from primary AGV field and simulation literature;
# see thesis Section 3.X for full derivation.
#
# References:
#   MAI: Ramos-Fuentes et al. (2023) 7.7% reduction at 20-25% shade;
#        Amaducci et al. (2018) maize under Agrovoltaico simulation
#   WHE: Weselek et al. (2021) Heggelbach pilot +2.7% in 2018;
#        Dupraz et al. (2011) STICS modelling, LER 1.35-1.7
#   PTW: Weselek et al. (2021) +11% potato in 2018;
#        Colauzzi et al. (2026) 4-year Italian trial -12% at ST1
#   Cross-cutting: Laub et al. (2022) meta-analysis yield response
AgrivoltaicCropYieldFactor = {
    'MAI': 1,
    'WHE': 1,
    'PTW': 1,
}

# Shade derate applied to BOTH irrigation demand and evapotranspiration.
# Marrou et al. (2013) half-density wheat cycle: 0.68 PAR transmission.
# Weselek et al. (2021) Heggelbach pilot: 0.70 mean PAR.
# Single value across crops; crop-specific refinement deferred.
AgrivoltaicShadeFactor = 0.70

# Solar resource incident on AGV land, BC-wide area-weighted.
# Natural Resources Canada (NRCan) annual horizontal global insolation
# for BC agricultural areas: ~3.4 kWh/m^2/day annual average.
# Conversion: 3.4 kWh/m^2/day x 365 d/yr x 1314 = 4,470 PJ per 1000 km^2 yr.
# Applied uniformly across GeoCLEWs clusters; PV resource heterogeneity
# is smaller than crop-yield heterogeneity, and Saedi (2023) cluster
# assignments do not preserve raster-cell mappings needed for area-
# weighted cluster-level PV averaging.
AgrivoltaicSolarInput = {
    'MAI': 4470.0,
    'WHE': 4470.0,
    'PTW': 4470.0,
}

# Electricity yield from single-axis-tracking bifacial agrivoltaic
# systems on BC agricultural land.
# Source: Jamil, Bonnington & Pearce (2023, Sustainability 15:3228)
# SAM simulation of Heliene 72M-405 G1 bifacial modules with 20 m
# inter-row spacing for farm-equipment access. BC area-weighted
# average across 750 kWh/kWp and 950 kWh/kWp zones.
# Derivation: 4,007 GWh/yr on 1% of ~25,500 km^2 BC cropland
# = 56 PJ per 1000 km^2 per year.
AgrivoltaicElectricityYield = {
    'MAI': 56.0,
    'WHE': 56.0,
    'PTW': 56.0,
}

# EL_225115 added this to identify committed sites
# type_of_techn : [name,contact_capacity(GW),commission_year]
committed_sites = {
    "PWRWNDB": [
        ["Stewart Creek Wind Project", 0.1999, 2031],
        ["Nithi Mountain Wind Project", 0.1999, 2031],
        ["Highland Valley Wind Project", 0.1972, 2032],
        ["Taylor Wind Project", 0.2000, 2032],
        ["K2 Wind Project", 0.1596, 2032],
        ["Nilhts'i Ecoener Project (Formerly Hixon Wind Power Project)", 0.1404, 2032],
        ["Brewster Wind Project", 0.1972, 2032],
        ["Mount Mabel Wind Project", 0.1428, 2032],
        ["Boulder and Elkhart Wind Project", 0.0944, 2032]
    ],

    "PWRSOLB": [
        ["ShTSaQU Solar Project", 0.104, 2030]
    ]
}
