#!/usr/bin/env python3
"""
Generate section configuration files for all California codes.
Creates skeleton section configs that can be updated with real data from leginfo.
"""

import json
from pathlib import Path

# All 29 California legal codes
CODES = {
    "BPC": "Business and Professions Code",
    "CIV": "Civil Code",
    "CCP": "Code of Civil Procedure",
    "COM": "Commercial Code",
    "CORP": "Corporations Code",
    "EDC": "Education Code",
    "ELEC": "Elections Code",
    "EVID": "Evidence Code",
    "FAM": "Family Code",
    "FIN": "Financial Code",
    "FGC": "Fish and Game Code",
    "FAC": "Food and Agricultural Code",
    "GOV": "Government Code",
    "HNC": "Health and Nursing Code",
    "HSC": "Health and Safety Code",
    "INS": "Insurance Code",
    "LAB": "Labor Code",
    "MVC": "Military and Veterans Code",
    "PEN": "Penal Code",
    "PROB": "Probate Code",
    "PCC": "Professional Conduct Code",
    "PRC": "Public Records Code",
    "PUC": "Public Utilities Code",
    "RTC": "Revenue and Taxation Code",
    "SHC": "Streets and Highways Code",
    "UIC": "Unemployment Insurance Code",
    "VEH": "Vehicle Code",
    "WAT": "Water Code",
    "WIC": "Welfare and Institutions Code",
}

CONFIG_DIR = Path(__file__).parent / "section_configs"
CONFIG_DIR.mkdir(exist_ok=True)

for code, name in CODES.items():
    config = {
        "code": code,
        "name": name,
        "note": "Section list is dynamically discovered from leginfo.legislature.ca.gov",
        "sections": [],
        "total_sections_estimated": 0,
        "divisions": []
    }

    config_file = CONFIG_DIR / f"{code.lower()}_sections.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Created {config_file}")

print(f"\nGenerated {len(CODES)} configuration files in {CONFIG_DIR}")
