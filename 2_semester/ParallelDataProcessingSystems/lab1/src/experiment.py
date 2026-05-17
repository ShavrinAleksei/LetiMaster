import csv
from simulator import Simulator

class Experiment:
    """Проведение экспериментов с разными параметрами"""
    
    def __init__(self, grid, goal_pos, start_points, spawn_rates, strategies, episodes_per_config=30):
        self.grid = grid
        self.goal_pos = goal_pos
        self.start_points = start_points
        self.spawn_rates = spawn_rates
        self.strategies = strategies
        self.episodes_per_config = episodes_per_config
    
    def run_batch(self, spawn_rate, strategy_name, strategy_weights):
        """Выполняет серию эпизодов для заданной конфигурации"""
        results = []
        sim = Simulator(self.grid, self.goal_pos, spawn_rate, strategy_weights)
        
        for _ in range(self.episodes_per_config):
            for start_pos in self.start_points:
                outcome = sim.run_episode(start_pos)
                outcome['spawn_rate'] = spawn_rate
                outcome['strategy'] = strategy_name
                outcome['start_pos'] = start_pos
                results.append(outcome)
        
        return results
    
    def save_to_csv(self, data, filename="experiment_results.csv"):
        """Сохраняет результаты в CSV файл"""
        if not data:
            return
        
        fields = data[0].keys()
        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(data)
        print("Результаты сохранены в " + filename)
    
    def run_all(self, output_file="experiment_results.csv"):
        """Запускает все эксперименты"""
        all_results = []
        
        for rate in self.spawn_rates:
            for name, weights in self.strategies.items():
                print(f"Запуск конфигурации: скорость={rate} стратегия={name}")
                batch = self.run_batch(rate, name, weights)
                all_results.extend(batch)
        
        self.save_to_csv(all_results, output_file)