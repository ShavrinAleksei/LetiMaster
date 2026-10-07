import pathlib
import numpy as np
import pandas as pd

DATA_DIR = pathlib.Path(__file__).resolve().parent
DATA_FILE = "sc2021_train_deals.csv"

AGG_COLS = ["material_code", "company_code", "country", "region", "manager_code"]
GROUPS = 941

TARGET_FULL_RANGE = pd.date_range("2019-01-01", "2020-07-01", freq="MS")
RS = 82736


def rmsle(y_true, y_pred):
    """RMSLE с обрезкой отрицательных прогнозов."""
    y_pred = np.clip(np.asarray(y_pred, dtype=float), 0.0, None)
    y_true = np.asarray(y_true, dtype=float)
    return float(np.sqrt(np.mean((np.log1p(y_true) - np.log1p(y_pred)) ** 2)))


def load_group_ts(data_dir=DATA_DIR):
    """Загружает данные и строит матрицу group x month."""
    data_dir = pathlib.Path(data_dir)
    data = pd.read_csv(data_dir / DATA_FILE, parse_dates=["month", "date"])

    group_ts = (
        data.groupby(AGG_COLS + ["month"])["volume"]
        .sum()
        .unstack(fill_value=0)
        .sort_index(axis=1)
    )
    return group_ts


def month_value(group_ts, month):
    """Значение месяца или нули, если месяца нет в данных."""
    if month in group_ts.columns:
        return group_ts[month].astype(float)
    return pd.Series(0.0, index=group_ts.index)
