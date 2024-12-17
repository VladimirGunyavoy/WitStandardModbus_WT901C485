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
    if len(response) < 5:
        return None, None, None, None, None, None

    data = response[3:-2]
    values = struct.unpack(">hhh", data[:6])  # Чтение 3 пар значений (16 бит каждое)

    # Масштабирование данных
    accX = values[0] / 1000.0   # Акселерометр в G
    accY = values[1] / 1000.0
    accZ = values[2] / 1000.0

    gyroX = values[3] / 32768.0 * 2000.0  # Гироскоп в град/сек
    gyroY = values[4] / 32768.0 * 2000.0
    gyroZ = values[5] / 32768.0 * 2000.0

    return accX, accY, accZ, gyroX, gyroY, gyroZ

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



if __name__ == "__main__":
    try:
        with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Connected to {PORT} at {BAUD_RATE} baud.")
            while True:
                response = send_modbus_request(ser, DEVICE_ADDRESS, 0x03, 0x30, 6)  # Чтение 6 регистров
                if response:
                    accX, accY, accZ, gyroX, gyroY, gyroZ = parse_data(response)
                    print_data(accX, accY, accZ, gyroX, gyroY, gyroZ)
                else:
                    print("No response.")
                time.sleep(1)
    except KeyboardInterrupt:
        print("Program stopped.")
    except Exception as e:
        print("Error:", e)
