from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt
from typing import Callable

np.random.seed(42)

DistributionFunction = Callable[[float, int], np.ndarray]
DistributionCase = tuple[str, DistributionFunction, float]


@dataclass
class Statistics:
    mean: float
    std: float


def uniform_distribution(alpha: float, size: int) -> np.ndarray:
    # Равномерное распределение на [0, alpha]
    u: np.ndarray = np.random.uniform(low=0, high=alpha, size=size)
    return u


def exponential_distribution(lamb: float, size: int) -> np.ndarray:
    # Показательное распределение с параметром lamb
    u: np.ndarray = uniform_distribution(1, size)
    return -np.log(1 - u) / lamb


def triangular_distribution(a: float, size: int) -> np.ndarray:
    # Треугольное распределение с параметром a
    u: np.ndarray = uniform_distribution(1, size)
    return a * (1 - np.sqrt(1 - u))


def get_statistics(data: np.ndarray) -> Statistics:
    return Statistics(mean=float(np.mean(data)), std=float(np.std(data)))


def plot_histogram(data: np.ndarray, title: str, stats: Statistics) -> None:
    full_title: str = f"{title} ({data.shape[0]}) Мат.ожидание: {stats.mean:.3f}, СКО: {stats.std:.3f}"
    print(full_title)
    plt.figure(figsize=(8, 6))
    plt.title(full_title)
    plt.hist(data, bins=20, color="skyblue", edgecolor="black")
    plt.title(full_title)
    plt.xlabel("Значение")
    plt.ylabel("Плотность")
    plt.savefig(full_title.replace(" ", "_") + ".png", dpi=300, bbox_inches="tight")


def main() -> None:
    alpha: float = 60.0
    lamb: float = 1 / 200.0
    a: float = 30.0
    sizes: list[int] = [100, 1_000, 10_000, 100_000]
    use_cases: list[DistributionCase] = [
        ("Равномерное распределение", uniform_distribution, alpha),
        ("Показательное распределение", exponential_distribution, lamb),
        ("Треугольное распределение", triangular_distribution, a),
    ]

    for distribution_name, distribution_func, param in use_cases:
        for size in sizes:
            data: np.ndarray = distribution_func(param, size)
            stats: Statistics = get_statistics(data)
            plot_histogram(data, distribution_name, stats)


if __name__ == "__main__":
    main()
