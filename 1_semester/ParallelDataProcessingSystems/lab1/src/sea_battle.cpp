#include <iostream>
#include <vector>
#include <algorithm>
#include <mpi.h>
#include <fstream>
#include <numeric>


#define FIELD_SIZE 6
#define DENSITY_PERCENT 20
#define COUNT_SHIPS ((int)(FIELD_SIZE * FIELD_SIZE * DENSITY_PERCENT) / 100)

enum class PlayerStatus {
    ALIVE = 0,
    DEAD = 1
};

enum class CellState {
    WATER = 0,
    SHIP = 1,
    UNKNOWN = 2
};

enum class ShotResult {
    MISS = 0,
    HIT = 1,
    DEAD = 2
};

struct Cell {
    int x;
    int y;
    CellState state;
};

using Board = std::vector<Cell>;


void safe_cout(int rank, const std::string& message) {
    std::string filename = "debug_player_" + std::to_string(rank) + ".log";
    std::string log_message = "[Игрок " + std::to_string(rank) + "] " + message;
    std::ofstream file(filename, std::ios::app);
    file << log_message << std::endl;
    file.close();
}

Board generateBoard(int fieldSize = FIELD_SIZE) {
    Board board;
    board.reserve(fieldSize * fieldSize);

    for (int y = 0; y < fieldSize; y++) {
        for (int x = 0; x < fieldSize; x++) {
            board.push_back({x, y, CellState::WATER});
        }
    }

    return board;
};

void placeShips(Board& board, int fieldSize = FIELD_SIZE, int countShips = COUNT_SHIPS) {
    int placed = 0;
    std::cout << countShips << std::endl;
    while (placed < countShips) {
        int x = rand() % fieldSize;
        int y = rand() % fieldSize;

        int idx = y * fieldSize + x;

        if (board[idx].state == CellState::WATER) {
            board[idx].state = CellState::SHIP;
            placed++;
        }
    }
};

Cell getBoardCell(const Board& board, int x, int y, int fieldSize = FIELD_SIZE) {
    return board[y * fieldSize + x];
};

PlayerStatus getPlayerStatus(const Board& board) {
    bool hasShip = std::any_of(board.begin(), board.end(), [](const Cell& c){ return c.state == CellState::SHIP; });
    return hasShip ? PlayerStatus::ALIVE : PlayerStatus::DEAD;
};

Board generateAvaliableCells(int fieldSize = FIELD_SIZE) {
    Board availableCells;
    availableCells.reserve(fieldSize * fieldSize);

     for (int y = 0; y < fieldSize; y++) {
        for (int x = 0; x < fieldSize; x++) {
            availableCells.push_back({x, y, CellState::UNKNOWN});
        }
    }

    return availableCells;
};

Cell getRandomAvaliableCell(Board& availableCells) {
    if (availableCells.empty()) {
        return {-1, -1, CellState::UNKNOWN};
    }

    int idx = rand() % availableCells.size();
    Cell target = availableCells[idx];

    availableCells[idx] = availableCells.back();
    availableCells.pop_back();

    return target;
};

void sendShot(const Cell& target, int destRank) {
    int coords[2] = { target.x, target.y };
    MPI_Send(coords, 2, MPI_INT, destRank, 0, MPI_COMM_WORLD);
};

Cell receiveShot(int sourceRank) {
    int coords[2];
    MPI_Recv(coords, 2, MPI_INT, sourceRank, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);

    Cell target = {coords[0], coords[1], CellState::UNKNOWN};

    return target;
};

ShotResult processIncomingShot(Board& board, PlayerStatus& currentStatus, const Cell& shot, int fieldSize = FIELD_SIZE) {
    int idx = shot.y * fieldSize + shot.x;

    if (board[idx].state == CellState::SHIP) {
        board[idx].state = CellState::WATER;
        PlayerStatus newStatus = getPlayerStatus(board);

        if (newStatus == PlayerStatus::DEAD) {
            currentStatus = newStatus;
            return ShotResult::DEAD;
        }
        return ShotResult::HIT;
    }
    return ShotResult::MISS;
};

void sendShotResult(ShotResult result, int destRank) {
    int r = static_cast<int>(result);
    MPI_Send(&r, 1, MPI_INT, destRank, 1, MPI_COMM_WORLD);
};

ShotResult receiveShotResult(int sourceRank) {
    int r;
    MPI_Recv(&r, 1, MPI_INT, sourceRank, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    return static_cast<ShotResult>(r);
};

int getAlivePlayersCount(int rank, int size, PlayerStatus myStatus, std::vector<int>& allStatuses) {
    int myStatusInt = static_cast<int>(myStatus);
    MPI_Allgather(&myStatusInt, 1, MPI_INT, allStatuses.data(), 1, MPI_INT, MPI_COMM_WORLD);
    
    std::string message = "Состояния всех игроков: [";
    for (int i = 0; i < size; i++) {
        message += (allStatuses[i] == 0 ? "ЖИВ" : "МЕРТВ");
        if (i < size - 1) message += ", ";
    }
    message += "]";
    safe_cout(rank, message);

    int aliveCount = 0;
    for (int status : allStatuses) {
        if (status == static_cast<int>(PlayerStatus::ALIVE)) {
            aliveCount++;
        }
    }
    
    return aliveCount;
};

int findNextAlivePlayer(int currentRank, int size, const std::vector<int>& allStatuses) {
    for (int offset = 1; offset < size; offset++) {
        int nextRank = (currentRank + offset) % size;
        if (allStatuses[nextRank] == static_cast<int>(PlayerStatus::ALIVE)) {
            return nextRank;
        }
    }
    return currentRank;
};

int findPreviousAlivePlayer(int currentRank, int size, const std::vector<int>& allStatuses) {
    for (int offset = 1; offset < size; offset++) {
        int prevRank = (currentRank - offset + size) % size;
        if (allStatuses[prevRank] == static_cast<int>(PlayerStatus::ALIVE)) {
            return prevRank;
        }
    }
    return currentRank;
};

void playGame(int rank, int size) {
    safe_cout(rank, "START GAME");
    int attackTarget = -1;
    int defenseSource = -1;
    int alivePlayersCount = size;
    
    Board myBoard = generateBoard();
    placeShips(myBoard);
    Board availableCells = generateAvaliableCells();

    PlayerStatus myStatus = PlayerStatus::ALIVE;
    std::vector<int> allStatuses(size);

    while (true) {
        alivePlayersCount = getAlivePlayersCount(rank, size, myStatus, allStatuses);
        if (alivePlayersCount <= 1) {
            break;
        }

        int newAttackTarget = findNextAlivePlayer(rank, size, allStatuses);
        defenseSource = findPreviousAlivePlayer(rank, size, allStatuses);

        if (attackTarget != newAttackTarget) {
            availableCells = generateAvaliableCells();
        }
        attackTarget = newAttackTarget;

        if (myStatus == PlayerStatus::ALIVE) {
            Cell target = getRandomAvaliableCell(availableCells);
            safe_cout(rank, "Стреляет в игрока: " + std::to_string(attackTarget) + " по координатам: (" + std::to_string(target.x) + "," + std::to_string(target.y) + ")");
            sendShot(target, attackTarget);

            Cell incomingShot = receiveShot(defenseSource);
            safe_cout(rank, "Получил выстрел от игрока: " + std::to_string(defenseSource) + " по координатам: (" + std::to_string(incomingShot.x) + "," + std::to_string(incomingShot.y) + ")");
            ShotResult myIncomingShotResult = processIncomingShot(myBoard, myStatus, incomingShot);
            std::string resultStr;
            switch(myIncomingShotResult) {
                case ShotResult::MISS: resultStr = "ПРОМАХ"; break;
                case ShotResult::HIT: resultStr = "ПОПАДАНИЕ"; break;
                case ShotResult::DEAD: resultStr = "УБИТ"; break;
            }
            safe_cout(rank, "Результат выстрела: " + resultStr);
            sendShotResult(myIncomingShotResult, defenseSource);

            ShotResult myShotResult = receiveShotResult(attackTarget);
            std::string myResultStr;
            switch(myShotResult) {
                case ShotResult::MISS: myResultStr = "ПРОМАХ"; break;
                case ShotResult::HIT: myResultStr = "ПОПАДАНИЕ"; break;
                case ShotResult::DEAD: myResultStr = "УБИТ"; break;
            }
            safe_cout(rank, "Результат атаки: " + myResultStr);
        }
    }
    
    if (myStatus == PlayerStatus::ALIVE && alivePlayersCount == 1) {
        safe_cout(rank, "ПОБЕДИЛ!");
    } else if (myStatus == PlayerStatus::ALIVE) {
        safe_cout(rank, "ВЫЖИЛ В НИЧЬЕЙ!");
    } else {
        safe_cout(rank, "ПРОИГРАЛ!");
    }
};

int main(int argc,  char *argv[]) {  
    int rank, size; 
    MPI_Status Status;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank); 
    MPI_Comm_size(MPI_COMM_WORLD, &size); 
    std::cout << "Процесс " << rank << ": MPI_Comm_size вернул size = " << size << std::endl;
    if(size < 2){
        std::cerr << "Запустите минимум 2 процесса для игры!" << std::endl;
        MPI_Finalize();
        return 0;
    }

    srand(time(NULL) + rank);

    double startTime = MPI_Wtime();
    playGame(rank, size);
    double endTime = MPI_Wtime();
    double gameTime = (endTime - startTime) * 1000;

    std::vector<double> allTimes;
    if (rank == 0) {
        allTimes.resize(size);
    }

    MPI_Gather(&gameTime, 1, MPI_DOUBLE, 
            allTimes.data(), 1, MPI_DOUBLE, 
            0, MPI_COMM_WORLD);

    if (rank == 0) {
        double maxTime = *std::max_element(allTimes.begin(), allTimes.end());
        double avgTime = std::accumulate(allTimes.begin(), allTimes.end(), 0.0) / size;
        
        std::cout << "\n=== РЕЗУЛЬТАТЫ ДЛЯ " << size << " ПРОЦЕССОВ ===" << std::endl;
        std::cout << "Максимальное время: " << maxTime << " мс" << std::endl;
        std::cout << "Среднее время: " << avgTime << " мс" << std::endl;
        
        // Записываем в файл для последующего анализа
        std::ofstream file("timing_results" + std::to_string(FIELD_SIZE) + ".txt", std::ios::app);
        file << size << " " << maxTime << " " << avgTime << std::endl;
        file.close();
    }

    std::cout << "Процесс " << rank 
              << " завершил игру за " 
              << gameTime << " мс" << std::endl;

    MPI_Finalize(); 
    return 0; 
};
