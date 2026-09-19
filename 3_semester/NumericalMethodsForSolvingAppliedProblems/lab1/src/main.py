import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Загрузка данных
train = pd.read_csv('train.csv', sep=';', decimal=',')
test  = pd.read_csv('test.csv',  sep=';', decimal=',')

t_train = train['t'].values.astype(float)
v_train = train['v'].values.astype(float)
t_test  = test['t'].values.astype(float)
v_test  = test['v'].values.astype(float)

# Модель
def exp_model(t, a, b):
    """v(t) = a * exp(b * t)"""
    return a * np.exp(b * t)

# Начальные приближения
a_start = v_train[0]
b_start = np.log(v_train[-1] / v_train[0]) / (t_train[-1] - t_train[0])

print(f"a_start = {a_start}")
print(f"b_start = {b_start:.10e}")

# Подгонка модели
popt, pcov = curve_fit(exp_model, t_train, v_train, p0=[a_start, b_start])
a_model, b_model = popt

# Стандартные ошибки
perr = np.sqrt(np.diag(pcov))

print("\n=== ПАРАМЕТРЫ МОДЕЛИ ===")
print(f"a = {a_model:.6f}  (std err = {perr[0]:.6f})")
print(f"b = {b_model:.10e}  (std err = {perr[1]:.10e})")

# Прогноз на тестовой выборке
v_pred_test = exp_model(t_test, a_model, b_model)
test['pred'] = v_pred_test

print("\n=== ПРОГНОЗ НА ТЕСТЕ ===")
print(test.to_string(index=False))

# Метрики
error = v_test - v_pred_test
MAE  = np.mean(np.abs(error))
MSE  = np.mean(error ** 2)
RMSE = np.sqrt(MSE)
MAPE = np.mean(np.abs(error / v_test)) * 100

print("\n=== МЕТРИКИ НА ТЕСТЕ ===")
print(f"MAE  = {MAE:.4f}")
print(f"MSE  = {MSE:.4f}")
print(f"RMSE = {RMSE:.4f}")
print(f"MAPE = {MAPE:.2f}%")

# График
t_grid = np.linspace(t_train.min(), t_test.max(), 300)
v_grid = exp_model(t_grid, a_model, b_model)

plt.figure(figsize=(10, 6))
plt.scatter(t_train, v_train, color='black', label='Обучающая выборка', zorder=3)
plt.scatter(t_test,  v_test,  color='red', marker='^', s=80,
            label='Тестовая выборка', zorder=3)
plt.plot(t_grid, v_grid, color='blue', linewidth=2,
         label='Экспоненциальная модель')
plt.xlabel('t, ч')
plt.ylabel('v, мм/с')
plt.title('Экспоненциальная модель v(t) = a·exp(b·t)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('plot.png')
plt.show()

# Итоговая модель
print(f"\nИтоговая модель: v(t) = {a_model:.6f} * exp({b_model:.8e} * t)")
print(f"MAPE на тесте: {MAPE:.2f}%")