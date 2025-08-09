import pandas as pd
import os

def get_column_summary(df: pd.DataFrame):
    column_report = {}

    for col in df.columns:
        series = df[col]
        summary = {}

        # Core stats
        summary["dtype"] = str(series.dtype)
        summary["missing_values"] = int(series.isnull().sum())
        summary["num_duplicates"] = int(series.duplicated().sum())
        summary["num_unique"] = int(series.nunique())
        summary["sample_values"] = series.dropna().astype(str).unique().tolist()[:5]

        # Type-specific quick checks (basic only)
        if pd.api.types.is_numeric_dtype(series):
            summary["min"] = series.min(skipna=True)
            summary["max"] = series.max(skipna=True)
            summary["mean"] = series.mean(skipna=True)
        elif pd.api.types.is_string_dtype(series):
            summary["avg_length"] = int(series.dropna().astype(str).apply(len).mean())

        column_report[col] = summary

    return column_report


if __name__ == "__main__":
    path = "data/raw/sample_messy.csv"

    if not os.path.exists(path):
        print(f"File not found: {path}")
        exit()

    df = pd.read_csv(path)
    report = get_column_summary(df)

    print("\nGeneral Column Summary:\n")
    for col, stats in report.items():
        print(f"{col}")
        for k, v in stats.items():
            print(f"   - {k}: {v}")
        print()
