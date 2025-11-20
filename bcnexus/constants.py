base_load_year = 2021
result_type = {
    "otoole": {
        "year": "YEAR",
        "technology": "TECHNOLOGY"
    },
    "cloud_results": {
        "year": "y",
        "technology": "t"
    }
}

title = "BC Combined Modelling"
demand_data = "data/downloaded_data/CODERS/data-pull/demand"
demand_scenarios = {
    'CM': "Current Measures (Canada Energy Future 2023)",
    'CNZ': "Canadian Net Zero (Canada Energy Future 2023)",
    'GNZ': "Global Net Zero (Canada Energy Future 2023)"
}
plot_files = {
    "demand": ["BC_end_use_demand_Current Measures.csv", "BC_end_use_demand_Canada Net-zero.csv", "BC_end_use_demand_Global Net-zero.csv"],
    "capacity": ["NewCapacity.csv", "TotalCapacityAnnual.csv"],
    "generation": ["TotalTechnologyAnnualActivity.csv"],
    "consumption": ["UseByTechnology.csv"],
    "emission": ["AnnualEmissions.csv", "AnnualTechnologyEmission.csv"],
    "landuse": ["RateOfProductionByTechnologyByMode.csv"]
}

units_mapping = {
    "capacity": "Capacity (Gigawatts)",
    "generation_pj": "Generation (Petajoules)",
    "generation_gwh": "Generation (GWh)",
    "emission": "Million Tonnes of CO2",
    'capital_investment' : "Million $",
    "landuse": "Thousand Sq. Km per Petajoules",
    "demand": "Petajoules",
    "consumption_pj": "Petajoules",
    "consumption_gwh": "GWh"
}
emission_targets = {
    'years': [2030, 2040, 2050],
    'emissions_MTeCO2': [40, 25, 0]  # MTeCO2
}
emission_inventory={
    'years':[2021, 2022, 2023],
    'emissions_MTeCO2': [63.8,65.6,55.94] # MTeCO2
}
technologies = {
    "capacity": ["PWRWND", "PWRNGS", "PWRBIO", "PWRHYD", "PWRSOL", "PWRGEO", "PWRURN", "CCS", "HDG", "IMPPWR","BATTERY_STORAGE"],
    "emission": ["DEMAGR", "DEMCOM", "DEMIND", "DEMRES", "DEMTRA", "CCS"],
    "energy": ["PWRBIO", "PWRHYD", "PWRNGS", "PWRSOL", "PWRWND", "PWRGEO", "PWRURN", "CCS", "IMPPWR","BATTERY_STORAGE"],
    "landuse": ["LNDAGRBC1C01", "LNDAGRBC1C02", "LNDAGRBC1C03", "LNDAGRBC1C04", "LNDAGRBC1C05", "LNDAGRBC1C06", "LNDAGRBC1C07"]
}

end_use_fuels = ["BIO", "DSL", "ELCB02", "GSL", "HDG", "HFO", "JFL", "LPG", "NGS", "RPP"]

sector_mapping = {
    "all": {
        "IND": "Industrial",
        "COM": "Commercial",
        "RES": "Residential",
        "TRA": "Transport",
        "CRP": "Crop Production",
        "LND": "Land Use",
        "PUB": "Public Services"
    },
    "power": {
        "IND": "Industrial",
        "COM": "Commercial",
        "RES": "Residential",
        "TRA": "Transport"
    }
}

filenames_mapping = {
    "NewCapacity.csv": "New Capacity",
    "TotalCapacityAnnual.csv": "Total Capacity",
    "AnnualEmissions.csv": "System Emission",
    "AnnualTechnologyEmission.csv": "Sectoral Emission",
    "TotalTechnologyAnnualActivity.csv": "Generation",
    "RateOfProductionByTechnologyByMode.csv": "Land-use (clusters of BC)",
    "UseByTechnology.csv": "Consumption",
    "BC_end_use_demand_Current Measures.csv": "Current Measures",
    "BC_end_use_demand_Canada Net-zero.csv": "Canada Net-zero",
    "BC_end_use_demand_Global Net-zero.csv": "Global Net-zero"
}

custom_colors = {
    "PWRWND": "#87CEEB",  # Sky Blue for Wind
    "PWRNGS": "#FFA07A",  # Light Salmon for Natural Gas
    "PWRBIO": "#228B22",  # Forest Green for Biomass/Biofuel
    "PWRHYD": "#4682B4",  # Steel Blue for Hydro
    "PWRSOL": "#FFD700",  # Gold for Solar
    "PWRGEO": "#8B4513",  # Saddle Brown for Geothermal
    "PWRURN": "#808080",  # Gray for Nuclear
    "IMPPWR": "#FF4500",  # Orange Red for Power Import
    "EXPPWR": "#32CD32",  # Lime Green for Power Export
    "PWRTRN": "#000000",  # Black for Transmission Grid
    "BATTERY_STORAGE" : 'lightgreen',

    "IMP": "#FF4500",  # Orange Red for Import
    "CCS": "#2F4F4F",  # Dark Slate Gray for Carbon Capture and Storage
    "HDG": "#1E90FF",  # Dodger Blue for Hydrogen
    "BIO": "#6B8E23",  # Olive Drab for Biomass
    "DSL": "#8B0000",  # Dark Red for Diesel
    "ELCB02": "#0000FF",  # Blue for Electricity
    "GSL": "#FF6347",  # Tomato for Gasoline
    "HFO": "#8B4513",  # Saddle Brown for Heavy Fuel Oil
    "HYD": "#4682B4",  # Steel Blue for Hydro
    "JFL": "#00008B",  # Dark Blue for Jet Fuel
    "LPG": "#FF69B4",  # Hot Pink for Liquefied Petroleum Gas
    "NGS": "#FFA07A",  # Light Salmon for Natural Gas
    "RPP": "#DAA520",  # Goldenrod for Refined Petroleum Products

    "WTRSURBC1": "#1E90FF",  # Dodger Blue for Surface Water
    "SOL": "#FFD700",  # Gold for Solar
    "WND": "#87CEEB",  # Sky Blue for Wind
    "AGR": "#32CD32",  # Lime Green for Agricultural
    "COM": "#4682B4",  # Steel Blue for Commercial
    "IND": "#708090",  # Slate Gray for Industrial
    "RES": "#FFB6C1",  # Light Pink for Residential
    "TRA": "#FF8C00",  # Dark Orange for Transport
    "LNDAGRBC1C01": "#32CD32",  # Lime Green for Land resource - Cluster 1
    "LNDAGRBC1C02": "#4682B4",  # Steel Blue for Land resource - Cluster 2
    "LNDAGRBC1C03": "#FFD700",  # Gold for Land resource - Cluster 3
    "LNDAGRBC1C04": "#FF8C00",  # Dark Orange for Land resource - Cluster 4
    "LNDAGRBC1C05": "#FFB6C1",  # Light Pink for Land resource - Cluster 5
    "LNDAGRBC1C06": "#6B8E23",  # Olive Drab for Land resource - Cluster 6
    "LNDAGRBC1C07": "#808080"   # Gray for Land resource - Cluster 7
}

colors_name_mapping = {
    "Wind": "#DDB3F9",
    "Natural Gas": "#D27A78",
    "Biomass/Biofuel": "#5BAB59",
    "Hydro": "#86B4D8",
    "Solar": "#FEE566",
    "Geothermal": "#B067B3",
    "Nuclear": "gray",
    "Carbon Capture and Storage": "#FF6347",  # Tomato
    "Hydrogen": "#00FFFF",  # Aqua
    "Biomass": "#A52A2A",  # Brown
    "Diesel": "#FFA500",  # Orange
    "Electricity": "#008000",  # Green
    "Gasoline": "#DC143C",  # Crimson
    "Heavy Fuel Oil": "#800000",  # Maroon
    "Jet Fuel": "#00008B",  # DarkBlue
    "Liquefied Petroleum Gas": "#FF1493",  # DeepPink
    "Surface Water": "#4169E1",  # RoyalBlue
    "Refined Petroleum Products": "#B8860B",  # DarkGoldenRod,
    "Agricultural": "#C57F7B",
    "Commercial": "#65B465",
    "Industrial": "#B3B3B3",
    "Residential": "#87B4D7",
    "Transport": "#676767",
    "Land resource - Cluster 1": "#DDB3F9",
    "Land resource - Cluster 2": "#D27A78",
    "Land resource - Cluster 3": "#5BAB59",
    "Land resource - Cluster 4": "#86B4D8",
    "Land resource - Cluster 5": "#FEE566",
    "Land resource - Cluster 6": "#B067B3",
    "Land resource - Cluster 7": "gray"
}

legend_labels = {
    "PWRWND": "Wind",
    "PWRNGS": "Natural Gas",
    "PWRBIO": "Biomass/Biofuel",
    "PWRHYD": "Hydro",
    "PWRSOL": "Solar",
    "PWRGEO": "Geothermal",
    "PWRURN": "Nuclear",
    "IMPPWR": "Power Import",
    "PWRTRN" : "Transmission Grid",
    "EXPPWR": "Power Export",
    "BATTERY_STORAGE" : "Battery Storage",
    "CCS": "Carbon Capture and Storage",
    "HDG": "Hydrogen",
    "BIO": "Biomass",
    "DSL": "Diesel",
    "ELCB02": "Electricity",
    "GSL": "Gasoline",
    "HFO": "Heavy Fuel Oil",
    "HYD": "Hydro",
    "JFL": "Jet Fuel",
    "LPG": "Liquefied Petroleum Gas",
    "NGS": "Natural Gas",
    "RPP": "Refined Petroleum Products",
    "WTRSURBC1": "Surface Water",
    "SOL": "Solar",
    "WND": "Wind",
    "RES": "Residential",
    "IND": "Industrial",
    "TRA": "Transport",
    "AGR": "Agricultural",
    "COM": "Commercial",
    "DEMRES": "Residential",
    "DEMIND": "Industrial",
    "DEMTRA": "Transport",
    "DEMAGR": "Agricultural",
    "DEMCOM": "Commercial",
    "LNDAGRBC1C01": "Land resource - Cluster 1",
    "LNDAGRBC1C02": "Land resource - Cluster 2",
    "LNDAGRBC1C03": "Land resource - Cluster 3",
    "LNDAGRBC1C04": "Land resource - Cluster 4",
    "LNDAGRBC1C05": "Land resource - Cluster 5",
    "LNDAGRBC1C06": "Land resource - Cluster 6",
    "LNDAGRBC1C07": "Land resource - Cluster 7"
}


name_mapping = {
    "FUEL": {
        "AGRDSL": "Diesel input in Agriculture",
        "AGRELCB02": "Electricity input in Agriculture",
        "AGRNGS": "Natural Gas input in Agriculture",
        "AGRWATBC1": "Agricultural water for irrigation",
        "BIO": "Biomass",
        "COA": "Coal",
        "COMBIO": "Biomass input in Commercial",
        "COMELCB02": "Electricity input in Commercial",
        "COMKER": "Kerosene input in Commercial",
        "COMNGS": "Natural Gas input in Commercial",
        "CRPALF": "Crop Alfalfa",
        "CRPBRL": "Crop Barley",
        "CRPMAI": "Crop Maize",
        "CRPOAT": "Crop Oats",
        "CRPOTH": "Crop Other",
        "CRPPEA": "Crop Peas",
        "CRPPTW": "Crop Potatoes",
        "CRPRAP": "Crop Rapeseed",
        "CRPRYE": "Crop Rye",
        "CRPWHE": "Crop Wheat",
        "CRU": "Crude Oil",
        "DSL": "Diesel",
        "ELCB01": "Electricity from power plants",
        "ELCB02": "Electricity from the transmission",
        "GEO": "Geothermal",
        "GSL": "Gasoline",
        "HFO": "Heavy Fuel Oil",
        "HYD": "Hydro",
        "INDBIO": "Biomass input in Industrial",
        "INDDSL": "Diesel input in Industrial",
        "INDELCB02": "Electricity input in Industrial",
        "INDNGS": "Natural Gas input in Industrial",
        "JFL": "Jet Fuel",
        "KER": "Kerosene",
        "LALFHIBC1": "Land resource commodity for crop combination Alfalfa Irrigation",
        "LALFHRBC1": "Land resource commodity for crop combination Alfalfa Rain-fed",
        "LALFIIBC1": "Land resource commodity for crop combination Alfalfa Irrigation",
        "LALFIRBC1": "Land resource commodity for crop combination Alfalfa Rain-fed",
        "LALFLRBC1": "Land resource commodity for crop combination Alfalfa Rain-fed",
        "LBARBC1": "Barren and sparsely vegetated land commodity in BC",
        "LBC1": "Land resource in BC1",
        "LBLTBC1": "Built-up land commodity in BC1",
        "LBRLHIBC1": "Land resource commodity for crop combination Barley Irrigation",
        "LBRLHRBC1": "Land resource commodity for crop combination Barley Rain-fed",
        "LBRLIIBC1": "Land resource commodity for crop combination Barley Irrigation",
        "LBRLIRBC1": "Land resource commodity for crop combination Barley Rain-fed",
        "LBRLLRBC1": "Land resource commodity for crop combination Barley Rain-fed",
        "LFORBC1": "Forest land commodity in BC1",
        "LGRSBC1": "Grassland and woodland commodity in BC1",
        "LMAIHIBC1": "Land resource commodity for crop combination Maize Irrigation",
        "LMAIHRBC1": "Land resource commodity for crop combination Maize Rain-fed",
        "LMAIIIBC1": "Land resource commodity for crop combination Maize Irrigation",
        "LMAIIRBC1": "Land resource commodity for crop combination Maize Rain-fed",
        "LMAILRBC1": "Land resource commodity for crop combination Maize Rain-fed",
        "LND4PWR": "Land density for power generation technology",
        "LOATHIBC1": "Land resource commodity for crop combination Oats Irrigation",
        "LOATHRBC1": "Land resource commodity for crop combination Oats Rain-fed",
        "LOATIIBC1": "Land resource commodity for crop combination Oats Irrigation",
        "LOATIRBC1": "Land resource commodity for crop combination Oats Rain-fed",
        "LOATLRBC1": "Land resource commodity for crop combination Oats Rain-fed",
        "LOTHBC1O": "The agricultural land commodity in BC1",
        "LOTHHIBC1": "Land resource commodity for crop combination Other Irrigation",
        "LOTHHRBC1": "Land resource commodity for crop combination Other Rain-fed",
        "LOTHIIBC1": "Land resource commodity for crop combination Other Irrigation",
        "LOTHIRBC1": "Land resource commodity for crop combination Other Rain-fed",
        "LOTHLRBC1": "Land resource commodity for crop combination Other Rain-fed",
        "LPEAHIBC1": "Land resource commodity for crop combination Peas Irrigation",
        "LPEAHRBC1": "Land resource commodity for crop combination Peas Rain-fed",
        "LPEAIIBC1": "Land resource commodity for crop combination Peas Irrigation",
        "LPEAIRBC1": "Land resource commodity for crop combination Peas Rain-fed",
        "LPEALRBC1": "Land resource commodity for crop combination Peas Rain-fed",
        "LPTWHIBC1": "Land resource commodity for crop combination Potatoes Irrigation",
        "LPTWHRBC1": "Land resource commodity for crop combination Potatoes Rain-fed",
        "LPTWIIBC1": "Land resource commodity for crop combination Potatoes Irrigation",
        "LPTWIRBC1": "Land resource commodity for crop combination Potatoes Rain-fed",
        "LPTWLRBC1": "Land resource commodity for crop combination Potatoes Rain-fed",
        "LRAPHIBC1": "Land resource commodity for crop combination Rapeseed Irrigation",
        "LRAPHRBC1": "Land resource commodity for crop combination Rapeseed Rain-fed",
        "LRAPIIBC1": "Land resource commodity for crop combination Rapeseed Irrigation",
        "LRAPIRBC1": "Land resource commodity for crop combination Rapeseed Rain-fed",
        "LRAPLRBC1": "Land resource commodity for crop combination Rapeseed Rain-fed",
        "LRYEHIBC1": "Land resource commodity for crop combination Rye Irrigation",
        "LRYEHRBC1": "Land resource commodity for crop combination Rye Rain-fed",
        "LRYEIIBC1": "Land resource commodity for crop combination Rye Irrigation",
        "LRYEIRBC1": "Land resource commodity for crop combination Rye Rain-fed",
        "LRYELRBC1": "Land resource commodity for crop combination Rye Rain-fed",
        "LWATBC1": "Water bodies commodity in BC1",
        "LWHEHIBC1": "Land resource commodity for crop combination Wheat Irrigation",
        "LWHEHRBC1": "Land resource commodity for crop combination Wheat Rain-fed",
        "LWHEIIBC1": "Land resource commodity for crop combination Wheat Irrigation",
        "LWHEIRBC1": "Land resource commodity for crop combination Wheat Rain-fed",
        "LWHELRBC1": "Land resource commodity for crop combination Wheat Rain-fed",
        "NGS": "Natural Gas",
        "PUBWATBC1": "Water lost to evapotranspiration",
        "PWRBIO": "Biomass input to Power",
        "PWRGEO": "Geothermal input to Power",
        "PWRHYD": "Hydro input to Power",
        "PWRNGS": "Natural Gas input to Power",
        "PWRSOL": "Solar input to Power",
        "PWRURN": "Uranium input to Power",
        "PWRWATBC1": "Water input to Power",
        "PWRWND": "Wind input to Power",
        "RESBIO": "Biomass",
        "RESELCB02": "Electricity input in Residential",
        "RESKER": "Kerosene input in Residential",
        "RESNGS": "Natural Gas input in Residential",
        "SOL": "Solar",
        "TRABIO": "Biomass input in the Transportation sector",
        "TRADSL": "Diesel input in the Transportation sector",
        "TRAELCB02": "Electricity input in the Transportation sector",
        "TRAGSL": "Gasoline input in the Transportation sector",
        "TRAHFO": "Heavy Fuel Oil input in the Transportation sector",
        "TRAJFL": "Jet Fuel input in the Transportation sector",
        "TRALPG": "Liquefied Petroleum Gas input in the Transportation sector",
        "TRANGS": "Natural Gas input in the Transportation sector",
        "URN": "Uranium",
        "WND": "Wind",
        "WTREVTBC1": "Water lost to evapotranspiration",
        "WTRGRCBC1": "Water lost to evapotranspiration",
        "WTRPRCBC1": "Agricultural water for irrigation",
        "WTRSURBC1": "Agricultural water for irrigation"
    }
}
    

mode_of_operation = {
    1: "ALFHI",
    2: "ALFII",
    3: "ALFHR",
    4: "ALFIR",
    5: "ALFLR",
    6: "BARHI",
    7: "BARII",
    8: "BARHR",
    9: "BARIR",
    10: "BARLR",
    11: "MAIHI",
    12: "MAIII",
    13: "MAIHR",
    14: "MAIIR",
    15: "MAILR",
    16: "OATHI",
    17: "OATII",
    18: "OATHR",
    19: "OATIR",
    20: "OATLR",
    21: "OTHHI",
    22: "OTHII",
    23: "OTHHR",
    24: "OTHIR",
    25: "OTHLR",
    26: "PEAHI",
    27: "PEAII",
    28: "PEAHR",
    29: "PEAIR",
    30: "PEALR",
    31: "PTWHI",
    32: "PTWII",
    33: "PTWHR",
    34: "PTWIR",
    35: "PTWLR",
    36: "RAPHI",
    37: "RAPII",
    38: "RAPHR",
    39: "RAPIR",
    40: "RAPLR",
    41: "RYEHI",
    42: "RYEII",
    43: "RYEHR",
    44: "RYEIR",
    45: "RYELR",
    46: "WHEHI",
    47: "WHEII",
    48: "WHEHR",
    49: "WHEIR",
    50: "WHELR",
    51: "Barren and sparsely vegetated land",
    52: "Forest land",
    53: "Grassland & woodland",
    54: "Built-up land",
    55: "Water bodies",
    56: "Other agricultural lands",
    57: "Storage Discharging Mode"
}