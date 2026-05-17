import csv
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import multiprocessing as mp
from matplotlib.colors import ListedColormap, BoundaryNorm
from simulator import Simulator

class Visualizer:
    """Визуализация результатов и анимации"""
    
    def __init__(self, grid):
        self.grid = grid
    
    def load_results(self, filename="experiment_results.csv"):
        """Загружает данные эксперимента из CSV файла"""
        data = []
        with open(filename, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['steps'] = int(row['steps'])
                row['success'] = row['success'] == 'True'
                row['spawn_rate'] = float(row['spawn_rate'])
                data.append(row)
        return data
    
    def plot_metrics(self, data, output_dir="results"):
        """Строит графики зависимости шагов и вероятности успеха от скорости спавна"""
        os.makedirs(output_dir, exist_ok=True)
        
        strategies = sorted(list(set(r['strategy'] for r in data)))
        rates = sorted(list(set(r['spawn_rate'] for r in data)))
        
        avg_steps_data = {}
        success_probs_data = {}
        
        for strat in strategies:
            avg_steps_data[strat] = []
            success_probs_data[strat] = []
            
            for r in rates:
                subset = [d for d in data if d['strategy'] == strat and d['spawn_rate'] == r]
                if subset:
                    successful = [d for d in subset if d['success']]
                    avg = np.mean([d['steps'] for d in successful]) if successful else None
                    prob = len(successful) / len(subset)
                    avg_steps_data[strat].append(avg)
                    success_probs_data[strat].append(prob)
                else:
                    avg_steps_data[strat].append(None)
                    success_probs_data[strat].append(np.nan)
        
        # График среднего числа шагов
        plt.figure()
        for strat in strategies:
            # Фильтруем None значения
            clean_rates = []
            clean_steps = []
            for r, s in zip(rates, avg_steps_data[strat]):
                if s is not None and not np.isnan(s):
                    clean_rates.append(r)
                    clean_steps.append(s)
            
            if clean_rates:  # рисуем только если есть данные
                plt.plot(clean_rates, clean_steps, marker='o', label=strat)
        plt.xlabel("Вероятность появления ботов")
        plt.ylabel("Среднее число шагов")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(output_dir, "steps_vs_spawn.png"))
        plt.close()
        
        # График вероятности успеха
        plt.figure()
        for strat in strategies:
            plt.plot(rates, success_probs_data[strat], marker='s', label=strat)
        plt.xlabel("Вероятность появления ботов")
        plt.ylabel("Вероятность успешной доставки")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(output_dir, "success_vs_spawn.png"))
        plt.close()
        
        print("Графики сохранены в директории " + output_dir)
    
    def generate_animation(self, start_pos, goal_pos, spawn_prob, strategy_weights, filename="episode_animation.gif"):
        """Создает анимацию движения агента и ботов"""
        frames = []
        sim = Simulator(self.grid, goal_pos, spawn_prob, strategy_weights)
        shared = sim.init_shared_state(start_pos)
        
        lock = mp.Lock()
        barrier = mp.Barrier(3)
        
        agent_proc = mp.Process(target=sim.agent_worker, args=(shared, lock, barrier))
        bot_proc = mp.Process(target=sim.bot_worker, args=(shared, lock, barrier))
        
        agent_proc.start()
        bot_proc.start()
        
        max_steps = 200
        
        for _ in range(max_steps):
            try:
                barrier.wait(timeout=10.0)
            except Exception:
                break
            
            lock.acquire()
            sim.check_collisions(shared)
            
            base_grid = np.array(shared['grid']).copy()
            ax, ay = shared['agent']['pos']
            if 0 <= ax < len(self.grid) and 0 <= ay < len(self.grid[0]):
                base_grid[ax, ay] = 5
            
            for bot in shared['bots']:
                if bot.get('alive', True):
                    bx, by = bot['pos']
                    if 0 <= bx < len(self.grid) and 0 <= by < len(self.grid[0]):
                        base_grid[bx, by] = 6
            
            frames.append(base_grid)
            
            if shared['episode_done']:
                lock.release()
                break
            lock.release()
        
        agent_proc.join(timeout=5)
        bot_proc.join(timeout=5)
        
        if not frames:
            print("Кадры не записаны")
            return
        
        fig, ax = plt.subplots(figsize=(6, 6))
        cmap = ListedColormap(["#777580", "#1a1a2e", "#00ff26", "#bac43a", "#ff8235", "#ff0000", "#32cfff"])
        bounds = range(8)
        norm = BoundaryNorm(bounds, len(cmap.colors))
        
        im = ax.imshow(frames[0], cmap=cmap, norm=norm, origin="upper")
        ax.set_xticks([])
        ax.set_yticks([])
        
        def update(frame):
            im.set_array(frame)
            return [im]
        
        ani = anim.FuncAnimation(fig, update, frames=frames, interval=100, repeat=False)
        ani.save(filename, writer="pillow", fps=10)
        print("Анимация сохранена: " + filename)