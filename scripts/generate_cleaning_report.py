import pandas as pd
import os
from analyze_csv import get_column_summary
from gpt_advisor import get_cleaning_advice

# Load dataset
DATA_PATH = "data/raw/sample_messy.csv"
OUTPUT_PATH = "logs/cleaning_recommendations.md"

def generate_cleaning_report(csv_path):
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)
    summary = get_column_summary(df)

    print(f"\nGenerating GPT cleaning advice for: {csv_path}\n")

    report_lines = [f"# Cleaning Recommendations for `{os.path.basename(csv_path)}`\n"]

    for column, stats in summary.items():
        print(f"Analyzing column: {column}...")

        try:
            suggestion = get_cleaning_advice(column, stats)
        except Exception as e:
            suggestion = f"Error getting GPT advice: {e}"

        # Print to terminal
        print(f"\nGPT Suggestion for `{column}`:\n{suggestion}\n")

        # Append to report
        report_lines.append(f"## `{column}`\n")
        report_lines.append("**Stats:**")
        for k, v in stats.items():
            report_lines.append(f"- {k}: {v}")
        report_lines.append("\n**GPT Suggestion:**\n")
        report_lines.append(suggestion)
        report_lines.append("\n---\n")

    # Save to markdown
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\nSaved GPT cleaning report to: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_cleaning_report(DATA_PATH)
