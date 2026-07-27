import pandas as pd
from pathlib import Path

BASE_PATH = Path("data/clean excel files")

def clean_cols(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    return df


def load_all_data():

    files = [
        ("c06_2026_clean.xlsx", "ACTUAL"),
        ("BDG2026_v4_clean.xlsx", "BDG"),
        ("fcst1_2026_clean.xlsx", "FCS"),
        ("LY25_clean.xlsx", "LY"),
    ]

    dfs = []

    for file, scenario in files:
        df = pd.read_excel(BASE_PATH / file)

        df = clean_cols(df)

        # CUSTOMER NORMALIZATION
        if "customer_merge" in df.columns:

            df["customer_merge"] = (
                df["customer_merge"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            df["customer_merge"] = df["customer_merge"].replace({
                "SDF": "SAME DEUTZ-FAHR DEUTSCHLAND GMBH",
                "ATLAS COPCO_NC": "ATLAS COPCO",
                "YANMAR ITALY": "YANMAR"
            })

        df["scenario"] = scenario

        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)
