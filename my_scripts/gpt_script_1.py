import serial
import struct
import time

# Настройки подключения
PORT = "COM7"  # Ваш порт
BAUD_RATE = 230400
DEVICE_ADDRESS = 0x50  # Адрес устройства Modbus

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
    time.sleep(0.1)  # Ждём ответ

    response = ser.read(50)  # Чтение ответа (примерный размер)
    if response:
        print("Received:", response.hex())
    else:
        print("No response.")

# Основной блок
if __name__ == "__main__":
    try:
        with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
            print(f"Connected to {PORT} at {BAUD_RATE} baud.")
            while True:
                send_modbus_request(ser, DEVICE_ADDRESS, 0x03, 0x30, 6)  # Чтение 6 регистров с 0x30
                time.sleep(1)
    except KeyboardInterrupt:
        print("Program stopped.")
    except Exception as e:
        print("Error:", e)
