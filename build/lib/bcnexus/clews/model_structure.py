#  M Eliasinul Islam (EL), 2024

# ____________________________________________
# This file defines the constants of clews model building script.
# Based on the data in this file, clewsy builds the SETS, InputActivityRatio and OutputActivityRatio


Model= 'BC Clews Model V2.0'
clews_builder_config_path='config/clews_builder.yaml'

# The OSeMOSYS regions in the model.  
# For most models, leave this as REGION1 as CLEWs regions are built with technologies and commodities rather than OSeMOSYS regions.
Regions= {'REGION1': ['BC','#000000']}

# Add or reduce the model time horizon as needed.
snapshot={ 
  'start': 2021,
  'end': 2050
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
    'IND': 'Industry',
    'RES': 'Residential',
    'COM': 'Commercial',
    'AGR': 'Agricultural',
    'TRA': 'Transport',
    'OTH': 'Other',
    'BIO': 'Biomass',
    'COA': 'Coal',
    'CRU': 'Crude oil',
    'DSL': 'Diesel',
    'ELCB01': 'Electricity from power plants in region B',
    'ELCB02': 'Electricity from transmission in region B',
    'GSL': 'Gasoline',
    'HFO': 'Heavy fuel oil',
    'NGS': 'Natural gas',
    'KER': 'Kerosene',
    'LPG': 'LPG',
    'OHC': 'Other hydrocarbons',
    'GEO': 'Geothermal',
    'HYD': 'Hydropower',
    'SOL': 'Solar',
    'WND': 'Wind',
    'CHC': 'Charcoal',
    'PCK': 'Petroleum coke',
    'JFL': 'Jet fuel',
    'URN': 'Uranium',
    'ALF': 'Alfalfa',
    'WHE': 'Wheat',
    'RAP': 'Rapeseed',
    'OAT': 'Oat',
    'BRL': 'Barley',
    'PEA': 'Dry pea',
    'MAI': 'Maize',
    'RYE': 'Rye',
    'PTW': 'White potato'  #corrected from 'PWT'
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
  'OTH': 'Other agricultural land'
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
  'OTH': 0.694
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
  'OTH': 0.051
}

# Percent of excess water (Irrigation + Precipitation - Evapotranspiration) that returns as groundwater.
# for croplands.  Rest returns as Runoff.
GroundwaterPercentofExcess= 0.051

# Defines the final demand fuels in the model, and the sectors they are used in.
EndUseFuels= {
  'IND': ['DSL', 'BIO', 'NGS', 'ELCB02'],
  'RES': ['KER', 'BIO', 'NGS', 'ELCB02'],
  'COM': ['KER', 'BIO', 'NGS', 'ELCB02'],
  'AGR': ['DSL', 'NGS', 'ELCB02'],
  'TRA': ['GSL', 'DSL', 'HFO', 'JFL', 'BIO', 'NGS', 'LPG', 'ELCB02']
}

# Imports and exports - add and remove fuels as needed to represent a given region.
ImportFuels= ['JFL', 'LPG', 'GSL', 'KER', 'DSL', 'HFO','CRU', 'COA'] 
ExportFuels= ['NGS',  'BIO','CRU', 'COA']

# Domestically available fuels.
DomesticMining= ['NGS', 'URN','CRU', 'COA']
DomesticRenewables= ['WND', 'HYD', 'BIO', 'SOL', 'GEO']

# Transformation technologies that connect parts of the CLEWs model together.  
    # For example, power transmission between grids, oil refineries, biofuel plants, etc.
    # Note:  These technologies cannot create fuels but assume that their fuels are created elsewhere (either in the DomesticMining, DomesticRenewables or ImportFuels).

"""
______________________________________________________________________________________________
>>>>>>>>>>>>>>>>>>>>>>>>>>>> Structure: <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
['TECHNOLOGY', 'INPUTFUEL', 'IAR', 'OUTPUTFUEL', 'OAR', 'Name', 'ModeOfOperation']

# One can use multiple lines for a single technology to create additional input or output activity ratios for a given technology (such as the refinery example below).

"""
TransformationTechnologies= [
# 90% efficient grid distribution system:
  ['PWRTRNB01', 'ELCB01', '1.11', 'ELCB02', '1', 'Power transmission grid B', '1'],
  
# Example of land use impact of a power generation technology:
# ['power plant name and discription', 'input fuel', 'input activity ratio: for 1PJ of output how much land will be needded', 'output fuel- leave it blank', 'output activity raio- leave it blank', 'discription-leave it blank', 'Mode of operation'],
 
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
}

# Emissions to be tracked in the model.
Emissions= {
  'CO2': ['Carbon dioxide emissions.','#00cc66']
}

# Crop yield factors for calibrating the model.  Codes here must match crop codes in the land use data.
# -------->>>>>>>>>>>>>>>>>>> needs to be automated
CropYieldFactors= {
    'ALF': 0.95,
    'WHE': 0.95,
    'RAP': 0.95,
    'OAT': 0.95,
    'BAR': 0.95,    #corrected from 'BRL'
    'PEA': 0.95,
    'MAI': 0.95,
    'RYE': 0.95,
    'PTW': 0.95,
    'OTH': 0.95
}

Limitations={
  'STORAGE':'STORAGE set is being handled separately',
  'FUEL': 'Hydrobasin INFLOW fuel and the associated activity ratios are handled seprately.',
  'DAYSCRO' : 'SET representing Chronological day is handled separately.'
}