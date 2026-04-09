# ROS Turtle Simulator on RabbitMQ

## Установка зависимостей

### Установка пакетного менеджера uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Инициализация venv, активация и синхронизация зависимостей

```bash
uv venv && source .venv/bin/activate && uv sync
```

## Запуск
### RabbitMQ в Docker

```bash
docker run -d --name rabbitmq -p 5672:5672 rabbitmq:3
```

### Симулятор TurtlrSim

```bash
uv run python -m turtle_sim \
  --host localhost \
  --turtle-name turtle1 \
  --linear-speed 3.0 \
  --angular-speed 2.5 \
  --start-x 5.0 \
  --start-y 5.0
```

### Сталкеры

```bash
uv run python -m stalker_chain \
  --host localhost \
  --victim-turtle turtle1 \
  --num-followers 2 \
  --speed 0.9
```

## Управление turtle1

↑ / W	Вперед

↓ / S	Назад

← / A	Поворот налево

→ / D	Поворот направо

**PS: Можно одновременно двигаться и поворачивать**

**PS2: Есть супер буст x2 к скорости при одновременном нажатии клавиш управления стрелками и символами в соответствуюзем направлении**
