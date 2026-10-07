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


def get_features_for_month(group_ts, target_month):
    """Признаки для одного target_month. Используется только история до target_month."""
    end = target_month - pd.offsets.MonthBegin(1)
    hist = group_ts.loc[:, :end]

    if hist.shape[1] == 0:
        hist = pd.DataFrame(0.0, index=group_ts.index, columns=[end])

    features = pd.DataFrame(index=group_ts.index)

    # Календарные признаки
    features["month"] = target_month.month
    features["quarter"] = target_month.quarter
    features["year"] = target_month.year
    features["month_idx"] = (target_month.year - 2018) * 12 + target_month.month
    features["month_sin"] = np.sin(2 * np.pi * target_month.month / 12)
    features["month_cos"] = np.cos(2 * np.pi * target_month.month / 12)

    # Лаги 1..12
    for lag in range(1, 13):
        m = target_month - pd.offsets.MonthBegin(lag)
        features[f"vol_tm{lag}"] = month_value(group_ts, m)

    # Скользящие статистики (по времени, т.е. по столбцам hist)
    # Транспонируем, чтобы rolling работал вдоль оси времени
    hist_t = hist.T  # shape: (месяцы, группы)
    for w in (3, 6, 12):
        roll_t = hist_t.rolling(window=w, min_periods=1)
        features[f"mean_{w}"] = roll_t.mean().iloc[-1]
        features[f"std_{w}"] = roll_t.std().iloc[-1].fillna(0.0)
        features[f"min_{w}"] = roll_t.min().iloc[-1]
        features[f"max_{w}"] = roll_t.max().iloc[-1]

    # Статистики по всей истории
    features["hist_mean"] = hist.mean(axis=1)
    features["hist_std"] = hist.std(axis=1).fillna(0.0)
    features["hist_min"] = hist.min(axis=1)
    features["hist_max"] = hist.max(axis=1)
    features["hist_nonzero_ratio"] = (hist > 0).mean(axis=1)

    # Тренды и отношения
    features["diff_1_2"] = features["vol_tm1"] - features["vol_tm2"]
    features["ratio_1_2"] = features["vol_tm1"] / (features["vol_tm2"] + 1.0)
    features["diff_1_3"] = features["vol_tm1"] - features["vol_tm3"]
    features["diff_1_6"] = features["vol_tm1"] - features["mean_6"]
    features["diff_1_12"] = features["vol_tm1"] - features["mean_12"]

    features = features.fillna(0.0)

    # Целевая переменная
    features[TARGET] = month_value(group_ts, target_month)

    return features




def build_dataset(group_ts):
    rows = []

    for target_month in TARGET_FULL_RANGE:
        df = get_features_for_month(group_ts, target_month).reset_index()
        df["target_month"] = target_month
        rows.append(df)

    df = pd.concat(rows, ignore_index=True)
    df = df.sort_values("target_month", kind="mergesort").reset_index(drop=True)

    assert df["target_month"].is_monotonic_increasing
    assert (df["target_month"].value_counts() == GROUPS).all()

    return df


def run_cv(df):
    exclude = {"target", "target_month"}
    feature_cols = [c for c in df.columns if c not in exclude]

    ts_cv = TimeSeriesSplit(n_splits=5, test_size=GROUPS * 3)
    losses = []

    for fold, (train_idx, test_idx) in enumerate(ts_cv.split(df), 1):
        train = df.iloc[train_idx]
        test = df.iloc[test_idx]

        X_train = train[feature_cols]
        X_test = test[feature_cols]

        y_train = train[TARGET].values
        y_test = test[TARGET].values

        model = CatBoostRegressor(
            iterations=3000,
            learning_rate=0.03,
            depth=6,
            l2_leaf_reg=3.0,
            loss_function="RMSE",
            eval_metric="RMSE",
            random_seed=RS,
            od_type="Iter",
            od_wait=100,
            verbose=False,
            cat_features=CAT_COLS,
            allow_writing_files=False,
        )

        # Важно: учим на log1p(target), т.к. RMSLE = RMSE на log1p
        model.fit(
            X_train,
            np.log1p(y_train),
            eval_set=(X_test, np.log1p(y_test)),
            use_best_model=True,
        )

        train_pred = np.expm1(model.predict(X_train))
        test_pred = np.expm1(model.predict(X_test))

        train_loss = rmsle(y_train, train_pred)
        test_loss = rmsle(y_test, test_pred)

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
    print(f"\nAvg Train RMSLE: {avg[0]:.6f}, Avg Test RMSLE: {avg[1]:.6f}")


def main():
    group_ts = load_group_ts()
    print(f"Group time series shape: {group_ts.shape}")

    df = build_dataset(group_ts)
    print(f"CatBoost dataset shape: {df.shape}")

    run_cv(df)


if __name__ == "__main__":
    main()