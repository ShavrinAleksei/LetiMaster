from matplotlib import pyplot as plt

plt.style.use("bmh")
plt.rcParams["axes.titlesize"] = "large"

import pathlib
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error
from catboost import CatBoostRegressor

# Пути и seed
DATA_DIR = pathlib.Path("./")
RS = 42

# Загрузка данных
train = pd.read_parquet(DATA_DIR.joinpath("train.parquet"))
print(train.head())

# Признаки и таргеты
CAT = ["feature4"]
TARGETS = ["target0", "target1"]
FTS = train.filter(like="feature").columns.difference(CAT)

# Гистограмма таргетов
plt.figure(figsize=(6, 6))
train[TARGETS].plot(kind="hist", range=(0, 100), bins=20, alpha=0.6, ax=plt.gca())
plt.xlabel("target")
plt.show()

# Кодирование категориального признака
train["gas"] = 0
train.loc[train.feature4 == "gas2", "gas"] = 1

FTS = FTS.union(["gas"])

# Разделение на train и valid
X_tr, X_val, y_tr, y_val = train_test_split(
    train[FTS], train[TARGETS], train_size=0.5, random_state=RS
)

# Обучение отдельной модели для каждого таргета
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

# Сборка предсказаний и обрезка по диапазону таргетов
tr_preds = np.column_stack(tr_preds)
val_preds = np.column_stack(val_preds)

tr_preds = np.clip(tr_preds, 0, 100)
val_preds = np.clip(val_preds, 0, 100)

# Метрики
print(f"MAPE (train): {mean_absolute_percentage_error(y_tr, tr_preds) * 100:.3f} %")
print(f"MAPE (val): {mean_absolute_percentage_error(y_val, val_preds) * 100:.3f} %")

# Сохранение моделей
for target, model in models.items():
    model.save_model(DATA_DIR.joinpath(f"{target}-cb-v1.cbm"))