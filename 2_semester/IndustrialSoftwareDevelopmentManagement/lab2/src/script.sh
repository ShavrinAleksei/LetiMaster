#!/usr/bin/zsh

# Проверка наличия необходимых файлов
if [[ ! -f "my_file.txt" ]]; then
    echo "Ошибка: файл my_file.txt не найден в текущей директории."
    exit 1
fi

if [[ ! -f "messages.txt" ]]; then
    echo "Ошибка: файл messages.txt не найден в текущей директории."
    exit 1
fi

# Создание директорий и файлов для каждого имени из my_file.txt
while IFS= read -r name; do
    [[ -z "$name" ]] && continue

    mkdir -p "$name"
    touch "$name/cherry_pie.sh" "$name/good_coffee.sh"
    mkdir -p "$name/post_box"
    cp messages.txt "$name/post_box/"
done < my_file.txt

echo "Директории и файлы успешно созданы."

# Запрос сообщения от пользователя
echo "Введите сообщение (одна строка):"
read -r user_message

if [[ -z "$user_message" ]]; then
    echo "Сообщение не введено. Ничего не будет добавлено."
    exit 0
fi

# Добавление сообщения во все скопированные файлы messages.txt
while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    target_file="$name/post_box/messages.txt"
    if [[ -f "$target_file" ]]; then
        echo "\n$user_message" >> "$target_file"
    else
        echo "Предупреждение: $target_file не найден, пропускаем."
    fi
done < my_file.txt

echo "Готово!"
