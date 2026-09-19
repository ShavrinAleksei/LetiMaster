import os
import pickle


def save_results(results, filename):
    """Сохраняет результаты в файл"""
    os.makedirs('saved_results', exist_ok=True)
    with open(os.path.join('saved_results', filename), 'wb') as f:
        pickle.dump(results, f)
    print(f"Результаты сохранены: saved_results/{filename}")


def load_results(filename):
    """Загружает результаты из файла"""
    filepath = os.path.join('saved_results', filename)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            results = pickle.load(f)
        print(f"Результаты загружены: saved_results/{filename}")
        return results
    return None


def load_all_results():
    """Загружает все доступные сохранённые результаты"""
    results_dict = {}
    
    # Пробуем загрузить результаты для разных количеств агентов
    for name, filename in [('1 агент', 'results_1agent.pkl'),
                           ('2 агента', 'results_2agent.pkl'),
                           ('3 агента', 'results_3agent.pkl')]:
        data = load_results(filename)
        if data is not None:
            results_dict[name] = data
            print(f"Загружены результаты: {name}")
        else:
            print(f"Загружены результаты: {name} {filename}", data)
    
    return results_dict
