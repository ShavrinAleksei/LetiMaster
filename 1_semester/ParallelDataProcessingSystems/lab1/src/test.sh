#!/bin/bash

PROGRAM="./sea_battle"
RUNS=30  # Количество запусков для каждого числа процессов

# Тестируемые количества процессов
PROCESS_COUNTS="2 3 4 5 6 8 10 12 16 24 32"

for processes in $PROCESS_COUNTS; do
    echo "=== Тестируем $processes процессов ==="
    
    for ((run=1; run<=RUNS; run++)); do
        echo "  Запуск $run/$RUNS..."
        mpirun -np $processes --oversubscribe $PROGRAM 2>/dev/null | grep "РЕЗУЛЬТАТЫ" -A 2
    done
    echo ""
done

echo "Все запуски завершены"