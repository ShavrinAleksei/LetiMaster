#!/usr/bin/zsh

# Проверка наличия хотя бы одного аргумента
if [ $# -eq 0 ]; then
    echo "Ошибка: опция не указана."
    echo "Использование: $0 { -p | -l | -z | -a }"
    exit 1
fi

# Обработка первого аргумента
case "$1" in
    -p)
        echo "Версия Python:"
        python3 --version
        ;;
    -l)
        echo "Версия Linux (дистрибутив):"
        grep -E "^(NAME|VERSION)=" /etc/os-release
        ;;
    -z)
        echo "Zen of Python:"
        python3 -c "import this"
        ;;
    -a)
        echo "Разработчик скрипта: Шаврин Алексей Павлович"
        ;;
    *)
        echo "Ошибка: неверная опция '$1'."
        echo "Допустимые опции: -p, -l, -z, -a"
        exit 1
        ;;
esac

exit 0