
import pandas as pd
import sys

def view_parquet(path: str):
    # 设置 pandas 不隐藏内容
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", None)

    print(f"\n=== Loading parquet: {path} ===\n")
    df = pd.read_parquet(path)

    print("=== DataFrame Info ===")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print("\nColumn names:")
    print(df.columns.tolist())

    print("\n=== dtypes ===")
    print(df.dtypes)

    print("\n=== FULL DATAFRAME ===")
    print(df)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python view_parquet.py <file.parquet>")
    else:
        view_parquet(sys.argv[1])
