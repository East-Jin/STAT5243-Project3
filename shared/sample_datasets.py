from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def get_titanic() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "titanic.csv")


def get_ames_housing() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "ames_housing.csv")


BUILTIN_DATASETS = {
    "titanic": get_titanic,
    "ames_housing": get_ames_housing,
}

BUILTIN_LABELS = {
    "titanic": "Titanic (classification)",
    "ames_housing": "Ames Housing (regression)",
}
