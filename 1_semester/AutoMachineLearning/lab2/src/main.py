import time

import openml
import pandas as pd
import autosklearn.regression
import autosklearn.classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)
import matplotlib.pyplot as plt

def run_airdelays_task(
    dataset_id=42721,
    time_limit=1000,
    n_jobs=1,
    test_size=0.2,
    random_state=42
):
    # Загрузка данных
    dataset = openml.datasets.get_dataset(dataset_id)

    X, y, _, _ = dataset.get_data(target=dataset.default_target_attribute)
    print(X.shape)
    print("=== DESCRIPTION ===")
    print("Описание набора данных:\n", dataset.description)
    print("=== INFO ===")
    print(X.info())

    # Разделение на train/test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)

    # Обучение Auto-sklearn
    regressor = autosklearn.regression.AutoSklearnRegressor(
        time_left_for_this_task=time_limit,
        n_jobs=n_jobs,
    )

    start_time = time.time()
    regressor.fit(X_train, y_train)
    elapsed = time.time() - start_time
    print(f"Время выполнения: {elapsed:.1f} сек")

    # Оценка модели
    y_pred = regressor.predict(X_test)

    print("\n=== METRICS ===")
    print("MAE:", mean_absolute_error(y_test, y_pred))
    print("RMSE:", mean_squared_error(y_test, y_pred, squared=False))
    print("R^2:", r2_score(y_test, y_pred))

    # Информация о поиске
    print("\n=== SEARCH STATISTICS ===")
    print(regressor.sprint_statistics())

    print("\n=== LEADERBOARD ===")
    print(regressor.leaderboard())

    # Информация о лучших моделях
    models_dict = regressor.show_models()
    df_all = pd.DataFrame.from_dict(models_dict, orient='index')
    columns_to_drop = ['data_preprocessor', 'feature_preprocessor', 'regressor']
    df_clean = df_all.drop(columns=columns_to_drop, errors='ignore')
    print("\n=== MODELS INFO ===")
    print(df_clean)

def run_smoke_detection_task(
    file_path="smoke_detection_iot.csv",
    time_limit=200,
    n_jobs=1
):
    # Загрузка данных
    df = pd.read_csv(file_path)
    print("=== INFO ===")
    print(df.info())
    print("\n=== HEAD ===")
    print(df.head(10))
    print(f"\n=== STATISTIC ===")
    print(df.describe())

    # Удаляем предсказываемый класс из признаков
    X = df.iloc[:, :-1]
    # Получаем метки классов для каждого обьекта
    y = df.iloc[:, -1]

    # Разделение на train/test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Обучение Auto-sklearn
    cls = autosklearn.classification.AutoSklearnClassifier(
        time_left_for_this_task=time_limit,
        per_run_time_limit=time_limit//10,
        n_jobs=n_jobs
    )
    cls.fit(X_train, y_train)

    # Оценка модели
    y_pred = cls.predict(X_test)

    print("\n=== METRICS ===")
    # Проверка пересечения train / test
    X_train_df = pd.DataFrame(X_train, columns=X.columns)
    X_test_df = pd.DataFrame(X_test, columns=X.columns)
    overlap = pd.merge(X_train_df, X_test_df, how='inner')
    print("Overlap: ", len(overlap))
    # Проверка утечки целевого признака
    print("Target in X:", "Fire Alarm" in X.columns)

    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("\nClassification report:")
    report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    df_report = pd.DataFrame(report_dict).transpose()
    print(df_report)

    plt.figure(figsize=(6, 6))
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=cls.classes_,
    )
    disp.plot(cmap="Blues", values_format="d")
    plt.title("Confusion Matrix (Smoke Detection)")
    plt.tight_layout()
    plt.savefig("ConfusionMatrix(SmokeDetection).png")
    plt.close()
    # Информация о поиске
    print("\n=== SEARCH STATISTICS ===")
    print(cls.sprint_statistics())

    print("\n=== LEADERBOARD ===")
    print(cls.leaderboard())

    # Информация о лучших моделях
    print("\n=== MODELS INFO ===")
    print(cls.show_models())


if __name__ == "__main__":
    # run_airdelays_task()

    run_smoke_detection_task()
