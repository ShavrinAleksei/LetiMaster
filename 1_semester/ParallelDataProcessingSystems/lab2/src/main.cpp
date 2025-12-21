#include <iostream>
#include <vector>
#include <mpi.h>
#include <cstdlib>
#include <ctime>
#include <fstream>
#include <numeric>
#include <algorithm>

#define COMPLEXITY 30000

void complexComputation(int iterations) {
    long long counter = 0;
    for (int i = 0; i < iterations; i++) {
        counter++;
    }
}

void processTask(int rank, int size) {
    std::srand(std::time(nullptr) + rank);
    double random_number = (std::rand() % 1000) / 10.0;

    complexComputation(COMPLEXITY);
    
    std::cout << "Процесс " << rank << ": мое число = " << random_number << std::endl;
    
    std::vector<double> all_numbers;
    if (rank == 0) {
        all_numbers.resize(size);
    }

    MPI_Gather(&random_number, 1, MPI_DOUBLE, 
               all_numbers.data(), 1, MPI_DOUBLE, 
               0, MPI_COMM_WORLD);
    
    if (rank == 0) {
        std::cout << "\n=== РЕЗУЛЬТАТ ===" << std::endl;
        std::cout << "Числа в порядке возрастания рангов процессов:" << std::endl;
        
        for (int i = 0; i < size; i++) {
            std::cout << "Процесс " << i << ": " << all_numbers[i] << std::endl;
        }
    }
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    double startTime = MPI_Wtime();
    processTask(rank, size);
    double endTime = MPI_Wtime();
    double processTime = (endTime - startTime) * 1000;
    
    std::vector<double> allTimes;
    if (rank == 0) {
        allTimes.resize(size);
    }
    MPI_Gather(&processTime, 1, MPI_DOUBLE, 
            allTimes.data(), 1, MPI_DOUBLE, 
            0, MPI_COMM_WORLD);
    
    if (rank == 0) {
        double maxTime = *std::max_element(allTimes.begin(), allTimes.end());
        double avgTime = std::accumulate(allTimes.begin(), allTimes.end(), 0.0) / size;
        
        std::cout << "\n=== РЕЗУЛЬТАТЫ ДЛЯ " << size << " ПРОЦЕССОВ ===" << std::endl;
        std::cout << "Максимальное время: " << maxTime << " мс" << std::endl;
        std::cout << "Среднее время: " << avgTime << " мс" << std::endl;

        std::ofstream file("results_30000.txt", std::ios::app);
        if (file.is_open()) {
            std::cout << "open" << std::endl;
            file << size << " " << maxTime << " " << avgTime << std::endl;
            file.close();
        }
    }
    MPI_Finalize();
    
    return 0;
}