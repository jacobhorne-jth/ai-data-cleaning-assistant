import os
import pandas as pd
from pathlib import Path
from dateutil import parser

from analyze_csv import get_column_summary
from gpt_advisor import get_cleaning_advice
from auto_cleaner import apply_cleaning_rules

def clean_dates(df, column):
    def try_parse_date(x):
        try:
            return parser.parse(str(x)).date()
        except Exception:
            return pd.NaT
    df[column] = df[column].apply(try_parse_date)
    return df

def run_pipeline(input_csv_path):
    if not os.path.exists(input_csv_path):
        print(f"File not found: {input_csv_path}")
        return

    print(f"\nLoading: {input_csv_path}")
    df = pd.read_csv(input_csv_path)

    print("\nAnalyzing columns...")
    summary = get_column_summary(df)

    print("\nGetting GPT cleaning suggestions...")
    suggestions = {}
    md_lines = [f"# GPT Cleaning Suggestions for `{os.path.basename(input_csv_path)}`\n"]

    for column, stats in summary.items():
        print(f"Advising on: {column}")
        try:
            suggestion = get_cleaning_advice(column, stats)
            suggestions[column] = suggestion
        except Exception as e:
            suggestions[column] = f"Error: {e}"

        md_lines.append(f"## `{column}`\n")
        md_lines.append("**Stats:**")
        for k, v in stats.items():
            md_lines.append(f"- {k}: {v}")
        md_lines.append("\n**GPT Suggestion:**\n")
        md_lines.append(suggestions[column])
        md_lines.append("\n---\n")

    # Save Markdown summary
    os.makedirs("logs", exist_ok=True)
    md_path = "logs/cleaning_recommendations.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\nGPT suggestions saved to: {md_path}")

    # Auto-cleaning
    print("\nApplying safe cleaning rules...")
    cleaned_df, cleaning_log = apply_cleaning_rules(df, suggestions)

    # Fix join_date formatting if column exists
    if 'join_date' in cleaned_df.columns:
        print("Standardizing date format in 'join_date' column...")
        cleaned_df = clean_dates(cleaned_df, 'join_date')

    # Save cleaned output
    os.makedirs("data/cleaned", exist_ok=True)
    cleaned_path = "data/cleaned/cleaned_output.csv"
    cleaned_df.to_csv(cleaned_path, index=False)

    # Create combined file for Tableau comparison
    cleaned_path = Path("data/cleaned/cleaned_output.csv")
    if cleaned_path.exists():
        before = pd.read_csv("data/raw/sample_messy.csv")
        after = pd.read_csv(cleaned_path)

        before["Source"] = "Before"
        after["Source"] = "After"
        before["RowID"] = range(len(before))
        after["RowID"] = range(len(after))

        combined = pd.concat([before, after], ignore_index=True)
        combined.to_csv("data/cleaned/tableau_comparison.csv", index=False)
        print("Tableau comparison CSV saved to: data/cleaned/tableau_comparison.csv")

    # Save log
    log_path = "logs/cleaning_log.md"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(cleaning_log)

    print(f"Cleaned dataset saved to: {cleaned_path}")
    print(f"Cleaning log saved to: {log_path}")
    print("\nCleaning pipeline complete.")

if __name__ == "__main__":
    path = input("Enter path to your CSV file: ").strip()
    run_pipeline(path)
    