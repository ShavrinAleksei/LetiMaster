
import matplotlib.pyplot as plt
import numpy as np

def parse_data_to_format(complexities: list[int], processes_order: list[int]) -> dict:
    """
    Парсит данные из файлов в формат: {сложность: [средние_значения_времени_по_процессам]}
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
                    if len(parts) >= 2:
                        proc = int(parts[0])
                        avg_time = float(parts[1])  # среднее время
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
    for proc in processes:
        field_sizes = []
        times = []
        
        for size in sorted(data.keys()):
            idx = processes.index(proc)
            # Проверяем, есть ли данные для этого процесса и этого размера матрицы
            if idx < len(data[size]):
                field_sizes.append(size)
                times.append(data[size][idx])
        
        if field_sizes and times:
            plt.plot(field_sizes, times, 'o-', label=f'{proc} процессов', linewidth=2, markersize=8)
    
    plt.xlabel('Размер матрицы (N)')
    plt.ylabel('Время выполнения (мс)')
    plt.title('Зависимость времени от сложности задачи')
    plt.legend(loc='lower right', framealpha=0.7)
    plt.grid(True, alpha=0.3)
    plt.yscale('log')
    plt.xticks(sorted(data.keys()))
    plt.savefig('performance2.png', dpi=300, bbox_inches='tight')

    
    # График 2: По количеству процессов
    # plt.subplot(1, 2, 2)
    # for field_size in sorted(data.keys()):
    #     valid_proc = processes[:len(data[field_size])]
    #     plt.plot(valid_proc, data[field_size], 's-', label=f'{field_size}')
    
    # plt.xlabel('Количество процессов')
    # plt.ylabel('Время (мс)')
    # plt.title('Зависимость времени от числа процессов')
    # plt.legend()
    # plt.legend(loc='lower right', framealpha=0.9)
    # plt.grid(True)
    # plt.xscale('log')
    # plt.yscale('log')
    # plt.xticks(processes, labels=[str(p) for p in processes])
    # plt.tight_layout()
    # plt.savefig('performance.png', dpi=300, bbox_inches='tight')

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
        print(speedups)
        available_processes = processes[:len(times)]
        plt.plot(available_processes, speedups, 'o-', linewidth=1.5, markersize=4, 
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

def plot_experimental_vs_theoretical(data, processes=2):
    """
    Построение графика времени выполнения для 2 процессов:
    data: словарь {размер_матрицы: [время_для_1_процесса, время_для_2_процессов, ...]}
    """
    matrix_sizes = sorted(data.keys())
    experimental_times = [data[size][1] if len(data[size]) > 1 else None for size in matrix_sizes]

    # Рассчитаем теоретическое время для 2 процессов
    T1_times = [data[size][0] for size in matrix_sizes]  # последовательное время
    theoretical_times = [T1/2 for T1 in T1_times]       # идеальное ускорение на 2 процессах

    plt.figure(figsize=(10,6))
    plt.plot(matrix_sizes, experimental_times, 'o-', label='Экспериментальное время (2 процесса)', linewidth=2)
    plt.plot(matrix_sizes, theoretical_times, 's--', label='Теоретическое время (идеальное)', linewidth=2)

    plt.xlabel('Размер матрицы (N)')
    plt.ylabel('Время выполнения (мс)')
    plt.title('Сравнение экспериментального и теоретического времени на 2 процессах')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.xticks(matrix_sizes)
    plt.yscale('log')
    plt.tight_layout()
    plt.savefig('theor_vs_practic.png', dpi=300, bbox_inches='tight')
    # plt.show()

def main():
    complexities = [10, 50, 100, 200, 500, 1000, 10000]
    processes = [1, 2, 5, 10, 25, 50]
    # data = parse_data_to_format(complexities, processes)
    # print(data)
    # data_clean = {}
    # for complexity, times in data.items():
    #     data_clean[complexity] = [round(float(t), 4) for t in times]
    data_clean = {
        10: [0.0084, 0.5175, 7.1467, 10.0372],
        50: [1.1247, 1.3571, 2.905, 8.0809, 43.7621, 145.921],
        100: [9.4622, 4.3881, 10.6226, 18.4496, 35.0732, 128.983], 
        200: [69.8828, 19.421, 10.1278, 20.0242, 45.2051, 79.9205], 
        500: [1020.24, 316.57, 121.197, 168.037, 240.19, 340.298],
        1000: [8047.735, 2936.84, 2130.52, 1379.815, 1473.485, 2019.89]
    }
    print(data_clean)
    # plot_simple_performance(data_clean, processes)
    # plot_simple_speedup(data_clean, processes)
    plot_experimental_vs_theoretical(data_clean)


if __name__ == "__main__":
    main()