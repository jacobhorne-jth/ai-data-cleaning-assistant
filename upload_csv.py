import pandas as pd
import os

def load_csv():
    # Step 1: Ask for file path
    path = input("Enter path to your CSV file: ").strip()

    # Step 2: Validate
    if not os.path.isfile(path):
        print("Error: File does not exist.")
        return None

    if not path.lower().endswith(".csv"):
        print("Error: Not a CSV file.")
        return None

    try:
        df = pd.read_csv(path)
        print(f"Successfully loaded CSV with {df.shape[0]} rows and {df.shape[1]} columns.\n")
        print("First few rows:")
        print(df.head())
        return df
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

# Run if this file is executed directly
if __name__ == "__main__":
    load_csv()
