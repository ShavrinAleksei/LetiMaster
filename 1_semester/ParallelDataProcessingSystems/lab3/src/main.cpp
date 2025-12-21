#include <mpi.h>
#include <iostream>
#include <vector>
#include <algorithm>
#include <numeric>
#include <fstream>

void processTask(int world_rank, int world_size) {
    int N, A;
    
    if (world_rank % 2 == 0) {
        N = 1;
    } else {
        N = 2;
    }

    A = world_rank * 10;
    std::cout << "Process " << world_rank << " (A = " << A << ", N = " << N << ")" << std::endl;

    MPI_Comm group_comm;
    MPI_Comm_split(MPI_COMM_WORLD, N, world_rank, &group_comm);
    
    int group_rank, group_size;
    MPI_Comm_rank(group_comm, &group_rank);
    MPI_Comm_size(group_comm, &group_size);
    
    std::vector<int> gathered_A(group_size);
    MPI_Allgather(&A, 1, MPI_INT, 
                  gathered_A.data(), 1, MPI_INT, 
                  group_comm);
    
    std::cout << "Process " << world_rank << " (N=" << N << "): ";
    std::cout << "Received values: ";
    for (int i = 0; i < group_size; i++) {
        std::cout << gathered_A[i];
        if (i < group_size - 1) std::cout << " ";
    }
    std::cout << std::endl;

    MPI_Comm_free(&group_comm);
}

void getTimeStatistic(int rank, int size, double processTime) {
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

        std::ofstream file("results.txt", std::ios::app);
        if (file.is_open()) {
            file << size << " " << maxTime << " " << avgTime << std::endl;
            file.close();
            std::cout << "Результаты записаны в results.txt" << std::endl;
        } else {
            std::cout << "Ошибка открытия файла!" << std::endl;
        }
    }
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    
    int world_rank, world_size;
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);

    double startTime = MPI_Wtime();
    processTask(world_rank, world_size);
    double endTime = MPI_Wtime();
    double processTime = (endTime - startTime) * 1000;

    getTimeStatistic(world_rank, world_size, processTime);
    
    MPI_Finalize();
    return 0;
}