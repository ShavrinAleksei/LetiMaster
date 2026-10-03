from matplotlib import pyplot as plt

plt.style.use("bmh")
plt.rcParams["axes.titlesize"] = "large"

import pathlib
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.linear_model import LinearRegression, RidgeCV
from sklearn.preprocessing import StandardScaler
from catboost import CatBoostRegressor

# Пути и seed
DATA_DIR = pathlib.Path("./")
RS = 42

# Загрузка данных
train = pd.read_parquet(DATA_DIR.joinpath("train.parquet"))
print("Размер данных:", train.shape)
print(train.head())

# Признаки и таргеты
CAT = ["feature4"]
TARGETS = ["target0", "target1"]
FTS = train.filter(like="feature").columns.difference(CAT)

# Кодирование категориального признака
train["gas"] = 0
train.loc[train.feature4 == "gas2", "gas"] = 1
FTS = FTS.union(["gas"])

# Разделение на train и valid (как в baseline)
X_tr, X_val, y_tr, y_val = train_test_split(
    train[FTS], train[TARGETS], train_size=0.5, random_state=RS
)
print("Train:", X_tr.shape, "Valid:", X_val.shape)

# Residual plot для линейной модели
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

for ax, tg in zip(axes, TARGETS):
    lin = LinearRegression().fit(X_tr, y_tr[tg])
    residuals = y_tr[tg] - lin.predict(X_tr)
    for g_val, color in zip([0, 1], ["blue", "orange"]):
        mask = X_tr["gas"] == g_val
        ax.scatter(lin.predict(X_tr)[mask], residuals[mask],
                   alpha=0.1, s=1, c=color, label=f"gas{g_val+1}")
    ax.axhline(0, color="red", linestyle="--")
    ax.legend()
    ax.set_xlabel("Предсказание линейной модели")
    ax.set_ylabel("Остаток")
    ax.set_title(f"Residual plot для {tg}")

plt.tight_layout()
plt.savefig("residuals.png", dpi=100, bbox_inches="tight")
plt.close()

# Обучение CatBoost (baseline организаторов)
models = {}
tr_preds = []
val_preds = []

for tg in TARGETS:
    print(f"{tg}", "=" * 10)
    cb_model = CatBoostRegressor(
        max_depth=4,
        iterations=5000,
        early_stopping_rounds=20,
        objective="MAPE",
        verbose=200,
        random_state=RS
    )
    cb_model.fit(X_tr, y_tr[tg], eval_set=(X_val, y_val[tg]))
    tr_preds.append(cb_model.predict(X_tr))
    val_preds.append(cb_model.predict(X_val))
    models[tg] = cb_model

# Сборка и обрезка
tr_preds = np.clip(np.column_stack(tr_preds), 0, 100)
val_preds = np.clip(np.column_stack(val_preds), 0, 100)

# Метрики
print(f"MAPE (train): {mean_absolute_percentage_error(y_tr, tr_preds) * 100:.3f} %")
print(f"MAPE (val): {mean_absolute_percentage_error(y_val, val_preds) * 100:.3f} %")

# Важность признаков из CatBoost
importances = {}
for tg in TARGETS:
    imp = models[tg].get_feature_importance()
    importances[tg] = imp
    print(f"\n=== Топ-10 признаков для {tg} ===")
    pairs = sorted(zip(FTS, imp), key=lambda x: -x[1])[:10]
    for name, val in pairs:
        print(f"{name}: {val:.2f}")

# Визуализация важности
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
for ax, tg in zip(axes, TARGETS):
    pairs = sorted(zip(FTS, importances[tg]), key=lambda x: x[1])
    names = [p[0] for p in pairs]
    vals = [p[1] for p in pairs]
    ax.barh(names, vals)
    ax.set_title(f"Важность признаков для {tg}")
plt.tight_layout()
plt.savefig("feature_importance.png", dpi=100, bbox_inches="tight")
plt.close()

# Построение Ridge-регрессии с постепенным расширением признаков
idx_tr, idx_val = train_test_split(
    np.arange(len(train)), train_size=0.5, random_state=RS
)
X_all = train[FTS].values
y_all = {tg: train[tg].values for tg in TARGETS}

def mape(y_true, y_pred):
    return mean_absolute_percentage_error(y_true, y_pred) * 100

def fit_ridge(X_train, y_train, X_valid):
    scaler = StandardScaler()
    Xtr = scaler.fit_transform(X_train)
    Xval = scaler.transform(X_valid)
    model = RidgeCV(alphas=np.logspace(-3, 3, 20), cv=5)
    model.fit(Xtr, y_train)
    return model.predict(Xval)

# Важные признаки, отобранные по результатам CatBoost
important = {
    "target0": ["feature22", "feature2", "feature13", "feature19", "feature20"],
    "target1": ["feature16", "feature13", "feature20", "gas", "feature22"],
}

results = {"target0": {}, "target1": {}}
best_matrices = {}  # будем хранить лучшую матрицу признаков для каждого таргета

for tg in TARGETS:
    print(f"\n{'=' * 20} {tg} {'=' * 20}")
    imp_idx = [list(FTS).index(f) for f in important[tg]]

    # 1. OLS
    lin = LinearRegression().fit(X_tr, y_tr[tg])
    results[tg]["OLS"] = mape(y_val[tg], lin.predict(X_val))
    print(f"OLS:                    {results[tg]['OLS']:.3f}%")

    # 2. Ridge на исходных
    pred = fit_ridge(X_tr, y_tr[tg], X_val)
    results[tg]["Ridge"] = mape(y_val[tg], pred)
    print(f"Ridge:                  {results[tg]['Ridge']:.3f}%")

    # 3. Ridge + квадраты
    X_sq = np.hstack([X_all, X_all ** 2])
    pred = fit_ridge(X_sq[idx_tr], y_all[tg][idx_tr], X_sq[idx_val])
    results[tg]["Ridge + квадраты"] = mape(y_all[tg][idx_val], pred)
    print(f"Ridge + квадраты:       {results[tg]['Ridge + квадраты']:.3f}%")

    # 4. Ridge + взаимодействия
    X_int = X_sq.copy()
    for fi in imp_idx:
        for j in range(X_all.shape[1]):
            if j != fi:
                X_int = np.hstack([X_int, (X_all[:, fi] * X_all[:, j]).reshape(-1, 1)])
    pred = fit_ridge(X_int[idx_tr], y_all[tg][idx_tr], X_int[idx_val])
    results[tg]["Ridge + взаимодействия"] = mape(y_all[tg][idx_val], pred)
    print(f"Ridge + взаимодействия: {results[tg]['Ridge + взаимодействия']:.3f}%")

    # 5. Ridge + степени 3-4
    X_pow = X_int.copy()
    for fi in imp_idx:
        X_pow = np.hstack([
            X_pow,
            (X_all[:, fi] ** 3).reshape(-1, 1),
            (X_all[:, fi] ** 4).reshape(-1, 1),
        ])
    pred = fit_ridge(X_pow[idx_tr], y_all[tg][idx_tr], X_pow[idx_val])
    results[tg]["Ridge + степени 3-4"] = mape(y_all[tg][idx_val], pred)
    print(f"Ridge + степени 3-4:    {results[tg]['Ridge + степени 3-4']:.3f}%")

    # Запоминаем лучшую матрицу для этого таргета
    best_name = min(results[tg], key=results[tg].get)
    best_matrices[tg] = {
        "Ridge + квадраты": X_sq,
        "Ridge + взаимодействия": X_int,
        "Ridge + степени 3-4": X_pow,
    }[best_name]
    best_matrices[tg + "_name"] = best_name

# Итоговая таблица
print(f"\n{'=' * 60}")
print(f"{'Модель':<30} {'target0':>12} {'target1':>12} {'combined':>12}")
print("-" * 60)
for model in results["target0"].keys():
    m0 = results["target0"][model]
    m1 = results["target1"][model]
    mc = (m0 + m1) / 2
    print(f"{model:<30} {m0:>11.3f}% {m1:>11.3f}% {mc:>11.3f}%")

# Финальные модели
best0 = min(results["target0"], key=results["target0"].get)
best1 = min(results["target1"], key=results["target1"].get)
mape_best0 = results["target0"][best0]
mape_best1 = results["target1"][best1]
mape_combined = (mape_best0 + mape_best1) / 2

print(f"\nЛучшая для target0: {best0} ({mape_best0:.3f}%)")
print(f"Лучшая для target1: {best1} ({mape_best1:.3f}%)")
print(f"\nCombined MAPE финального решения: {mape_combined:.3f}%")
print(f"Baseline CatBoost (val):          1.633%")

# Проверка генерализации: Ridge vs CatBoost
print(f"\n{'=' * 70}")
print("Проверка генерализации: Ridge vs CatBoost")
print("=" * 70)

gen_features = {"target0": "feature22", "target1": "feature16"}
gen_results = {"Ridge": {}, "CatBoost": {}}

for tg in TARGETS:
    fname = gen_features[tg]
    fi = list(FTS).index(fname)
    q10, q90 = np.percentile(X_all[:, fi], [10, 90])
    extreme = (X_all[:, fi] <= q10) | (X_all[:, fi] >= q90)
    normal = ~extreme

    print(f"\n{tg}: {fname} q10={q10:.2f}, q90={q90:.2f}")
    print(f"Нормальных: {normal.sum()}, Крайних: {extreme.sum()}")

    # --- Ridge на лучшей матрице ---
    X_best = best_matrices[tg]
    pred_ridge = fit_ridge(X_best[normal], y_all[tg][normal], X_best[extreme])
    gen_results["Ridge"][tg] = mape(y_all[tg][extreme], pred_ridge)

    # --- CatBoost на тех же данных ---
    # Чтобы не "подглядывать" в extreme для early stopping,
    # разбиваем normal на внутренние train/val
    normal_idx = np.where(normal)[0]
    rng = np.random.RandomState(RS)
    rng.shuffle(normal_idx)
    n_inner = int(0.8 * len(normal_idx))
    inner_tr = normal_idx[:n_inner]
    inner_val = normal_idx[n_inner:]

    cb = CatBoostRegressor(
        max_depth=4, iterations=5000,
        early_stopping_rounds=20, objective="MAPE",
        verbose=0, random_state=RS
    )
    cb.fit(X_all[inner_tr], y_all[tg][inner_tr],
           eval_set=(X_all[inner_val], y_all[tg][inner_val]))
    pred_cb = np.clip(cb.predict(X_all[extreme]), 0, 100)
    gen_results["CatBoost"][tg] = mape(y_all[tg][extreme], pred_cb)

    print(f"  Ridge MAPE:    {gen_results['Ridge'][tg]:.3f}%")
    print(f"  CatBoost MAPE: {gen_results['CatBoost'][tg]:.3f}%")

# Итоговая таблица
print(f"\n{'=' * 70}")
print(f"{'Модель':<15} {'target0':>12} {'target1':>12} {'combined':>12}")
print("-" * 70)
for model in ["Ridge", "CatBoost"]:
    m0 = gen_results[model]["target0"]
    m1 = gen_results[model]["target1"]
    mc = (m0 + m1) / 2
    print(f"{model:<15} {m0:>11.3f}% {m1:>11.3f}% {mc:>11.3f}%")

# Итоговое сравнение с обычной валидацией
print(f"\n{'=' * 70}")
print("Сравнение: обычная валидация vs крайние значения")
print("=" * 70)
print(f"{'Модель':<25} {'val':>10} {'extreme':>12} {'Δ':>10}")
print("-" * 70)
# Ridge
ridge_val = mape_combined
ridge_ext = (gen_results["Ridge"]["target0"] + gen_results["Ridge"]["target1"]) / 2
print(f"{'Ridge + степени 3-4':<25} {ridge_val:>9.3f}% {ridge_ext:>11.3f}% {ridge_ext - ridge_val:>+9.3f}%")
# CatBoost
cb_ext = (gen_results["CatBoost"]["target0"] + gen_results["CatBoost"]["target1"]) / 2
print(f"{'CatBoost (baseline)':<25} {1.633:>9.3f}% {cb_ext:>11.3f}% {cb_ext - 1.633:>+9.3f}%")_