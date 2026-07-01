"""
combine_results.py
------------------
Combines all OSeMOSYS result CSVs into a single wide-format file.
"""

import argparse
import pandas as pd
from pathlib import Path

# FIX: Added STORAGE, SEASON, DAYTYPE, and DAILYTIMEBRACKET to the index columns
INDEX_COLS = [
    "REGION", 
    "TECHNOLOGY", 
    "STORAGE", 
    "FUEL", 
    "EMISSION", 
    "SEASON", 
    "DAYTYPE", 
    "DAILYTIMEBRACKET", 
    "TIMESLICE", 
    "MODE_OF_OPERATION", 
    "YEAR"
]
SENTINEL = "__ALL__"


def load_result_file(filepath):
    df = pd.read_csv(filepath)
    param_name = filepath.stem

    if "VALUE" not in df.columns:
        print(f"  Skipping {param_name}: no VALUE column. Columns: {list(df.columns)}")
        return None

    present_index = [col for col in INDEX_COLS if col in df.columns]
    df = df[present_index + ["VALUE"]].rename(columns={"VALUE": param_name})

    for col in INDEX_COLS:
        if col not in df.columns:
            df[col] = SENTINEL

    for col in INDEX_COLS:
        df[col] = df[col].astype(str).replace({"nan": SENTINEL, "None": SENTINEL, "<NA>": SENTINEL, "": SENTINEL})

    dup_count = df.duplicated(subset=INDEX_COLS).sum()
    if dup_count > 0:
        print(f"  WARNING {param_name}: {dup_count} duplicate index rows. Aggregating with sum().")
        df = df.groupby(INDEX_COLS, as_index=False)[param_name].sum()

    return df[INDEX_COLS + [param_name]]


def combine_results(results_dir, output_path):
    results_dir = Path(results_dir)
    output_path = Path(output_path)

    csv_files = sorted(results_dir.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {results_dir}")
        return

    print(f"Found {len(csv_files)} result files in {results_dir}")

    combined = None
    for filepath in csv_files:
        print(f"  Processing: {filepath.name}")
        df = load_result_file(filepath)
        if df is None:
            continue
        if combined is None:
            combined = df
        else:
            combined = pd.merge(combined, df, on=INDEX_COLS, how="outer")

    if combined is None:
        print("No valid files were loaded.")
        return

    for col in INDEX_COLS:
        combined[col] = combined[col].replace(SENTINEL, pd.NA)

    sort_cols = [c for c in INDEX_COLS if c in combined.columns]
    combined = combined.sort_values(sort_cols, na_position="last").reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() in (".xlsx", ".xls"):
        if len(combined) > 1048575:
            print(f"  WARNING: {len(combined):,} rows exceeds Excel limit.")
        combined.to_excel(output_path, index=False, engine="openpyxl")
    else:
        combined.to_csv(output_path, index=False)

    print(f"\nDone. Saved to: {output_path}")
    print(f"   Rows: {len(combined):,}, Columns: {len(combined.columns)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results_dir", type=str, required=True)
    parser.add_argument("--output", type=str, default="results_combined.csv")
    args = parser.parse_args()
    combine_results(args.results_dir, args.output)