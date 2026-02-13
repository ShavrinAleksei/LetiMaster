import matplotlib.pyplot as plt
import numpy as np


def plot_simple_performance(data, processes):
    plt.figure(figsize=(12, 5))
    
    # График 1: По размеру поля
    plt.subplot(1, 2, 1)
    for proc in processes:
        idx = processes.index(proc)
        field_sizes = sorted(data.keys())
        times = [data[fs][idx] for fs in field_sizes if idx < len(data[fs])]
        if times:
            plt.plot(field_sizes, times, 'o-', label=f'{proc} процессов')
    
    plt.xlabel('Размер поля')
    plt.ylabel('Время (мс)')
    plt.title('Зависимость времени от размеров поля')
    plt.legend()
    plt.grid(True)
    
    # График 2: По количеству процессов
    plt.subplot(1, 2, 2)
    for field_size in sorted(data.keys()):
        valid_proc = processes[:len(data[field_size])]
        plt.plot(valid_proc, data[field_size], 's-', label=f'{field_size}×{field_size}')
    
    plt.xlabel('Количество процессов')
    plt.ylabel('Время (мс)')
    plt.title('Зависимость времени от числа процессов')
    plt.legend()
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
                label=f'Поле {field_size}×{field_size}')
    
    plt.xlabel('Количество процессов')
    plt.ylabel('Ускорение Sp = T₁ / Tₚ')
    plt.title('Сравнение идеального и реального ускорения')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.xticks(processes)
    plt.savefig('simple_speedup.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    data = {
        10: [8.7, 16.4, 35.0, 90.3, 144, 243, 322.8, 399.3, 558.7, 924.8, 1065],
        20: [45.6, 47.9, 76.0, 132, 346, 596, 666.8, 785.2, 1375, 2688, 3470],
        30: [82.3, 87.8, 103, 161, 446, 856, 1245, 1450, 1643, 2970, 9190],
        40: [114, 123, 134.2, 221.9, 535.8, 1093, 1598.6, 3029, 3992.7, 5165.6, 13395]
    }
    processes = [2, 3, 4, 5, 6, 8, 10, 12, 16, 24, 32]
    plot_simple_performance(data, processes)
    plot_simple_speedup(data, processes)


if __name__ == "__main__":
    main()
