import serial
import struct
import time
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
from collections import deque

# Настройки подключения
PORT = "COM7"
BAUD_RATE = 230400
DEVICE_ADDRESS = 0x50

# Фильтр для стабилизации данных
def moving_average(new_value, buffer, window_size=10):
    buffer.append(new_value)
    return sum(buffer) / len(buffer)

# CRC16 функция
def crc16(data):
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc

# Отправка Modbus-запроса
def send_modbus_request(ser, address, function, start_reg, count):
    request = struct.pack(">BBHH", address, function, start_reg, count)
    crc = crc16(request)
    request += struct.pack("<H", crc)
    ser.write(request)
    time.sleep(0.05)
    return ser.read(50)

# Парсинг данных из ответа Modbus
def parse_data(response):
    if len(response) < 5:
        return None, None, None
    data = response[3:-2]
    values = struct.unpack(">hhh", data[:6])
    roll = values[0] / 32768.0 * 180  # Углы в градусах
    pitch = values[1] / 32768.0 * 180
    yaw = values[2] / 32768.0 * 180
    return roll, pitch, yaw

# Матрица поворота
def rotation_matrix(roll, pitch, yaw):
    roll = np.radians(roll)
    pitch = np.radians(pitch)
    yaw = np.radians(yaw)
    Rx = np.array([[1, 0, 0], [0, np.cos(roll), -np.sin(roll)], [0, np.sin(roll), np.cos(roll)]])
    Ry = np.array([[np.cos(pitch), 0, np.sin(pitch)], [0, 1, 0], [-np.sin(pitch), 0, np.cos(pitch)]])
    Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx  # Yaw -> Pitch -> Roll

# Обновление куба на основе углов
def update(frame, ser, vertices, edges, ax, roll_buf, pitch_buf, yaw_buf):
    response = send_modbus_request(ser, DEVICE_ADDRESS, 0x03, 0x30, 3)
    roll, pitch, yaw = parse_data(response)
    if roll is not None:
        # Стабилизация данных через фильтр
        roll = moving_average(roll, roll_buf)
        pitch = moving_average(pitch, pitch_buf)
        yaw = moving_average(yaw, yaw_buf)
        
        print(f"Filtered -> Roll: {roll:.2f}, Pitch: {pitch:.2f}, Yaw: {yaw:.2f}")

        # Матрица поворота
        R = rotation_matrix(roll, pitch, yaw)
        rotated_vertices = np.dot(vertices, R.T)

        # Обновляем график
        ax.cla()
        ax.set_xlim([-1, 1])
        ax.set_ylim([-1, 1])
        ax.set_zlim([-1, 1])
        ax.set_title("IMU Cube Visualization")

        # Рисуем куб
        for edge in edges:
            edge_points = rotated_vertices[edge]
            ax.plot(edge_points[:, 0], edge_points[:, 1], edge_points[:, 2], color='blue')

# Основной блок
if __name__ == "__main__":
    try:
        with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Connected to {PORT} at {BAUD_RATE} baud.")

            # Куб: вершины и рёбра
            vertices = np.array([
                [-0.5, -0.5, -0.5],
                [0.5, -0.5, -0.5],
                [0.5, 0.5, -0.5],
                [-0.5, 0.5, -0.5],
                [-0.5, -0.5, 0.5],
                [0.5, -0.5, 0.5],
                [0.5, 0.5, 0.5],
                [-0.5, 0.5, 0.5]
            ])
            edges = [
                [0, 1, 2, 3, 0], [4, 5, 6, 7, 4], [0, 4], [1, 5], [2, 6], [3, 7]
            ]

            # Буферы для фильтра
            roll_buf, pitch_buf, yaw_buf = deque(maxlen=10), deque(maxlen=10), deque(maxlen=10)

            # Инициализация графика
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ani = FuncAnimation(fig, update, fargs=(ser, vertices, edges, ax, roll_buf, pitch_buf, yaw_buf), interval=100)
            plt.show()

    except KeyboardInterrupt:
        print("Program stopped.")
    except Exception as e:
        print("Error:", e)
