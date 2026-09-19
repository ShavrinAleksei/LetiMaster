import json
import csv
import os


def read_csv(file_path):
    """Читает CSV файл и возвращает список строк."""
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        data = [row for row in reader]
    return data


def convert_to_json(data, output_file):
    """Конвертирует данные из CSV в JSON."""
    # Преобразуем список строк в список словарей (первая строка - заголовки)
    headers = data[0]
    json_data = []

    for row in data[1:]:
        item = {}
        for i, value in enumerate(row):
            item[headers[i]] = value
        json_data.append(item)

    with open(output_file, 'w') as f:
        json.dump(json_data, f, indent=2)

    return True


if __name__ == "__main__":
    input_csv = "data.csv"
    output_json = "data.json"

    # Проверка существования входного файла
    if not os.path.exists(input_csv):
        print(f"Ошибка: файл {input_csv} не найден!")
        exit(1)

    data = read_csv(input_csv)
    convert_to_json(data, output_json)

    # Вывод количества записей (кроме заголовка)
    print(f"Конвертировано записей: {len(data)-1}")
    print("Готово!")
    