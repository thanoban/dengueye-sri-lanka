from pathlib import Path
import pandas as pd


# This finds the main project folder:
# D:\PROJECTS\AI_ML\Dengue_PredictionProject
PROJECT_ROOT = Path(__file__).resolve().parents[4]

# Folder where you put week1.csv, week2.csv, week3.csv...
INPUT_DIR = PROJECT_ROOT / "data" / "interim" / "cleaned_dengue" / "weekly_files"

# Final combined dengue CSV output
OUT_PATH = PROJECT_ROOT / "data" / "interim" / "cleaned_dengue" / "weekly_dengue_cases.csv"

REQUIRED_COLUMNS = [
    "year",
    "week",
    "start_date",
    "end_date",
    "region",
    "dengue_cases",
    "cumulative_cases",
    "source_file"
]


def main():
    if not INPUT_DIR.exists():
        raise FileNotFoundError(
            f"Folder not found: {INPUT_DIR}\n"
            "Create this folder and put your weekly CSV files inside it."
        )

    csv_files = sorted(INPUT_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in: {INPUT_DIR}")

    all_data = []

    print("CSV files found:")
    for file in csv_files:
        print("-", file.name)

    print()

    for file in csv_files:
        df = pd.read_csv(file)

        # Remove extra spaces from column names
        df.columns = df.columns.str.strip()

        # Check required columns
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]

        if missing_columns:
            raise ValueError(
                f"{file.name} is missing columns: {missing_columns}\n"
                f"Available columns: {list(df.columns)}"
            )

        # Keep only wanted columns
        df = df[REQUIRED_COLUMNS]

        # Clean text columns
        df["region"] = df["region"].astype(str).str.strip()
        df["source_file"] = df["source_file"].astype(str).str.strip()

        # Remove national total row if it exists
        df = df[df["region"].str.upper() != "SRILANKA"]

        # Convert numeric columns
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df["week"] = pd.to_numeric(df["week"], errors="coerce")
        df["dengue_cases"] = pd.to_numeric(df["dengue_cases"], errors="coerce")
        df["cumulative_cases"] = pd.to_numeric(df["cumulative_cases"], errors="coerce")

        # Remove invalid rows
        df = df.dropna(subset=["year", "week", "region", "dengue_cases"])

        df["year"] = df["year"].astype(int)
        df["week"] = df["week"].astype(int)
        df["dengue_cases"] = df["dengue_cases"].astype(int)
        df["cumulative_cases"] = df["cumulative_cases"].astype(int)

        all_data.append(df)

    # Combine all week CSV files into one dataframe
    combined = pd.concat(all_data, ignore_index=True)

    # Sort by time and region
    combined = combined.sort_values(["year", "week", "region"])

    # Check duplicate district-week rows
    duplicates = combined[
        combined.duplicated(subset=["year", "week", "region"], keep=False)
    ]

    if not duplicates.empty:
        print("WARNING: Duplicate rows found for year-week-region:")
        print(duplicates)
        print()

    print("Missing values:")
    print(combined.isna().sum())
    print()

    print("Summary:")
    print("Total rows:", len(combined))
    print("Unique regions:", combined["region"].nunique())
    print("Unique weeks:", combined[["year", "week"]].drop_duplicates().shape[0])
    print("Year range:", combined["year"].min(), "-", combined["year"].max())
    print("Week range:", combined["week"].min(), "-", combined["week"].max())
    print()

    print("Rows per week:")
    print(combined.groupby(["year", "week"]).size())
    print()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUT_PATH, index=False)

    print("Combined dengue dataset saved:")
    print(OUT_PATH)


if __name__ == "__main__":
    main()