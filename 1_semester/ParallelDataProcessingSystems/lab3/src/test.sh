#!/bin/bash

PROGRAM="./main"
RUNS=50  # Количество запусков для каждого числа процессов

# Тестируемые количества процессов
PROCESS_COUNTS="2 3 4 5 6 8 10 12 16 24 32"

for processes in $PROCESS_COUNTS; do
    echo "=== Тестируем $processes процессов ==="
    
    for ((run=1; run<=RUNS; run++)); do
        echo "  Запуск $run/$RUNS..."
        if [ $processes -le 6 ]; then
            # До 6 процессов - без oversubscribe (по числу ядер)
            mpirun -np $processes $PROGRAM 2>/dev/null | grep "РЕЗУЛЬТАТЫ" -A 2
        else
            # Больше 6 процессов - с oversubscribe
            mpirun -np $processes --oversubscribe $PROGRAM 2>/dev/null | grep "РЕЗУЛЬТАТЫ" -A 2
        fi
    done
    echo ""
done

echo "Все запуски завершены"