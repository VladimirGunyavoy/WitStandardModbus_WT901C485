import serial
import struct
import time

# Настройки подключения
PORT = "COM7"
BAUD_RATE = 230400
DEVICE_ADDRESS = 0x50

def crc16(data):
    """Вычисление CRC16 Modbus"""
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

def send_modbus_request(ser, address, function, start_reg, count):
    """Формирование и отправка Modbus-запроса"""
    request = struct.pack(">BBHH", address, function, start_reg, count)
    crc = crc16(request)
    request += struct.pack("<H", crc)
    ser.write(request)
    time.sleep(0.1)
    return ser.read(50)


    
def parse_data(response):
    if len(response) < 15:  # Минимум 15 байт для 6 регистров (3 акселерометр + 3 гироскоп)
        print("Invalid response: Not enough data")
        return None, None, None, None, None, None

    try:
        # Извлечение данных из ответа
        data = response[3:-2]  # Пропускаем заголовок и CRC
        values = struct.unpack(">hhhhhh", data[:12])  # Читаем 6 регистров (акселерометр и гироскоп)

        # Масштабирование акселерометра
        accX = values[0] / 1000.0   # Акселерометр в G
        accY = values[1] / 1000.0
        accZ = values[2] / 1000.0

        # Масштабирование гироскопа
        gyroX = values[3] / 32768.0 * 2000.0  # Гироскоп в град/сек
        gyroY = values[4] / 32768.0 * 2000.0
        gyroZ = values[5] / 32768.0 * 2000.0

        # Вывод для проверки
        print(f"Raw Values: {values}")
        return accX, accY, accZ, gyroX, gyroY, gyroZ

    except struct.error as e:
        print(f"Data unpacking error: {e}")
        return None, None, None, None, None, None


def print_data(accX, accY, accZ, gyroX, gyroY, gyroZ):
    """
    Красивый вывод данных сенсора WT901C-485
    :param accX: Ускорение по оси X (в G)
    :param accY: Ускорение по оси Y (в G)
    :param accZ: Ускорение по оси Z (в G)
    :param gyroX: Угловая скорость по оси X (в град/сек)
    :param gyroY: Угловая скорость по оси Y (в град/сек)
    :param gyroZ: Угловая скорость по оси Z (в град/сек)
    """
    print("\n" + "=" * 50)
    print(f"{'Sensor Data':^50}")
    print("=" * 50)
    print(f"Acceleration (G):")
    print(f"    X: {accX:>8.3f} G   |   Y: {accY:>8.3f} G   |   Z: {accZ:>8.3f} G")
    print("-" * 50)
    print(f"Gyro (°/s):")
    print(f"    X: {gyroX:>8.3f}°/s  |   Y: {gyroY:>8.3f}°/s  |   Z: {gyroZ:>8.3f}°/s")
    print("=" * 50)
    print()
    print()


from collections import deque

# Инициализация буферов
accX_buf, accY_buf, accZ_buf = deque(maxlen=10), deque(maxlen=10), deque(maxlen=10)
gyroX_buf, gyroY_buf, gyroZ_buf = deque(maxlen=10), deque(maxlen=10), deque(maxlen=10)

def moving_average(new_value, buffer):
    buffer.append(new_value)
    return sum(buffer) / len(buffer)

if __name__ == "__main__":
    try:
        with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Connected to {PORT} at {BAUD_RATE} baud.")
            while True:
                response = send_modbus_request(ser, DEVICE_ADDRESS, 0x03, 0x30, 6)  # Чтение 6 регистров

                if response:
                    accX, accY, accZ, gyroX, gyroY, gyroZ = parse_data(response)
                    # Получаем данные и применяем фильтр
                    accX = moving_average(accX, accX_buf)
                    accY = moving_average(accY, accY_buf)
                    accZ = moving_average(accZ, accZ_buf)
                    gyroX = moving_average(gyroX, gyroX_buf)
                    gyroY = moving_average(gyroY, gyroY_buf)
                    gyroZ = moving_average(gyroZ, gyroZ_buf)

                    print_data(accX, accY, accZ, gyroX, gyroY, gyroZ)
                else:
                    print("No response.")
                time.sleep(1)
    except KeyboardInterrupt:
        print("Program stopped.")
    except Exception as e:
        print("Error:", e)
