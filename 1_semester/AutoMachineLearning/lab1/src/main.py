import openml
import h2o
from h2o.automl import H2OAutoML
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    ConfusionMatrixDisplay
)


def run_handwritten_digits_recognition_task(
    dataset_id=32,
    max_runtime=600,
    nthreads=1,
    test_size=0.2,
    seed=42
):
    # Инициализация H2O
    h2o.init(nthreads=nthreads)

    # Загрузка данных
    dataset = openml.datasets.get_dataset(dataset_id)
    X, y, _, _ = dataset.get_data(target=dataset.default_target_attribute)
    target_feature = "target"
    df = pd.concat([X, y.rename(target_feature)], axis=1)

    print("=== INFO ===")
    print(df.info())
    print("\n=== HEAD ===")
    print(df.head(10))
    print(f"\n=== STATISTIC ===")
    print(df.describe())

    # Разбиение на train/test
    train_df, test_df = train_test_split(
        df, test_size=test_size, random_state=seed, stratify=df[target_feature]
    )

    train_h2o = h2o.H2OFrame(train_df)
    test_h2o = h2o.H2OFrame(test_df)

    features = [c for c in train_h2o.columns if c != target_feature]

    # Используем классификацию
    train_h2o[target_feature] = train_h2o[target_feature].asfactor()
    test_h2o[target_feature] = test_h2o[target_feature].asfactor()

    # AutoML
    aml = H2OAutoML(
        max_runtime_secs=max_runtime,
        seed=seed,
        balance_classes=True
    )

    aml.train(
        x=features,
        y=target_feature,
        training_frame=train_h2o
    )

    # Результат тренировки моделей
    lb = aml.leaderboard
    print(lb.head(rows=lb.nrows))

    perf = aml.leader.model_performance(test_h2o)
    print(perf)
    cm = perf.confusion_matrix().as_data_frame()
    print("\nConfusion Matrix:")
    print(cm)

    cm_values = cm.iloc[:10, :10].values.astype(int)
    labels = cm.columns[:10]
    disp = ConfusionMatrixDisplay(confusion_matrix=cm_values, display_labels=labels)
    disp.plot(cmap="Blues", values_format="d")
    plt.title("Confusion Matrix")
    plt.savefig("ConfusionMatrix(HandwrittenDigits).png")


def run_concrete_strength_task(
    file_path="concrete.xls",
    max_runtime=100,
    nthreads=1,
    test_size=0.2,
    seed=42,
    target_feature="strength"
):
    # Инициализация H2O
    h2o.init(nthreads=nthreads)

    # Загрузка данных
    df = pd.read_csv(file_path)
    print("=== INFO ===")
    print(df.info())
    print("\n=== HEAD ===")
    print(df.head(10))
    print(f"\n=== STATISTIC ===")
    print(df.describe())

    # Разбиение на train/test
    train_df, test_df = train_test_split(
        df, test_size=test_size, random_state=seed
    )

    train_h2o = h2o.H2OFrame(train_df)
    test_h2o = h2o.H2OFrame(test_df)
    features = [c for c in df.columns if c != target_feature]

    # AutoML
    aml = H2OAutoML(
        max_runtime_secs=max_runtime,
        seed=seed,
    )

    aml.train(
        x=features,
        y=target_feature,
        training_frame=train_h2o
    )

    # Результат тренировки моделей
    lb = aml.leaderboard
    print(lb.head(rows=lb.nrows))

    perf = aml.leader.model_performance(test_h2o)
    print(perf)

    leader = aml.leader
    print(leader.model_id)

    metalearner = leader.metalearner()
    print(metalearner)

    coefs = metalearner.coef()

    coef_df = (
        pd.DataFrame.from_dict(coefs, orient="index", columns=["weight"])
        .reset_index()
        .rename(columns={"index": "model"})
    )
    coef_df = coef_df.sort_values("weight", ascending=False)
    print(coef_df)

if __name__ == "__main__":
    run_handwritten_digits_recognition_task()

    # run_concrete_strength_task()