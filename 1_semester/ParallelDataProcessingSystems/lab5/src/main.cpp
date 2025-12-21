#include <mpi.h>
#include <vector>
#include <iostream>
#include <random>
#include <algorithm>
#include <stdexcept>
#include <fstream>
#include <string>

#define MATRIX_SIZE 10

using Matrix = std::vector<int>;

inline int& at(Matrix& m, int N, int i, int j) {
    return m[i * N + j];
}
inline int at(const Matrix& m, int N, int i, int j) {
    return m[i * N + j];
}

void printMatrix(const Matrix& M, int N, const std::string& name) {
    std::cout << "Матрица " << name << " (" << N << "x" << N << "):\n";
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            std::cout << at(M, N, i, j) << " ";
        }
        std::cout << "\n";
    }
}

Matrix generateRandomMatrix(int N, int minVal = 0, int maxVal = 9, unsigned seed = 42) {
    Matrix M(N * N);
    std::mt19937 rng(seed);
    std::uniform_int_distribution<int> dist(minVal, maxVal);
    for (int i = 0; i < N * N; ++i) M[i] = dist(rng);
    return M;
}

void multiplySequential(const Matrix& A, const Matrix& B, Matrix& C, int N) {
    C.assign(N * N, 0);
    for (int i = 0; i < N; ++i) {
        for (int k = 0; k < N; ++k) {
            int aik = at(A, N, i, k);
            for (int j = 0; j < N; ++j) {
                at(C, N, i, j) += aik * at(B, N, k, j);
            }
        }
    }
}

void checkDims(int dims[2], int N, int world_rank, MPI_Comm comm) {
    if (N % dims[0] != 0 || N % dims[1] != 0) {
        if (world_rank == 0) {
            std::cerr << "Ошибка: N = " << N
                      << " должно делиться и на dims[0] = " << dims[0]
                      << " и на dims[1] = " << dims[1] << "\n";
            std::cerr << "Выберите другое N или число процессов.\n";
        }
        MPI_Abort(comm, 1);
    }
}

void transposeMatrix(Matrix& M, int N) {
    for (int i = 0; i < N; ++i) {
        for (int j = i + 1; j < N; ++j) {
            std::swap(M[i * N + j], M[j * N + i]);
        }
    }
}

Matrix localMultiplyBlock(
    const Matrix& A_local,
    const Matrix& B_local,
    int N,
    int rowsPerProc,
    int colsPerProc
) {
    Matrix C_local(rowsPerProc * colsPerProc, 0);
    for (int i = 0; i < rowsPerProc; i++) {
        for (int k = 0; k < N; k++) {
            int aik = A_local[i * N + k];
            for (int j = 0; j < colsPerProc; j++) {
                C_local[i * colsPerProc + j] += aik * B_local[j * N + k];
            }
        }
    }
    return C_local;
}

void placeBlockIntoGlobal(
    const Matrix& local,
    Matrix& global,
    int N,
    int blockRows,
    int blockCols,
    int rowStart,
    int colStart
) {
    for (int i = 0; i < blockRows; ++i) {
        for (int j = 0; j < blockCols; ++j) {
            int globalRow = rowStart + i;
            int globalCol = colStart + j;
            at(global, N, globalRow, globalCol) = local[i * blockCols + j];
        }
    }
}

void printLocalMatrix(
    const Matrix& C_local, 
    int world_rank, 
    int rowsPerProc, 
    int colsPerProc, 
    const std::string& matrixName = "C_local"
) {
    std::cout << "Process " << world_rank << " " << matrixName << " (" 
              << rowsPerProc << "x" << colsPerProc << "):" << std::endl;
    
    for (int i = 0; i < rowsPerProc; ++i) {
        for (int j = 0; j < colsPerProc; ++j) {
            std::cout << C_local[i * colsPerProc + j] << " ";
        }
        std::cout << std::endl;
    }
    std::cout << std::endl;
}

void multiplyStriped2D(
    const Matrix& A, 
    const Matrix& B, 
    Matrix& C, 
    int N, 
    int world_size, 
    int world_rank,
    MPI_Comm comm
) {
    // Создаём 2D-декартову топологию
    MPI_Comm cart_comm; 
    int dimSize = 2;
    int dims[dimSize] = {0, 0}; 
    MPI_Dims_create(world_size, dimSize, dims); 
    int periods[dimSize] = {0, 0}; 
    int reorder = 0; 
    MPI_Cart_create(comm, dimSize, dims, periods, reorder, &cart_comm);

    // Проверяем делимость N на число блоков checkDims(dims, N, world_rank);
    checkDims(dims, N, world_rank, comm);

    int cart_rank;
    MPI_Comm_rank(cart_comm, &cart_rank);

    int coords[dimSize];
    MPI_Cart_coords(cart_comm, cart_rank, dimSize, coords);
    int my_row = coords[0];
    int my_col = coords[1];
    bool is_grid_root = (my_row == 0 && my_col == 0);

    MPI_Comm rowComm;
    int remain_dims_row[2] = {0, 1};  
    MPI_Cart_sub(cart_comm, remain_dims_row, &rowComm);

    MPI_Comm colComm;
    int remain_dims_col[2] = {1, 0};
    MPI_Cart_sub(cart_comm, remain_dims_col, &colComm);

    int row_rank, row_size;
    MPI_Comm_rank(rowComm, &row_rank);
    MPI_Comm_size(rowComm, &row_size);

    int col_rank, col_size;
    MPI_Comm_rank(colComm, &col_rank);
    MPI_Comm_size(colComm, &col_size);

    int col_root = 0, row_root = 0;
    
    // Локальные буферы полос
    int rowsPerProc = N / dims[0];
    int colsPerProc = N / dims[1];
    Matrix A_local(rowsPerProc * N);
    Matrix B_local(colsPerProc * N);

    // Рассылаем полосы А по строкам первого столбца
    if (my_col == 0) {
        const int* sendbuf = is_grid_root ? A.data() : nullptr;
        MPI_Scatter(sendbuf, rowsPerProc * N, MPI_INT, A_local.data(), rowsPerProc * N, MPI_INT, col_root, colComm);
        // printLocalMatrix(A_local, world_rank, rowsPerProc, N, "A recieved " + std::to_string(my_row) + " " + std::to_string(my_col));
    }
    // Рассылаем полученные полосы А по всем столбцам в строке
    MPI_Bcast(A_local.data(), rowsPerProc * N, MPI_INT, row_root, rowComm);

    // Рассылаем полосы B по столбцам первой строки
    if (my_row == 0) {
        const int* sendbuf = is_grid_root ? B.data() : nullptr;
        MPI_Scatter(sendbuf, colsPerProc * N, MPI_INT, B_local.data(), colsPerProc * N, MPI_INT, row_root, rowComm);
        // printLocalMatrix(B_local, world_rank, colsPerProc, N, "B recieved " + std::to_string(my_row) + " " + std::to_string(my_col));
    }
    // Рассылаем полученные полосы B по всем строкам в столбце
    MPI_Bcast(B_local.data(), colsPerProc * N, MPI_INT, col_root, colComm);

    // Локальное умножение: C_local = A_local * B_local
    Matrix C_local = localMultiplyBlock(A_local, B_local, N, rowsPerProc, colsPerProc);
    // printLocalMatrixC(C_local, world_rank, rowsPerProc, colsPerProc, 
    //              "C_local [" + std::to_string(my_row) + "," + std::to_string(my_col) + "]");

    if (cart_rank != 0) {
        MPI_Send(C_local.data(), static_cast<int>(C_local.size()), MPI_INT, 0, 2, cart_comm);
    } else {
        C.assign(N * N, 0);
        Matrix recvC(rowsPerProc * colsPerProc);
        for (int pr_block = 0; pr_block < dims[0]; pr_block++) {
            for (int pc_block = 0; pc_block < dims[1]; pc_block++) {
                if (pr_block == 0 && pc_block == 0) {
                    // Кладем свой локальный блок
                    placeBlockIntoGlobal(C_local, C, N, rowsPerProc, colsPerProc, 0, 0);
                    continue;
                }

                int src_coords[dimSize] = {pr_block, pc_block};
                int src_rank;
                MPI_Cart_rank(cart_comm, src_coords, &src_rank);

                MPI_Recv(recvC.data(), static_cast<int>(recvC.size()), MPI_INT, src_rank, 2, cart_comm, MPI_STATUS_IGNORE);

                int rowStart = pr_block * rowsPerProc;
                int colStart = pc_block * colsPerProc;
                placeBlockIntoGlobal(recvC, C, N, rowsPerProc, colsPerProc, rowStart, colStart);
            }
        }
    }

    MPI_Comm_free(&rowComm);
    MPI_Comm_free(&colComm);
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
        double avgTime = std::accumulate(allTimes.begin(), allTimes.end(), 0.0) / size;
        
        std::cout << "\n=== РЕЗУЛЬТАТЫ ДЛЯ " << size << " ПРОЦЕССОВ ===" << std::endl;
        std::cout << "Среднее время: " << avgTime << " мс" << std::endl;
        std::string filename = "results_" + std::to_string(MATRIX_SIZE) + ".txt";
        std::ofstream file(filename, std::ios::app);
        if (file.is_open()) {
            file << size << " " << avgTime << std::endl;
            file.close();
            std::cout << "Результаты записаны в " << filename << std::endl;
        } else {
            std::cout << "Ошибка открытия файла!" << std::endl;
        }
    }
}

void processTask(int world_size, int world_rank, MPI_Comm comm) {
    int N = MATRIX_SIZE;
    Matrix A, B, C;

    if (world_rank == 0) {
        // std::cout << "Введите размер матрицы N: ";
        // std::cin >> N;
        // if (N <= 0) {
        //     std::cerr << "N должно быть положительным\n";
        //     MPI_Abort(comm, 3);
        // }
        A = generateRandomMatrix(N, 0, 9, 42);
        B = generateRandomMatrix(N, 0, 9, 4242);
        printMatrix(A, N, "A");
        printMatrix(B, N, "B");
    }
    MPI_Bcast(&N, 1, MPI_INT, 0, comm);
    
    double startTime = MPI_Wtime();
    if (world_size == 1) {
        multiplySequential(A, B, C, N);
    } else {
        if (world_rank == 0) {
            transposeMatrix(B, N);
        }
        multiplyStriped2D(A, B, C, N, world_size, world_rank, comm);
    }
    double endTime = MPI_Wtime();
    double processTime = (endTime - startTime) * 1000;

    getTimeStatistic(world_rank, world_size, processTime);

    if (world_rank == 0) {
        // printMatrix(B, N, "Bt");
        printMatrix(C, N, "C (результат)");
    }
}

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int world_size = 0, world_rank = 0;
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);

    processTask(world_size, world_rank, MPI_COMM_WORLD);

    MPI_Finalize();
    return 0;
}
