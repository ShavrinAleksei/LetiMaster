import matplotlib.pyplot as plt
import numpy as np
import os
import imageio.v2 as imageio
from map_utils import load_map
from result_utils import load_all_results
from simulator import Simulator

AGENT_COLOR = "#ff0000"
COLLISION_COLLOR = "#000000"
BOT_COLOR = "#32cfff"
COLOR_MAP = {
    0: "#777580",
    1: "#1a1a2e",
    2: "#00ff26",
    3: "#bac43a",
    4: "#ff8235",
}

class Visualizer:
    def __init__(self):
        self.color_map = COLOR_MAP
        self.agent_color = AGENT_COLOR
        self.collision_color = COLLISION_COLLOR
        self.bot_color = BOT_COLOR


    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return [int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4)]

    def draw_frame(self, step, grid, agent_positions, bot_positions, collision=False):
        """Отрисовывает кадр и возвращает изображение (без сохранения)"""
        h, w = grid.shape
        img = np.ones((h, w, 3))

        # Красим карту
        for y in range(h):
            for x in range(w):
                val = grid[y, x]
                img[y, x] = self.hex_to_rgb(self.color_map.get(val, self.color_map[0]))

        # Красим ботов
        for (bx, by) in bot_positions:
            if 0 <= by < h and 0 <= bx < w:
                img[by, bx] = self.hex_to_rgb(self.bot_color)

        # Отрисовка агентов
        for idx, (ax, ay) in enumerate(agent_positions):
            if 0 <= ay < h and 0 <= ax < w:
                if collision:
                    img[ay, ax] = self.hex_to_rgb(self.collision_color)
                else:
                    img[ay, ax] = self.hex_to_rgb(self.agent_color)

        return img

    def create_gif_from_history(self, history, grid, output_path, fps=10):
        """Создаёт GIF напрямую из history (без сохранения PNG)"""
        if not history:
            print(f"Нет кадров")
            return None
        
        frames = []
        for agent_positions, bot_positions, collision in history:
            img = self.draw_frame(0, grid, agent_positions, bot_positions, collision)
            frames.append((img * 255).astype(np.uint8))
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        imageio.mimsave(output_path, frames, duration=1000/fps, loop=0)
        print(f"GIF сохранён: {output_path}")
        return output_path

    def visualize_experiment(self, num_agents, strategy, folder_base='results'):
        """Запускает и сохраняет GIF одного запуска"""
        grid, shape, starts, goals, spawn_points = load_map('citymap.txt')
        p = 0.02
        
        # Создаём конфигурацию агентов
        agent_configs = []
        for i in range(num_agents):
            agent_configs.append({
                'start': starts[i % len(starts)],
                'goal': goals[0],
                'strategy': strategy
            })
        
        folder = os.path.join(folder_base, f'{num_agents}agents_{strategy}')
        os.makedirs(folder, exist_ok=True)
        
        env = Simulator(grid, agent_configs, spawn_points, p, max_steps=300)
        env.start_agent()
        
        # Обучаем если нужно
        if strategy in ('sarsa', 'q_learning'):
            print(f"Тренировка {num_agents} агентов ({strategy})...")
            for ep in range(300):
                eps = max(0.02, 0.3 * (1.0 - ep / 300))
                epsilons = [eps] * num_agents
                env.run_episode(epsilons=epsilons)
        
        # Запускаем эпизод
        epsilons = [0.0 if strategy in ('sarsa', 'q_learning') else None] * num_agents
        success, steps, history = env.run_episode(epsilons=epsilons, visualize=True)
        env.stop_agent()
        
        print(f"  {num_agents} агент(а), {strategy}: шагов={steps}, успех={success}")
        
        # Создаём GIF
        gif_path = os.path.join(folder, f'{num_agents}agents_{strategy}.gif')
        self.create_gif_from_history(history, grid, gif_path, fps=10)
        
        return success
    
    def plot_comparison_graphs(self, results_dict, p_vals, strategies):
        """
        Функция для построения графиков сравнения результатов
        """
        os.makedirs('results', exist_ok=True)
        
        # Настройки стилей для разных количеств агентов
        colors = ['blue', 'green', 'red']
        linestyles = ['-', '--', ':']
        
        # Линейные графики для каждой метрики
        for metric_name, metric_idx, ylabel in [
            ('avg_steps', 0, 'Среднее количество шагов'),
            ('success_rate', 1, 'Вероятность успеха')
        ]:
            plt.figure(figsize=(12, 7))
            
            for agents_i, (agents_label, results) in enumerate(results_dict.items()):
                for strat_i, strat in enumerate(strategies):
                    if strat in results:
                        vals = [results[strat][p][metric_idx] for p in p_vals]
                        plt.plot(p_vals, vals,
                                color=colors[strat_i],
                                marker='o',
                                linestyle=linestyles[agents_i],
                                linewidth=2,
                                markersize=6,
                                label=f'{agents_label}, {strat}')
            
            plt.xlabel("Вероятность генерации бота (p_gen)", fontsize=12)
            plt.ylabel(ylabel, fontsize=12)
            plt.title(f"{ylabel} для разных количеств агентов", fontsize=14)
            plt.grid(True, alpha=0.3)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
            plt.tight_layout()
            plt.savefig(f'results/compare_{metric_name}_all.png', bbox_inches='tight', dpi=150)
            plt.close()
        
        print(f"Графики сохранены в 'results'")

if __name__ == "__main__":
    visualizer = Visualizer()
    # Загружаем карту для проверки стартовых точек
    grid, shape, starts, goals, spawn_points = load_map('citymap.txt')
    print(f"Доступно стартовых точек: {len(starts)}")
    
    # Список комбинаций: (число_агентов, стратегия)
    combinations = []
    
    for num_agents in [1, 2, 3]:
        if num_agents > len(starts):
            print(f"Пропускаем {num_agents} агента (нужно {num_agents} стартов, есть {len(starts)})")
            continue
        for strategy in ['bot_like', 'sarsa', 'q_learning']:
            combinations.append((num_agents, strategy))
    
    # Создаем гиф анимации комбинаций экспериментов
    for num_agents, strategy in combinations:
        print(f"{num_agents} агент(а), стратегия {strategy}")
        visualizer.visualize_experiment(num_agents, strategy, folder_base='results')   
    print("Все GIF созданы!")

    # Строим графики результатов
    BOT_SPAWN_PROBS = [0.01, 0.03, 0.05]
    STRATEGIES = ['bot_like', 'sarsa', 'q_learning']
    results_dict = load_all_results()
    print(results_dict)
    if results_dict:
        print(f"Построение графиков для: {list(results_dict.keys())}")
        visualizer.plot_comparison_graphs(results_dict, BOT_SPAWN_PROBS, STRATEGIES)
    else:
        print("Нет сохранённых результатов. Сначала запустите эксперименты.")