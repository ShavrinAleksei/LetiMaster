#!/bin/bash

PROGRAM="./main"
RUNS=10 # Количество запусков для каждого числа процессов

# Тестируемые количества процессов
PROCESS_COUNTS="50 25 10 5 2 1"

for processes in $PROCESS_COUNTS; do
    echo "=== Тестируем $processes процессов ==="
    
    for ((run=1; run<=RUNS; run++)); do
        echo "  Запуск $run/$RUNS..."
        if [ $processes -le 6 ]; then
            mpirun -np $processes $PROGRAM 2>/dev/null | grep "РЕЗУЛЬТАТЫ" -A 2
        else
            mpirun -np $processes --oversubscribe $PROGRAM 2>/dev/null | grep "РЕЗУЛЬТАТЫ" -A 2
        fi
    done
    echo ""
done

echo "Все запуски завершены"