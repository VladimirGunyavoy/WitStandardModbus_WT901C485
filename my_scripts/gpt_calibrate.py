import serial
import struct
import time

# Настройки подключения
PORT = "COM7"           # Укажите ваш COM-порт
BAUD_RATE = 230400      # Скорость передачи

# Команды для калибровки
CMD_ACCEL_CALIB = b'\xFF\xAA\x01\x01'  # Калибровка акселерометра
CMD_MAG_START = b'\xFF\xAA\x01\x07'    # Начало калибровки магнитометра
CMD_MAG_END = b'\xFF\xAA\x01\x00'      # Завершение калибровки магнитометра
CMD_RESET_ANGLES = b'\xFF\xAA\x01\x04' # Сброс углов

# Функция для отправки команды
def send_command(ser, command, description):
    print(f"Sending: {description}...")
    ser.write(command)
    time.sleep(0.5)
    print(f"{description} complete.\n")

# Основная функция калибровки
def calibrate_imu(port, baud_rate):
    try:
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            print(f"Connected to {port} at {baud_rate} baud.\n")

            # Калибровка акселерометра
            input("Положите сенсор на ровную поверхность и нажмите Enter для калибровки акселерометра...")
            send_command(ser, CMD_ACCEL_CALIB, "Accelerometer Calibration")

            # Калибровка магнитометра
            input("Нажмите Enter для начала калибровки магнитометра (вращайте сенсор вокруг XYZ)...")
            send_command(ser, CMD_MAG_START, "Magnetometer Calibration START")

            input("Нажмите Enter для завершения калибровки магнитометра...")
            send_command(ser, CMD_MAG_END, "Magnetometer Calibration END")

            # Сброс углов
            input("Нажмите Enter для сброса углов...")
            send_command(ser, CMD_RESET_ANGLES, "Angle Reset")

            print("Калибровка завершена успешно!")

    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Calibration stopped by user.")

if __name__ == "__main__":
    calibrate_imu(PORT, BAUD_RATE)
