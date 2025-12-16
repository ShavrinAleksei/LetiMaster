from typing import List

import simpy
import numpy as np
import pandas as pd
from enum import Enum, auto
from dataclasses import dataclass

np.random.seed(42)

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

class Distribution(Enum):
    UNIFORM = auto()
    EXPONENTIAL = auto()
    TRIANGULAR = auto()

@dataclass
class ExperimentStats:
    # Характеристики очереди
    QM: int  # Максимальная длина очереди (Queue Max)
    QA: float  # Средняя длина очереди (Queue Average)
    QZ: int  # Число заявок, поступивших на обслуживание без ожидания (Queue Zero)
    QT: float  # Среднее время пребывания заявки в очереди (включая нулевые ожидания)
    QX: float  # Среднее время пребывания заявки в очереди (без нулевых ожиданий)

    # Характеристики устройства (сервера)
    FR: float  # Коэффициент загрузки сервера (Facility Rate / Utilization)
    FT: float  # Среднее время обслуживания заявки (Facility Time / Average Service Time)

    rejects: float  # число отказов
    reject_prob: float  # вероятность отказа

    lambda_effective: float # Эффективность с учетом отказов

    # Дополнительно для анализа вариативности
    std_wait_time: float = 0.0  # СКО времени ожидания
    std_service_time: float = 0.0  # СКО времени обслуживания

    # Параметры эксперимента
    N: int = 0  # Общее число заявок, прошедших через систему
    rho: float = 0.0 # Приведенная интенсивность потока (λ/μ)
    service_dist: Distribution = Distribution.UNIFORM

@dataclass
class UseCase:
    rho: float
    N: int
    service_dist: Distribution
    max_queue_len: int

@dataclass
class UseCaseGroup:
    name: str
    description: str
    use_cases: List[UseCase]

class TimeGenerator:
    def __init__(self, dist_type: Distribution, avg_time: float):
        self.__dist_type: Distribution = dist_type
        self.__avg_time: float = avg_time

    def generate(self, count: int = 1) -> float:
        match(self.__dist_type):
            case Distribution.UNIFORM:
                return np.random.uniform(low=0, high=self.__avg_time * 2, size=count)
            case Distribution.EXPONENTIAL:
                return np.random.exponential(scale=self.__avg_time, size=count)
            case Distribution.TRIANGULAR:
                return np.random.triangular(
                    left=0,
                    mode=self.__avg_time,
                    right=self.__avg_time * 2,
                    size=count
                )
            case _:
                raise ValueError("Unknown distribution type")

class ServiceSystem:
    def __init__(self, env, service_gen: TimeGenerator, max_queue_len: int):
        self.env = env
        self.server = simpy.Resource(env, capacity=1)
        self.service_gen = service_gen
        self.max_queue_length = max_queue_len

        self.wait_times = []
        self.queue_lengths = []
        self.no_wait = 0
        self.rejects = 0
        self.service_times = []

    def handle_request(self):
        """Процесс обслуживания заявки"""
        arrival_time = self.env.now
        queue_length = len(self.server.queue)
        if queue_length > self.max_queue_length:
            self.rejects += 1
            return
        without_wait = queue_length == 0
        self.queue_lengths.append(queue_length)

        with self.server.request() as req:
            yield req
            if not without_wait:
                self.wait_times.append((self.env.now - arrival_time)[0])
            else:
                self.no_wait += 1
                self.wait_times.append(0)
            service_time = self.service_gen.generate()
            self.service_times.append(service_time)
            yield self.env.timeout(service_time)

class RequestGenerator:
    def __init__(
        self,
        env: simpy.Environment,
        system: ServiceSystem,
        N: int,
        interarrival_gen: TimeGenerator,
    ):
        self.env = env
        self.system = system
        self.N = N
        self.interarrival_gen = interarrival_gen

    def run(self):
        for i in range(self.N):
            interarrival = self.interarrival_gen.generate()
            yield self.env.timeout(interarrival)
            self.env.process(self.system.handle_request())

def run_experiment(N: int, mu: float, lamb: float, service_dist: Distribution, max_queue_len: int):
    avg_service_time: float = 1 / mu
    avg_interval_time: float = 1 / lamb
    env = simpy.Environment()

    interarrival_gen = TimeGenerator(
        dist_type=Distribution.EXPONENTIAL,
        avg_time=avg_interval_time
    )
    service_gen = TimeGenerator(
        dist_type=service_dist,
        avg_time=avg_service_time
    )

    system = ServiceSystem(
        env=env,
        service_gen=service_gen,
        max_queue_len=max_queue_len
    )

    request_gen = RequestGenerator(
        env=env,
        system=system,
        N=N,
        interarrival_gen=interarrival_gen,
    )
    env.process(request_gen.run())
    env.run()
    total_time: float = env.now

    QX = list(filter(lambda time: time > 0, system.wait_times))

    return ExperimentStats(
        QM=max(system.queue_lengths),
        QA=np.mean(system.queue_lengths),
        QZ=system.no_wait,
        QT=np.mean(system.wait_times),
        QX=np.mean(QX) if len(QX) else 0.0,
        FR=sum(system.service_times) / total_time,
        FT=np.mean(system.service_times),
        rejects=system.rejects,
        reject_prob=system.rejects / N,
        lambda_effective=lamb * (1 - system.rejects / N),
    )

def run_experiments(N: int, rho: float, lam: float, service_dist: Distribution, max_queue_len: int, repeats: int) -> ExperimentStats:
    mu: float = lam / rho

    all_stats: list[ExperimentStats] = []
    for _ in range(repeats):
        experiment_statistic = run_experiment(
            N=N,
            mu=mu,
            lamb=lam,
            service_dist=service_dist,
            max_queue_len=max_queue_len,
        )
        all_stats.append(experiment_statistic)

    return ExperimentStats(
        N=N,
        rho=rho,
        service_dist=service_dist,
        QM=int(np.mean(list(map(lambda stat: stat.QM, all_stats)))),
        QA=float(np.mean(list(map(lambda stat: stat.QA, all_stats)))),
        QZ=int(np.mean(list(map(lambda stat: stat.QZ, all_stats)))),
        QT=float(np.mean(list(map(lambda stat: stat.QT, all_stats)))),
        QX=float(np.mean(list(map(lambda stat: stat.QX, all_stats)))),
        FR=float(np.mean(list(map(lambda stat: stat.FR, all_stats)))),
        FT=float(np.mean(list(map(lambda stat: stat.FT, all_stats)))),
        rejects=float(np.mean(list(map(lambda stat: stat.rejects, all_stats)))),
        reject_prob=float(np.mean(list(map(lambda stat: stat.reject_prob, all_stats)))),
        lambda_effective=float(np.mean(list(map(lambda stat: stat.lambda_effective, all_stats)))),
        std_wait_time=float(np.std(list(map(lambda stat: stat.QT, all_stats)), ddof=1)),
        std_service_time=float(np.std(list(map(lambda stat: stat.FT, all_stats)), ddof=1))
    )

def main():
    lam: float = 1 / 50
    use_cases_groups = [
        UseCaseGroup(
            name="Равномерное распределение ρ=0.6",
            description="Исследование для равномерного закона обслуживания с низкой нагрузкой",
            use_cases=[
                UseCase(rho=0.6, N=1500, service_dist=Distribution.UNIFORM, max_queue_len=1),
                UseCase(rho=0.6, N=47_500, service_dist=Distribution.UNIFORM, max_queue_len=1),
            ]
        ),
        UseCaseGroup(
            name="Равномерное распределение ρ=0.85",
            description="Исследование для равномерного закона обслуживания с высокой нагрузкой",
            use_cases=[
                UseCase(rho=0.85, N=1500, service_dist=Distribution.UNIFORM, max_queue_len=4),
                UseCase(rho=0.85, N=47_500, service_dist=Distribution.UNIFORM, max_queue_len=4),
            ]
        ),
        UseCaseGroup(
            name="Экспоненциальное распределение ρ=0.6",
            description="Исследование для экспоненциального закона обслуживания с низкой нагрузкой",
            use_cases=[
                UseCase(rho=0.6, N=1500, service_dist=Distribution.EXPONENTIAL, max_queue_len=1),
                UseCase(rho=0.6, N=47_500, service_dist=Distribution.EXPONENTIAL, max_queue_len=1),
            ]
        ),
        UseCaseGroup(
            name="Экспоненциальное распределение ρ=0.85",
            description="Исследование для экспоненциального закона обслуживания с высокой нагрузкой",
            use_cases=[
                UseCase(rho=0.85, N=1500, service_dist=Distribution.EXPONENTIAL, max_queue_len=5),
                UseCase(rho=0.85, N=47_500, service_dist=Distribution.EXPONENTIAL, max_queue_len=5),
            ]
        ),
        UseCaseGroup(
            name="Треугольное распределение ρ=0.6",
            description="Исследование для треугольного закона обслуживания с низкой нагрузкой",
            use_cases=[
                UseCase(rho=0.6, N=1500, service_dist=Distribution.TRIANGULAR, max_queue_len=1),
                UseCase(rho=0.6, N=47_500, service_dist=Distribution.TRIANGULAR, max_queue_len=1),
            ]
        ),
        UseCaseGroup(
            name="Треугольное распределение ρ=0.85",
            description="Исследование для треугольного закона обслуживания с высокой нагрузкой",
            use_cases=[
                UseCase(rho=0.85, N=1500, service_dist=Distribution.TRIANGULAR, max_queue_len=4),
                UseCase(rho=0.85, N=47_500, service_dist=Distribution.TRIANGULAR, max_queue_len=4),
            ]
        ),
    ]

    for group in use_cases_groups:
        print(f"\n{'=' * 60}")
        print(f"ГРУППА: {group.name}")
        group_results = []
        for use_case in group.use_cases:
            stats = run_experiments(
                N=use_case.N,
                rho=use_case.rho,
                lam=lam,
                service_dist=use_case.service_dist,
                max_queue_len=use_case.max_queue_len,
                repeats=1
            )
            group_results.append(stats)

        df_group_results = pd.DataFrame([s.__dict__ for s in group_results])
        df_group_results = df_group_results.set_index('N')
        print(df_group_results)

if __name__ == "__main__":
    main()

