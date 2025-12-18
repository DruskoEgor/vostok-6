import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import math


# параметры ракеты (без округлений)
t1, t2 = 100.1, 257.4  # времена отделения первой и второй ступеней

m = 414_510             # начальная масса ракеты
m0 = 307_203            # масса после всех ступеней

fuel_stage1 = 191_878   # масса топлива первой ступени
fuel_stage2 = 76_311    # масса топлива второй ступени

Ft1, Ft2 = 6_000_000, 1_500_000  # тяга первой и второй ступеней
k1, k2 = 1_921, 512              # расход топлива в секунду для ступеней

# константы
ro = 1.225       # плотность воздуха на уровне моря
g = 9.80665      # ускорение свободного падения
Cd = 0.3         # коэффициент аэродинамического сопротивления
S = 80           # площадь поперечного сечения ракеты


# данные симуляции (без округлений)
t_ksp = np.array([0, 20, 40, 60, 80, 100.1, 120, 140, 160, 180, 200, 220, 240, 257.4])
h_ksp = np.array([0, 980, 4120, 9350, 18240, 33980, 52100, 70500,
                  88100, 96300, 108400, 120800, 129200, 131000])
v_ksp = np.array([0, 96, 198, 415, 612, 892, 1010, 1135,
                  1210, 1195, 1315, 1590, 1910, 2230])
m_ksp = np.array([414_510, 371_800, 331_200, 292_100, 251_600, 142_400,
                  126_900, 111_700, 99_800, 91_200, 85_400, 75_600,
                  70_200, 68_900])


# модель
# угол ракеты к вертикали
def angle(t):
    if t < 20:
        return math.radians(0)
    elif t < 80:
        return math.radians(15)
    elif t < 110:
        return math.radians(60)
    elif t < 160:
        return math.radians(60)
    else:
        return math.radians(100)


def atmospheric_density(h):
    # плотность воздуха как функция высоты, экспоненциальное уменьшение
    return ro * math.exp(-h / 6000)

def mass(t):
    # масса ракеты во времени с учётом расхода топлива
    if t < t1:
        return max(m - k1 * t, m - fuel_stage1)
    elif t < t2:
        return max((m - fuel_stage1) - k2 * (t - t1),
                   m - fuel_stage1 - fuel_stage2)
    else:
        return m - fuel_stage1 - fuel_stage2

def thrust(t):
    # сила тяги ракеты в зависимости от ступени
    if t < t1:
        return Ft1
    elif t < t2:
        return Ft2
    else:
        return 0

def equations(t, y):
    # система дифференциальных уравнений для скорости и высоты
    v, h = y

    m_t = mass(t)               # текущая масса
    Ft = thrust(t)              # текущая тяга
    alpha = angle(t)            # угол наклона

    p = atmospheric_density(h)  # плотность воздуха на текущей высоте

    # сопротивление воздуха квадратичное по скорости
    drag = 0.5 * Cd * p * S * v**2

    # ускорение ракеты
    a = (Ft - m_t * g * math.cos(alpha) - drag) / m_t

    return [a, v]


# решение
t_end = t2
t_eval = np.linspace(0, t_end, 1200)

solution = solve_ivp(
    equations,
    (0, t_end),
    [0, 0],
    t_eval=t_eval,
    rtol=1e-6,
    atol=1e-8
)

times = solution.t
velocities = solution.y[0]
heights = solution.y[1]
masses = np.array([mass(t) for t in times])


def state_at_time(t_target):
    idx = np.argmin(np.abs(times - t_target))
    return times[idx], velocities[idx], heights[idx], masses[idx]

print("Отделение 1-й ступени:", state_at_time(t1))
print("Отделение 2-й ступени:", state_at_time(t2))


# построение графиков
plt.style.use('seaborn-v0_8-darkgrid')
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

model_color = '#1f77b4'
sim_color = '#ff7f0e'

# график скорости
axes[0].plot(times, velocities, color=model_color, lw=2.5, label='модель')
axes[0].plot(t_ksp, v_ksp, '--', color=sim_color, lw=2, label='симуляция')
axes[0].set_ylabel('скорость (м/с)')
axes[0].legend()

# график высоты
axes[1].plot(times, heights, color=model_color, lw=2.5, label='модель')
axes[1].plot(t_ksp, h_ksp, '--', color=sim_color, lw=2, label='симуляция')
axes[1].set_ylabel('высота (м)')
axes[1].legend()


# график массы
axes[2].plot(times, masses, color=model_color, lw=2.5, label='модель')
axes[2].plot(t_ksp, m_ksp, '--', color=sim_color, lw=2, label='симуляция')
axes[2].set_ylabel('масса (кг)')
axes[2].set_xlabel('время (с)')
axes[2].legend()

plt.suptitle('сравнение модели и симуляции')
plt.tight_layout()
plt.show()
