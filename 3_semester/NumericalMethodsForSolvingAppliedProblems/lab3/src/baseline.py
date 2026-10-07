import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from catboost import CatBoostRegressor

from common import (
    AGG_COLS,
    GROUPS,
    TARGET_FULL_RANGE,
    RS,
    rmsle,
    load_group_ts,
    month_value,
)


CAT_COLS = AGG_COLS + ["month"]
TARGET = "target"

FTS_COLS = [
    "material_code", "company_code", "country", "region", "manager_code", "month",
    "vol_tm6", "vol_tm5", "vol_tm4", "vol_tm3", "vol_tm2", "vol_tm1",
    "last_year_avg", "last_year_min", "last_year_max",
]

# Общая функция оценки наивных baseline

def evaluate_simple(features, feature_col, name):
    print(f"\n=== {name} ===")

    ts_cv = TimeSeriesSplit(n_splits=5, test_size=GROUPS * 3)
    losses = []

    for fold, (train_idx, test_idx) in enumerate(ts_cv.split(features), 1):
        train = features.iloc[train_idx]
        test = features.iloc[test_idx]

        y_train = train["target"].values
        y_test = test["target"].values

        train_loss = rmsle(y_train, train[feature_col].values)
        test_loss = rmsle(y_test, test[feature_col].values)

        losses.append([train_loss, test_loss])

        print(f"Fold {fold}")
        print(
            f"  Train: {train['target_month'].min().date()} - "
            f"{train['target_month'].max().date()} | RMSLE={train_loss:.6f}"
        )
        print(
            f"  Test:  {test['target_month'].min().date()} - "
            f"{test['target_month'].max().date()} | RMSLE={test_loss:.6f}"
        )

    avg = np.mean(losses, axis=0)
    print(f"Avg Train RMSLE: {avg[0]:.6f}, Avg Test RMSLE: {avg[1]:.6f}")

# Baseline #1: last value

def make_last_value_features(group_ts):
    rows = []

    for target_month in TARGET_FULL_RANGE:
        prev_month = target_month - pd.offsets.MonthBegin(1)

        df = pd.DataFrame(index=group_ts.index)
        df["vol_tm1"] = month_value(group_ts, prev_month)
        df["target"] = month_value(group_ts, target_month)
        df["target_month"] = target_month

        rows.append(df.reset_index())

    features = pd.concat(rows, ignore_index=True)
    features = features.sort_values("target_month", kind="mergesort").reset_index(drop=True)

    assert features["target_month"].is_monotonic_increasing
    assert (features["target_month"].value_counts() == GROUPS).all()

    return features


# Baseline #2: last 3 months average

def make_last_3_avg_features(group_ts):
    rows = []

    for target_month in TARGET_FULL_RANGE:
        start = target_month - pd.offsets.MonthBegin(3)
        end = target_month - pd.offsets.MonthBegin(1)

        cols = pd.date_range(start, end, freq="MS")
        cols = [c for c in cols if c in group_ts.columns]

        if cols:
            avg = group_ts.loc[:, cols].mean(axis=1)
        else:
            avg = pd.Series(0.0, index=group_ts.index)

        df = pd.DataFrame(index=group_ts.index)
        df["last_3m_avg"] = avg
        df["target"] = month_value(group_ts, target_month)
        df["target_month"] = target_month

        rows.append(df.reset_index())

    features = pd.concat(rows, ignore_index=True)
    features = features.sort_values("target_month", kind="mergesort").reset_index(drop=True)

    assert features["target_month"].is_monotonic_increasing
    assert (features["target_month"].value_counts() == GROUPS).all()

    return features

# Baseline #3: CatBoostRegressor

def get_features(group_ts: pd.DataFrame, month: pd.Timestamp) -> pd.DataFrame:
    """Признаки для месяца `month`. В точности как в ноутбуке."""
    start_period = month - pd.offsets.MonthBegin(6)
    end_period = month - pd.offsets.MonthBegin(1)

    df = group_ts.loc[:, :end_period]

    features = pd.DataFrame([], index=df.index)
    features["month"] = month.month
    features[[f"vol_tm{i}" for i in range(6, 0, -1)]] = df.loc[:, start_period:end_period].copy()

    roll_t = df.T.rolling(window=12, min_periods=1)
    features = features.join(roll_t.mean().iloc[-1].rename("last_year_avg"))
    features = features.join(roll_t.min().iloc[-1].rename("last_year_min"))
    features = features.join(roll_t.max().iloc[-1].rename("last_year_max"))
    return features


def make_catboost_features(group_ts):
    datasets = []
    for target_month in TARGET_FULL_RANGE:
        features = get_features(group_ts, target_month)
        features["target"] = month_value(group_ts, target_month)
        features["target_month"] = target_month
        datasets.append(features.reset_index())

    df = pd.concat(datasets, ignore_index=True)
    df = df.sort_values("target_month", kind="mergesort").reset_index(drop=True)

    assert df["target_month"].is_monotonic_increasing
    assert (df["target_month"].value_counts() == GROUPS).all()

    return df

def evaluate_catboost_baseline(df, name):
    print(f"\n=== {name} ===")

    base_model = CatBoostRegressor(
        iterations=1000,
        early_stopping_rounds=30,
        depth=6,
        cat_features=CAT_COLS,
        random_state=RS,
        verbose=False,
        allow_writing_files=False,
    )

    ts_cv = TimeSeriesSplit(n_splits=5, test_size=GROUPS * 3)
    losses = []

    for fold, (train_idx, test_idx) in enumerate(ts_cv.split(df), 1):
        X_train = df[FTS_COLS].iloc[train_idx]
        X_test = df[FTS_COLS].iloc[test_idx]
        y_train = df[TARGET].iloc[train_idx]
        y_test = df[TARGET].iloc[test_idx]

        model = base_model.copy()
        model.fit(X_train, y_train, eval_set=(X_test, y_test))

        train_loss = rmsle(y_train, model.predict(X_train))
        test_loss = rmsle(y_test, model.predict(X_test))

        losses.append([train_loss, test_loss])

        print(f"Fold {fold}")
        print(
            f"  Train: {df['target_month'].iloc[train_idx].min().date()} - "
            f"{df['target_month'].iloc[train_idx].max().date()} | RMSLE={train_loss:.6f}"
        )
        print(
            f"  Test:  {df['target_month'].iloc[test_idx].min().date()} - "
            f"{df['target_month'].iloc[test_idx].max().date()} | RMSLE={test_loss:.6f}"
        )

    avg = np.mean(losses, axis=0)
    print(f"Avg Train RMSLE: {avg[0]:.6f}, Avg Test RMSLE: {avg[1]:.6f}")



def main():
    group_ts = load_group_ts()
    print(f"Group time series shape: {group_ts.shape}")

    last_value = make_last_value_features(group_ts)
    evaluate_simple(last_value, "vol_tm1", "Baseline #1: last value")

    last_3_avg = make_last_3_avg_features(group_ts)
    evaluate_simple(last_3_avg, "last_3m_avg", "Baseline #2: last 3 months average")

    catboost_features = make_catboost_features(group_ts)
    evaluate_catboost_baseline(catboost_features, "Baseline #3: CatBoostRegressor")


if __name__ == "__main__":
    main()