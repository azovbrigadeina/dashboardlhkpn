import pandas as pd
import requests
from io import StringIO

SHEET_ID = "1nSVGjisOcYJp5a2XQsMm-Q9GM1u8BL_RM-T9YUbYJ48"
GID = "465025576"
GSHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

def check_columns():
    try:
        response = requests.get(GSHEET_CSV_URL, timeout=15)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        print("Columns in Google Sheet:")
        print(df.columns.tolist())
        print("\nFirst 5 rows:")
        print(df.head())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_columns()
