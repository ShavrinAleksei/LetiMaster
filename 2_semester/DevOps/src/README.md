# DevOps lab - Вариант 52

## Описание
Проект состоит из двух контейнеров:
- **app** — веб-приложение на Flask (пример из репозитория devops-examples)
- **tester** — контейнер для запуска тестов (pylint, prettier, интеграционные тесты)

## Переменные окружения (.env)
Файл .env располагается в папке `src` и содержит переменные окружения для контейнера `tester`.

```.env
TEST_STEPS=all
```

Допустимые значения переменной задают этапы тестирования:

* пусто — все тесты
* all — все тесты
* pylint — только pylint
* pyjslint — только pyjslint
* jslint — только jslint
* integration — только интеграционные
* pylint,prettier — комбинации через запятую

## Инструкция по запуску

## Где выполнять команды
Все команды выполняются из папки `src/` (там где лежит `docker-compose.yaml`):
```bash
cd src
```

### 1. Сборка образов
```bash
docker compose build
```

### 2. Запуск контейнеров
```bash

docker compose up
```

### 3. Проверка статуса контейнеров
```bash

docker compose ps
```

## Запуск тестов
### 1. Запуск всех тестов
```bash

docker compose exec tester bash /tester/scripts/test_all.sh
```

### 2. Запуск отдельных тестов
```bash

# Pylint (статический анализ по 10 критериям)
docker compose exec tester bash /tester/scripts/test_pylint.sh

# JS beautifier (jslint)
docker compose exec tester bash /tester/scripts/test_jslint.sh

# JS beautifier (pyjslint)
docker compose exec tester bash /tester/scripts/test_pyjslint.sh

# Интеграционные тесты (проверка кодов возврата)
docker compose exec tester bash /tester/scripts/test_integration.sh
```

## Просмотр логов тестов

Логи каждого теста сохраняются в `/logs` внутри контейнера `tester` и монтируются на хост в папку `./logs`:
```bash

# Логи pylint
docker compose exec tester cat /logs/pylint_stdout.log
docker compose exec tester cat /logs/pylint_stderr.log

# Логи JS beautifier (jslint)
docker compose exec tester cat /logs/jslint_stdout.log
docker compose exec tester cat /logs/jslint_stderr.log

# Логи JS beautifier (pyjslint)
docker compose exec tester cat /logs/pyjslint_stdout.log
docker compose exec tester cat /logs/pyjslint_stderr.log

# Логи интеграционных тестов
docker compose exec tester cat /logs/integration_stdout.log
docker compose exec tester cat /logs/integration_stderr.log
```

## Статический анализ (pylint)

Pylint проверяет код по 10 критериям:

| Код     | Название                         | Описание                                                                |
|---------|----------------------------------|-------------------------------------------------------------------------|
| `C0114` | missing-module-docstring         | В начале файла нет строки документации модуля                           |
| `C0116` | missing-function-docstring       | У функции/метода нет docstring                                          |
| `C0304` | missing-final-newline            | В конце файла отсутствует пустая строка                                 |
| `C0413` | wrong-import-position            | Импорт находится не в начале файла                                      |
| `C3001` | unnecessary-lambda-assignment    | Лямбда присвоена переменной, лучше использовать `def`                   |
| `W0601` | global-variable-undefined        | Использование `global` для переменной, не определенной на уровне модуля |
| `W0612` | unused-variable                  | Переменная обьявлена, но не используется                                |
| `W0613` | unused-argument                  | Аргумент функции не используется                                        |
| `W0622` | redefined-builtin                | Переопределение встроенной функции (например, `len`)                    |
| `E0602` | undefined-variable               | Использование неопределенной переменной                                 |

## Подключение по SSH к контейнеру app

### Генерация SSH ключей
Ключи необходимо раположите в папке `app/ssh/keys/` с названиями `app_key` и `app_key.pub`
```bash

ssh-keygen -t rsa -b 4096 -f app/ssh/keys/app_key -N ""
```

### Подключение по SSH

SSH доступен на порту 2222, аутентификация по публичному ключу:
```bash

ssh -p 2222 root@localhost -i app/ssh/keys/app_key
```