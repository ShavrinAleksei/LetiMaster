import pandas as pd
import matplotlib.pyplot as plt

from sklearn.datasets import load_digits, fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, ConfusionMatrixDisplay

from hyperopt import tpe, rand, anneal, partial, mix, hp
from hpsklearn import (HyperoptEstimator, any_preprocessing, any_classifier)
from hpsklearn import (
    gradient_boosting_classifier, svc, random_forest_classifier, k_neighbors_classifier, extra_tree_classifier, ada_boost_classifier, sgd_classifier,
)
from sklearn.preprocessing import LabelEncoder
from scipy.io import arff

def custom_any_classifier(name):
    classifiers = [
        svc(f"{name}.svc"),
        k_neighbors_classifier(f"{name}.knn"),
        random_forest_classifier(f"{name}.random_forest"),
        extra_tree_classifier(f"{name}.extra_trees"),
        ada_boost_classifier(f"{name}.ada_boost"),
        gradient_boosting_classifier(f"{name}.grad_boosting", loss="log_loss"),
        sgd_classifier(f"{name}.sgd"),
    ]

    return hp.choice(name, classifiers)

def run_digits_task(
    test_size=0.2,
    random_state=42,
):
    print("=== DIGITS DATASET ===")

    # 1. Загрузка данных
    digits = load_digits()
    X = digits.data
    y = digits.target

    print("X shape:", X.shape)
    print("y shape:", y.shape)

    # 2. Train / test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state
    )

    # 3. Hyperopt-sklearn (TPE)
    estim = HyperoptEstimator(
        classifier=custom_any_classifier("clf"),
        preprocessing=any_preprocessing("prep"),
        algo=tpe.suggest,
    )

    estim.fit(X_train, y_train)

    # 4. Оценка
    y_pred = estim.predict(X_test)

    print("\n=== METRICS ===")
    print("Accuracy:", accuracy_score(y_test, y_pred))

    disp = ConfusionMatrixDisplay.from_predictions(y_test, y_pred)
    plt.title("Confusion Matrix (Digits, TPE)")
    plt.tight_layout()
    plt.savefig("cm_digits_tpe.png")
    plt.close()

    print("\n=== BEST MODEL ===")
    print(estim.best_model())

    # 5. Без параметров (по умолчанию)
    estim_default = HyperoptEstimator()
    estim_default.fit(X_train, y_train)
    y_pred_def = estim_default.predict(X_test)

    print("\n=== DEFAULT METRICS ===")
    print("Accuracy:", accuracy_score(y_test, y_pred_def))

    disp = ConfusionMatrixDisplay.from_predictions(y_test, y_pred)
    plt.title("Confusion Matrix (Digits, TPE)")
    plt.tight_layout()
    plt.savefig("cm_digits_default.png")
    plt.close()

    print("\n=== BEST DEFAULT MODEL ===")
    print(estim_default.best_model())


def run_electricity_prices_task(
    dataset_id=151,
    test_size=0.2,
    random_state=42,
):
    print("=== ELECTRICITY PRICES DATASET ===")

    # 1. Загрузка данных
    dataset = fetch_openml(data_id=dataset_id, as_frame=True)
    df = dataset.data.copy()
    df["target"] = dataset.target

    print("\n=== FIRST 10 ROWS (FULL DATASET) ===")
    print(df.head(10))

    X = dataset.data
    le = LabelEncoder()
    y = le.fit_transform(dataset.target)

    # 2. Описание
    print("\n=== DESCRIPTION ===")
    print(dataset.DESCR)

    print("\n=== INFO ===")
    print(X.info())

    # 3. Train / test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state
    )

    # 4. TPE (как в задании 1)
    estim_tpe = HyperoptEstimator(
        classifier=any_classifier("clf"),
        preprocessing=any_preprocessing("prep"),
        algo=tpe.suggest,
    )

    estim_tpe.fit(X_train, y_train)
    y_pred_tpe = estim_tpe.predict(X_test)

    print("\n=== TPE RESULTS ===")
    print("Accuracy:", accuracy_score(y_test, y_pred_tpe))

    disp = ConfusionMatrixDisplay.from_predictions(y_test, y_pred_tpe)
    plt.title("Confusion Matrix (Electricity, TPE)")
    plt.tight_layout()
    plt.savefig("cm_electricity_tpe_2.png")
    plt.close()

    print("\n=== BEST MODEL ===")
    print(estim_tpe.best_model())

    # 6. Смешанный алгоритм поиска
    mix_algo = partial(
        mix.suggest,
        p_suggest=[
            (0.25, rand.suggest),
            (0.25, anneal.suggest),
            (0.50, tpe.suggest),
        ]
    )

    estim_mix = HyperoptEstimator(
        classifier=any_classifier("clf"),
        algo=mix_algo,
    )

    estim_mix.fit(X_train, y_train)
    y_pred_mix = estim_mix.predict(X_test)

    print("\n=== MIXED SEARCH RESULTS ===")
    print("Accuracy:", accuracy_score(y_test, y_pred_mix))

    disp = ConfusionMatrixDisplay.from_predictions(y_test, y_pred_mix)
    plt.title("Confusion Matrix (Electricity, MIX)")
    plt.tight_layout()
    plt.savefig("cm_electricity_mix_2.png")
    plt.close()

    print("\n=== BEST MODEL ===")
    print(estim_mix.best_model())

    # 7. Классификатор best default
    best = estim_mix.best_model()
    learner = best["learner"]

    default_clf = learner.__class__()
    default_clf.fit(X_train, y_train)
    y_pred_def = default_clf.predict(X_test)

    print("\n=== ESTIMATOR ===")
    print("Accuracy:", accuracy_score(y_test, y_pred_def))

    disp = ConfusionMatrixDisplay.from_predictions(y_test, y_pred_def)
    plt.title("Confusion Matrix (Electricity, MIX)")
    plt.tight_layout()
    plt.savefig("cm_electricity_default_2.png")
    plt.close()


def run_creditcard_task(
    file_path="credit.arff",
    test_size=0.2,
    random_state=42,
):
    print("=== CREDIT CARD DATASET ===")

    # 1. Загрузка данных из ARFF
    data, meta = arff.loadarff(file_path)
    df = pd.DataFrame(data)

    print("\n=== INFO ===")
    print(df.info())
    print(df.describe())

    # 2. Преобразование данных
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]

    # 3. Train / test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state
    )

    # 4. Hyperopt-sklearn (TPE)
    estim = HyperoptEstimator(
        classifier=any_classifier("clf"),
        preprocessing=any_preprocessing("prep"),
        algo=tpe.suggest,
        trial_timeout=100,
    )

    estim.fit(X_train, y_train)

    # 5. Оценка
    y_pred = estim.predict(X_test)

    print("\n=== METRICS ===")
    print("Accuracy:", accuracy_score(y_test, y_pred))

    disp = ConfusionMatrixDisplay.from_predictions(y_test, y_pred)
    plt.title("Confusion Matrix (Credit Card, ATPE)")
    plt.tight_layout()
    plt.savefig("cm_creditcard_tpe_3.png")
    plt.close()

    print("\n=== BEST MODEL ===")
    print(estim.best_model())

if __name__ == "__main__":
    # run_digits_task()
    # run_electricity_prices_task()
    run_creditcard_task()

