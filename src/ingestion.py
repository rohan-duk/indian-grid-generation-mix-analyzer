
# Contributor: Teammate 2 / @smrithics26
# Reviewer: Teammate 3 / @teammate3_handle

"""Functions for reading raw grid CSV data and checking physical bounds."""

import csv
from pathlib import Path

# Q1: Five official regional load dispatch center regions in India
ALLOWED_REGIONS = {
    "Northern",
    "Western",
    "Southern",
    "Eastern",
    "North-Eastern",
}

# Columns that must contain non-negative numeric values
GEN_COLUMNS = [
    "Thermal_Gen_MU",
    "Nuclear_Gen_MU",
    "Hydro_Gen_MU",
    "Total_Gen_MU",
    "Peak_Demand_MW",
    "Deficit_MW",
]


def check_grid_row(row, line_no=0):
    """Validate physical bounds and region names for a single CSV row."""

    region = row.get("Region", "").strip()

    if region not in ALLOWED_REGIONS:
        return False, f"Line {line_no}: Invalid region '{region}'"

    for col in GEN_COLUMNS:
        try:
            val = float(row.get(col, 0))

            if val < 0:
                return False, (
                    f"Line {line_no}: Negative value {val} in {col}"
                )

        except (ValueError, TypeError):
            return False, (
                f"Line {line_no}: Non-numeric value in {col}"
            )

    return True, "Valid"


def clean_grid_dataset(raw_path, clean_path, audit_log_path):
    """Clean raw CSV data, export valid rows, and log rejected records."""

    raw_path = Path(raw_path)
    clean_path = Path(clean_path)
    audit_log_path = Path(audit_log_path)

    # Create output directories if they do not exist
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    valid_count = 0
    rejected_count = 0
    rejected_logs = []

    # Read the raw CSV file
    with open(raw_path, mode="r", encoding="utf-8", newline="") as infile:

        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        valid_rows = []

        for idx, row in enumerate(reader, start=2):
            total += 1

            is_valid, reason = check_grid_row(row, line_no=idx)

            if is_valid:
                valid_count += 1
                valid_rows.append(row)

            else:
                rejected_count += 1
                rejected_logs.append(reason)

    # Write valid records to the cleaned CSV file
    if fieldnames:
        with open(clean_path, mode="w", encoding="utf-8", newline="") as outfile:

            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(valid_rows)

    # Write rejected records to the audit log
    with open(audit_log_path, mode="w", encoding="utf-8") as log_file:

        log_file.write(
            "\n".join(rejected_logs) +
            ("\n" if rejected_logs else "")
        )

    # Return dataset cleaning statistics
    return {
        "total": total,
        "valid": valid_count,
        "rejected": rejected_count,
    }
