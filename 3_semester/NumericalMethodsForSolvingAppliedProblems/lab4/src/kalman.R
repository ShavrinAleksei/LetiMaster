# Параметры модели 
SigmaW <- matrix(1, 1, 1)   # шум процесса
SigmaV <- matrix(2, 1, 1)   # шум измерения

A <- matrix(-0.1, 1, 1)
B <- matrix(1,    1, 1)
C <- matrix(1,    1, 1)
D <- matrix(0,    1, 1)

maxIter <- 100

# Инициализация 
xtrue <- matrix(0, 1, 1)
xhat  <- matrix(0, 1, 1)
SigmaX <- matrix(0, 1, 1)
u     <- matrix(0, 1, 1)

xstore      <- numeric(maxIter + 1)
xhatstore   <- numeric(maxIter + 1)
SigmaXstore <- numeric(maxIter + 1)

xstore[1]      <- xtrue[1, 1]
xhatstore[1]   <- xhat[1, 1]
SigmaXstore[1] <- SigmaX[1, 1]

set.seed(42)

# Флаг для проверки: TRUE - с шумом, FALSE - без шума
USE_NOISE <- FALSE

for (k in 1:maxIter) {

  # 1. Генерируем управление
  u <- matrix(0.5 * runif(1) + cos(100 * k / pi) + 0.1 * k, 1, 1)

  # 2. Фильтр предсказывает, используя это же u
  xhat <- A %*% xhat + B %*% u
  SigmaX <- A %*% SigmaX %*% Conj(t(A)) + SigmaW

  # 3. Шумы
  if (USE_NOISE) {
    w <- matrix(rnorm(1, mean = 0, sd = sqrt(SigmaW[1, 1])), 1, 1)
    v <- matrix(rnorm(1, mean = 0, sd = sqrt(SigmaV[1, 1])), 1, 1)
  } else {
    w <- matrix(0, 1, 1)
    v <- matrix(0, 1, 1)
  }

  # 4. Система двигается с этим же u
  xtrue <- A %*% xtrue + B %*% u + w

  # 5. Измерение
  ztrue <- C %*% xtrue + D %*% u + v

  # 6. Оценка выхода системы 
  zhat <- C %*% xhat + D %*% u

  # 7. Коэффициент Калмана 
  L <- SigmaX %*% Conj(t(C)) %*% solve(C %*% SigmaX %*% Conj(t(C)) + SigmaV)

  # 8. Корректировка оценки состояния (update)
  xhat <- xhat + L %*% (ztrue - zhat)

  # 9. Корректировка ковариации ошибки
  SigmaX <- SigmaX - L %*% C %*% SigmaX

  # 10. Сохранение (индексы 2..101)
  xstore[k + 1]      <- xtrue[1, 1]
  xhatstore[k + 1]   <- xhat[1, 1]
  SigmaXstore[k + 1] <- SigmaX[1, 1]
}


# Метрики и визуализация
estErr <- xstore - xhatstore
rms    <- sqrt(mean(estErr * estErr))
cat(sprintf("RMS Error : %.3f\n", rms))

# Визуализация
fname <- if (USE_NOISE) "kalman_plot_noise.png" else "kalman_plot_clean.png"
png(fname, width = 1000, height = 800, res = 120)
par(mfrow = c(2, 1), mar = c(4, 4, 2, 1))

# График 1: истина vs оценка
plot(xhatstore, type = "l", col = "blue", lwd = 2,
     ylim = range(c(xhatstore, xstore)),
     ylab = "est vs. actual state", xlab = "",
     main = "Kalman Filter (R)")
lines(xstore, col = "red", lwd = 2)
legend("topleft", legend = c("оценка фильтра", "истинное состояние"),
       col = c("blue", "red"), lwd = 2)
grid()

# График 2: ошибка оценки
plot(estErr, type = "l", col = "#DC143C", lwd = 2,
     ylab = "estimation error", xlab = "iterations")
abline(h = 0, col = "gray", lty = 2)
grid()

dev.off()
cat(sprintf("График сохранён в %s\n", fname))