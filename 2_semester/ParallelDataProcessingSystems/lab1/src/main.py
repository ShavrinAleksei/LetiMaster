from navigation import Navigation
from experiment import Experiment
from visualize import Visualizer

def main():
    # Общая конфигурация
    MAP_FILE = "citymap.txt"
    START_POS = None                   # None = найдет автоматически первую точку с цифрой 2
    GOAL_POS = None                    # None = найдет автоматически точку с цифрой 4
    SPAWN_RATES = [0.01, 0.03, 0.05, 0.08]
    STRATEGIES = {
        'uniform': [0.25, 0.25, 0.25, 0.25],
        'straight_focus': [0.50, 0.20, 0.20, 0.10],
        'cautious': [0.10, 0.10, 0.10, 0.70]
    }
    EPISODES_PER_CONFIG = 30
    EXPERIMENT_RESULT_FILE = "experiment_results.csv"

    # Загружаем карту
    nav = Navigation(None)
    grid = nav.load_map(MAP_FILE)
    
    print(f"Карта загружена. Размер: {grid.shape}")
    
    # Автоматически находим стартовые точки и цель на карте
    START_POS, GOAL_POS = nav.find_start_and_goal()
    
    if not START_POS:
        print("Ошибка: на карте нет стартовой точки (цифра 2)")
        return
    if not GOAL_POS:
        print("Ошибка: на карте нет цели (цифра 4)")
        return
    
    print(f"Найдены стартовые точки: {START_POS}")
    print(f"Найдена цель: {GOAL_POS}")
    
   
    # Запуск экспериментов
    experiment = Experiment(grid, GOAL_POS, START_POS, SPAWN_RATES, STRATEGIES, episodes_per_config=EPISODES_PER_CONFIG)
    experiment.run_all(EXPERIMENT_RESULT_FILE)
    
    # Визуализация результатов
    visualizer = Visualizer(grid)
    data = visualizer.load_results(EXPERIMENT_RESULT_FILE)
    if data:
        visualizer.plot_metrics(data)
    else:
        print("Нет данных для визуализации")

if __name__ == "__main__":
    main()