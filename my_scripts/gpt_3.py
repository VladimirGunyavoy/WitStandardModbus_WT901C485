import serial
import struct
import time
from collections import deque

# Настройки подключения
PORT = "COM7"           # Укажите ваш COM-порт
BAUD_RATE = 230400      # Скорость передачи
DEVICE_ADDRESS = 0x50   # Адрес устройства Modbus

# Инициализация буферов для фильтрации
accX_buf, accY_buf, accZ_buf = deque(maxlen=50), deque(maxlen=50), deque(maxlen=50)
gyroX_buf, gyroY_buf, gyroZ_buf = deque(maxlen=50), deque(maxlen=50), deque(maxlen=50)

# Смещение акселерометра (Offset)
acc_offset_X = 0.0
acc_offset_Y = 0.0
acc_offset_Z = 0.0

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

# Парсинг данных из ответа
def parse_data(response):
    if len(response) < 15:
        print("Invalid response: Not enough data")
        return None, None, None, None, None, None

    data = response[3:-2]
    values = struct.unpack(">hhhhhh", data[:12])
    
    acc_scale = 1024
    accX = values[0] / acc_scale  
    accY = values[1] / acc_scale
    accZ = values[2] / acc_scale
    gyroX = values[3] / 32768.0 * 2000.0
    gyroY = values[4] / 32768.0 * 2000.0
    gyroZ = values[5] / 32768.0 * 2000.0
    return accX, accY, accZ, gyroX, gyroY, gyroZ

# Фильтр скользящего среднего
def moving_average(new_value, buffer):
    buffer.append(new_value)
    return sum(buffer) / len(buffer)

# Коррекция смещения
def correct_offset(accX, accY, accZ, offsetX, offsetY, offsetZ):
    """
    Коррекция смещения и ручная поправка оси Z для гравитации.
    """
    accX_corrected = accX - offsetX
    accY_corrected = accY - offsetY
    accZ_corrected = accZ - offsetZ + 1.0  # Добавляем 1 G к Z
    return accX_corrected, accY_corrected, accZ_corrected

# Вычисление смещения
def calculate_offset(accX_buf, accY_buf, accZ_buf):
    offsetX = sum(accX_buf) / len(accX_buf)
    offsetY = sum(accY_buf) / len(accY_buf)
    offsetZ = sum(accZ_buf) / len(accZ_buf)
    return offsetX, offsetY, offsetZ

# Красивый вывод данных
def print_data(accX, accY, accZ, gyroX, gyroY, gyroZ):
    print("\n" + "=" * 50)
    print(f"{'Sensor Data':^50}")
    print("=" * 50)
    print(f"Acceleration (G):")
    print(f"    X: {accX:>8.3f} G   |   Y: {accY:>8.3f} G   |   Z: {accZ:>8.3f} G")
    print("-" * 50)
    print(f"Gyro (°/s):")
    print(f"    X: {gyroX:>8.3f}°/s  |   Y: {gyroY:>8.3f}°/s  |   Z: {gyroZ:>8.3f}°/s")
    print("=" * 50)

# Основной цикл
if __name__ == "__main__":
    try:
        with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Connected to {PORT} at {BAUD_RATE} baud.")
            
            # Сброс IMU перед калибровкой
            CMD_RESET = b'\xFF\xAA\x01\x04'  # Сброс углов
            ser.write(CMD_RESET)
            time.sleep(1)

            print("Стабилизируйте сенсор на ровной поверхности...")
            for _ in range(50):
                response = send_modbus_request(ser, DEVICE_ADDRESS, 0x03, 0x30, 6)
                accX, accY, accZ, _, _, _ = parse_data(response)
                if accX is not None:
                    accX_buf.append(accX)
                    accY_buf.append(accY)
                    accZ_buf.append(accZ)
                print(f'{_} / 50')
                time.sleep(0.1)

            acc_offset_X, acc_offset_Y, acc_offset_Z = calculate_offset(accX_buf, accY_buf, accZ_buf)
            print(f"Offsets calculated -> X: {acc_offset_X:.3f}, Y: {acc_offset_Y:.3f}, Z: {acc_offset_Z:.3f}")

            while True:
                response = send_modbus_request(ser, DEVICE_ADDRESS, 0x03, 0x30, 6)
                accX, accY, accZ, gyroX, gyroY, gyroZ = parse_data(response)

                if accX is not None:
                    accX = moving_average(accX, accX_buf)
                    accY = moving_average(accY, accY_buf)
                    accZ = moving_average(accZ, accZ_buf)
                    accX, accY, accZ = correct_offset(accX, accY, accZ, acc_offset_X, acc_offset_Y, acc_offset_Z)

                    gyroX = moving_average(gyroX, gyroX_buf)
                    gyroY = moving_average(gyroY, gyroY_buf)
                    gyroZ = moving_average(gyroZ, gyroZ_buf)

                    # Масштабирование для диапазона ±16G
                    accX /= 2
                    accY /= 2
                    accZ /= 2

                    print_data(accX, accY, accZ, gyroX, gyroY, gyroZ)
                time.sleep(0.2)

    except KeyboardInterrupt:
        print("Program stopped.")
    except Exception as e:
        print("Error:", e)
