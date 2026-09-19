#!/usr/bin/zsh

# Определяем корневую директорию (родительскую по отношению к текущей)
root_dir="$(cd "$(dirname "$0")/.." && pwd)"

# Имя текущей директории (откуда запущен скрипт)
current_dir_name="$(basename "$(cd "$(dirname "$0")" && pwd)")"

# Находим все файлы cherry_pie.sh в корне
find "$root_dir" -type f -name "cherry_pie.sh" | while read -r target; do
    # Пропускаем сам файл, из которого запущен скрипт
    [[ "$target" == "$0" ]] && continue

    # Если файл пуст, заменяем его содержимым текущего скрипта
    if [[ ! -s "$target" ]]; then
        cp "$0" "$target"
        echo "Скопирован в $target"
    fi
done

# Логирование в white_lodge.txt в корневой папке
log_file="$root_dir/white_lodge.txt"
timestamp=$(date '+%Y-%m-%d %H:%M:%S')
echo "$timestamp $current_dir_name ordered a cherry pie" >> "$log_file"

echo "Готово. Запись добавлена в $log_file"
