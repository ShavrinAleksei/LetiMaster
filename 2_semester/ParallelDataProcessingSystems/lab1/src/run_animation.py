from navigation import Navigation
from visualize import Visualizer

def main():
    """
    Простой запуск анимации с выводом результата в консоль.
    """
    MAP_FILE = "citymap.txt"
    START_POS = None                   # None = найдет автоматически первую точку с цифрой 2
    GOAL_POS = None                    # None = найдет автоматически точку с цифрой 4
    SPAWN_PROB = 0.1                  # вероятность появления ботов (0.01, 0.03, 0.05, 0.08)
    STRATEGY_WEIGHTS = [0.25, 0.25, 0.25, 0.25]  # uniform
    OUTPUT_FILE = "episode_animation.gif"
    
    # Загружаем карту
    nav = Navigation(None)
    grid = nav.load_map(MAP_FILE)
    print(f"Карта загружена. Размер: {grid.shape}")
    
    # Автоматически находим старт и цель
    START_POS, GOAL_POS = nav.find_start_and_goal()
    
    # Проверки
    if START_POS is None:
        print("Ошибка: на карте нет стартовой точки (цифра 2)")
        return
    if GOAL_POS is None:
        print("Ошибка: на карте нет цели (цифра 4)")
        return
    start = START_POS[0]
    # Вывод настроек
    print(f"Стартовая позиция: {start}")
    print(f"Цель: {GOAL_POS}")
    print(f"Вероятность спавна ботов: {SPAWN_PROB}")
    print(f"Стратегия: {STRATEGY_WEIGHTS}")
    print(f"Выходной файл: {OUTPUT_FILE}")
    
    # Запускаем анимацию
    visualizer = Visualizer(grid)
    
    print("Запуск симуляции...")
    visualizer.generate_animation(
        start_pos=start,
        goal_pos=GOAL_POS,
        spawn_prob=SPAWN_PROB,
        strategy_weights=STRATEGY_WEIGHTS,
        filename=OUTPUT_FILE
    )

if __name__ == "__main__":
    main()