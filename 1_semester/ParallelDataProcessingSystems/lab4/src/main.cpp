#include <mpi.h>
#include <iostream>
#include <vector>
#include <cassert>
#include <algorithm>
#include <numeric>
#include <fstream>

#define Multiplicity 3


bool isValidCountOfProcesses(int world_size, int world_rank) {
    return world_size <= Multiplicity || world_size % Multiplicity != 0;
}

std::vector<int> generateData(int my_col, int N) {
    std::vector<int> data(N);
    for (int i = 0; i < N; ++i) {
        data[i] = my_col * 100 + i;
    }
    return data;
}

void processTask(int world_size, int world_rank) {
    int N = world_size / Multiplicity;

    int dimSize = 2;
    int dims[dimSize] = {N, Multiplicity};
    int periods[dimSize] = {0, 0};
    int reorder = 0;
    MPI_Comm cart_comm;
    MPI_Cart_create(MPI_COMM_WORLD, dimSize, dims, periods, reorder, &cart_comm);

    int coords[dimSize];
    MPI_Cart_coords(cart_comm, world_rank, dimSize, coords);
    int my_row = coords[0];
    int my_col = coords[1];

    int remain_dims[dimSize] = {1, 0}; // keep rows, drop cols => получим комм. по столбцам
    MPI_Comm col_comm;
    MPI_Cart_sub(cart_comm, remain_dims, &col_comm);

    int sub_rank, sub_size;
    MPI_Comm_rank(col_comm, &sub_rank);
    MPI_Comm_size(col_comm, &sub_size);
    assert(sub_size == N);

    int root_in_subcomm = 0;
    std::vector<int> sendbuf;
    int recv_value = 0;

    bool is_global_main = (my_row == 0);
    if (is_global_main) {
        sendbuf = generateData(my_col, N);
    }

    MPI_Scatter(
        is_global_main ? sendbuf.data() : nullptr, 
        1,
        MPI_INT,
        &recv_value,
        1,
        MPI_INT,
        root_in_subcomm,
        col_comm
    );

    std::cout << "GlobalRank=" << world_rank
                << " (row=" << my_row << ", col=" << my_col << ") "
                << "sub_rank=" << sub_rank
                << " received=" << recv_value << std::endl;

    MPI_Comm_free(&col_comm);
    MPI_Comm_free(&cart_comm);
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

    int world_size, world_rank;
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);

    if (isValidCountOfProcesses(world_size, world_rank)) {
        if (world_rank == 0) {
            std::cerr << "Error: the number of processes must be a multiple of " << Multiplicity << " and > " << Multiplicity << ". Current number of processes = "
                      << world_size << std::endl;
        }
        MPI_Finalize();
        return 0;
    }

    double startTime = MPI_Wtime();
    processTask(world_size, world_rank);
    double endTime = MPI_Wtime();
    double processTime = (endTime - startTime) * 1000;
    MPI_Barrier(MPI_COMM_WORLD);
    
    getTimeStatistic(world_rank, world_size, processTime);

    MPI_Finalize();
    return 0;
}
