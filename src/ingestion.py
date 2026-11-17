#Contributor: Teammate 2/smrithics26
# Reviewer: Teammate 3/@teammate3_handle

"""Functions for reading raw grid CSV data and checking physical bounds."""

import csv
from datetime import datetime
from pathlib import Path

# Q1: 5 official regional load dispatch center regions in India
ALLOWED_REGIONS = {
    "Northern",
    "Western",
    "Southern",
    "Eastern",
    "North-Eastern",
}

GEN_COLUMNS = [
    "Thermal_Gen_MU",
    "Nuclear_Gen_MU",
    "Hydro_Gen_MU",
    "Total_Gen_MU",
    "Peak Demand_MW",
    "Deficit_MW",
]


def check_grid_row(row, line_no=0):
    """Validate Q1 physical bounds and region names for a single CSV row."""
    region = row.get("Region", "").strip()
    if region not in ALLOWED_REGIONS:
        return False, f"Line {line_no}: Invalid region '{region}'"

    for col in GEN_COLUMNS:
        try:
            val = float(row.get(col, 0))
            if val < 0:
                return False, f"Line {line_no}: Negative generation value {val} in {col}"
        except (ValueError, TypeError):
            return False, f"Line {line_no}: Non-numeric value in {col}"

    return True, "Valid"