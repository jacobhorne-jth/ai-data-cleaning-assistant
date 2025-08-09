import pandas as pd
import os
import re
from dateutil import parser

CLEANED_OUTPUT = "data/cleaned/cleaned_output.csv"
CHANGE_LOG = "logs/cleaning_log.md"

def apply_cleaning_rules(df: pd.DataFrame, suggestions: dict):
    log_lines = ["# Auto-Cleaning Log (Safe Mode)\n"]
    original_len = len(df)

    for col in df.columns:
        if col not in suggestions:
            continue

        suggestion = suggestions[col].lower()
        series = df[col]
        changes = []

        # Fill missing values
        if "fill missing" in suggestion or "fill null" in suggestion:
            if pd.api.types.is_numeric_dtype(series):
                val = series.median()
                df[col] = series.fillna(val)
                changes.append(f"Filled nulls with median value: {val}")
            else:
                val = series.mode().iloc[0] if not series.mode().empty else "unknown"
                df[col] = series.fillna(val)
                changes.append(f"Filled nulls with mode: '{val}'")

        # Handle negative values
        if "negative" in suggestion and pd.api.types.is_numeric_dtype(series):
            neg_count = (series < 0).sum()
            df.loc[df[col] < 0, col] = series.median()
            changes.append(f"Replaced {neg_count} negative values with median")

        # Standardize emails
        if "email" in col.lower():
            invalid_mask = ~series.astype(str).str.contains(r"[^@]+@[^@]+\.[^@]+", na=False)
            fix_count = invalid_mask.sum()
            df.loc[invalid_mask, col] = "unknown@example.com"
            changes.append(f"Replaced {fix_count} invalid emails with placeholder")

        # More robust date cleaning — always apply to columns with "date" in name
        if "date" in col.lower():
            def try_parse_date(x):
                try:
                    return parser.parse(str(x)).date()
                except Exception:
                    return pd.NaT

            df[col] = df[col].apply(try_parse_date)
            nulls = df[col].isna().sum()
            changes.append(f"Parsed dates using dateutil.parser — {nulls} entries could not be parsed")

        # Handle non-numeric income/amount fields
        if "income" in col.lower() and "non-numeric" in suggestion:
            cleaned = pd.to_numeric(series, errors='coerce')
            nulls = cleaned.isnull().sum()
            df[col] = cleaned.fillna(cleaned.median())
            changes.append(f"Converted to numeric; replaced {nulls} invalid entries with median")

        # Remove duplicates (only full row dups)
        if "duplicate" in suggestion:
            before = len(df)
            df = df.drop_duplicates()
            after = len(df)
            removed = before - after
            changes.append(f"Removed {removed} duplicate rows")

        # Log changes
        if changes:
            log_lines.append(f"## {col}")
            for line in changes:
                log_lines.append(f"- {line}")
            log_lines.append("")

    final_len = len(df)
    log_lines.append(f"\nFinal row count: {final_len} (from original {original_len})")

    return df, "\n".join(log_lines)


# Optional: standalone run
if __name__ == "__main__":
    INPUT_CSV = "data/raw/sample_messy.csv"
    SUGGESTIONS_MD = "logs/cleaning_recommendations.md"

    if not os.path.exists(INPUT_CSV) or not os.path.exists(SUGGESTIONS_MD):
        print("Make sure the raw CSV and GPT suggestions file exist.")
        exit()

    df = pd.read_csv(INPUT_CSV)

    # Parse GPT suggestions from the .md file
    with open(SUGGESTIONS_MD, "r", encoding="utf-8") as f:
        lines = f.read().split("## ")
        suggestions = {}
        for block in lines[1:]:
            header, *rest = block.split("\n")
            col = header.strip("`").strip()
            suggestion_lines = [l for l in rest if not l.startswith("-")]
            text = "\n".join(suggestion_lines).strip()
            suggestions[col] = text

    cleaned_df, log = apply_cleaning_rules(df, suggestions)

    # Save cleaned file and log
    os.makedirs("data/cleaned", exist_ok=True)
    cleaned_df.to_csv(CLEANED_OUTPUT, index=False)
    with open(CHANGE_LOG, "w", encoding="utf-8") as f:
        f.write(log)

    print(f"Cleaned data saved to: {CLEANED_OUTPUT}")
    print(f"Cleaning log saved to: {CHANGE_LOG}")
