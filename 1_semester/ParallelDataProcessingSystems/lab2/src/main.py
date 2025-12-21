
import matplotlib.pyplot as plt
import numpy as np

def parse_data_to_format(complexities: list[int], processes_order: list[int]) -> dict:
    """
    Парсит данные из файлов в формат: {сложность: [средние_значения_времени_по_процессам]}
    Порядок процессов: [2, 3, 4, 5, 6, 8, 10, 12, 16, 24, 32]
    """
    result = {}
    
    for complexity in complexities:
        filename = f"results_{complexity}.txt"
        
        # Словарь для хранения всех измерений по процессам
        process_measurements = {p: [] for p in processes_order}
        
        try:
            with open(filename, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        proc = int(parts[0])
                        avg_time = float(parts[2])  # среднее время
                        if proc in process_measurements:
                            process_measurements[proc].append(avg_time)
            
            # Вычисляем средние значения для каждого процесса в нужном порядке
            median_times = []
            for proc in processes_order:
                measurements = process_measurements[proc]
                if measurements:  # если есть измерения
                    median_times.append(np.median(measurements))
                else:
                    median_times.append(None)
            
            result[complexity] = median_times
            print(f"Сложность {complexity}: обработано {sum(len(v) for v in process_measurements.values())} измерений")
            
        except FileNotFoundError:
            print(f"Файл {filename} не найден")
            continue
    
    return result

def plot_simple_performance(data, processes):
    plt.figure(figsize=(12, 5))
    
    # График 1: По сложности
    plt.subplot(1, 2, 1)
    for proc in processes:
        idx = processes.index(proc)
        field_sizes = sorted(data.keys())
        times = [data[fs][idx] for fs in field_sizes if idx < len(data[fs])]
        if times:
            plt.plot(field_sizes, times, 'o-', label=f'{proc} процессов')
    
    plt.xlabel('Сложность задачи')
    plt.ylabel('Время (мс)')
    plt.title('Зависимость времени от сложности задачи')
    plt.legend()
    plt.legend(loc='upper left', framealpha=0.5)
    plt.grid(True)
    
    # График 2: По количеству процессов
    plt.subplot(1, 2, 2)
    for field_size in sorted(data.keys()):
        valid_proc = processes[:len(data[field_size])]
        plt.plot(valid_proc, data[field_size], 's-', label=f'{field_size}')
    
    plt.xlabel('Количество процессов')
    plt.ylabel('Время (мс)')
    plt.title('Зависимость времени от числа процессов')
    plt.legend()
    plt.legend(loc='upper left', framealpha=0.9)
    plt.grid(True)
    plt.xscale('log')
    plt.xticks(processes, labels=[str(p) for p in processes])
    plt.tight_layout()
    plt.savefig('performance.png', dpi=300, bbox_inches='tight')

def plot_simple_speedup(data, processes):
    """
    Простой график ускорения для всех размеров полей
    """
    plt.figure(figsize=(10, 6))
    
    # Идеальное ускорение
    plt.plot(processes, processes, 'k--', linewidth=2, label='Идеальное ускорение')
    
    # Реальное ускорение для каждого размера поля
    for field_size, times in data.items():
        # Базовое время (эмулируем T1)
        T1 = times[0] * processes[0]  # T1 = T2 * 2
        speedups = [T1 / time for time in times]
        plt.plot(processes, speedups, 'o-', linewidth=1.5, markersize=4, 
                label=f'Сложность {field_size}')
    
    plt.xlabel('Количество процессов')
    plt.ylabel('Ускорение Sp = T₁ / Tₚ')
    plt.title('Сравнение идеального и реального ускорения')
    plt.legend()
    plt.legend(loc='upper left', framealpha=0.9)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.xticks(processes)
    plt.savefig('simple_speedup.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    complexities = [0, 10000, 20000, 30000]
    processes = [2, 3, 4, 5, 6, 8, 10, 12, 16, 24, 32]
    data = parse_data_to_format(complexities, processes)
    data_clean = {}
    for complexity, times in data.items():
        data_clean[complexity] = [round(float(t), 2) for t in times]

    print(data_clean)
    plot_simple_performance(data, processes)
    plot_simple_speedup(data, processes)


if __name__ == "__main__":
    main()