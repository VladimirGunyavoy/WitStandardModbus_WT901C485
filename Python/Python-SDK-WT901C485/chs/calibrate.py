from wit_motion_sensor import WitMotionSensor
import time

def calibrate_sensor(sensor):
    print("\n=== Калибровка акселерометра ===")
    print("Положите датчик на ровную поверхность")
    input("Нажмите Enter когда будете готовы...")
    sensor.device.AccelerationCalibration()
    print("Калибровка акселерометра завершена")
    
    print("\n=== Калибровка магнитного поля ===")
    print("1. Держите датчик на расстоянии от металлических предметов")
    print("2. Во время калибровки медленно поворачивайте датчик:")
    print("   - сделайте полный оборот вокруг оси X")
    print("   - сделайте полный оборот вокруг оси Y")
    print("   - сделайте полный оборот вокруг оси Z")
    input("Нажмите Enter чтобы начать...")
    
    sensor.device.BeginFiledCalibration()
    input("Выполните повороты датчика и нажмите Enter для завершения...")
    sensor.device.EndFiledCalibration()
    print("Калибровка магнитного поля завершена")

def main():
    sensor = WitMotionSensor()
    if not sensor.start():
        print("Ошибка запуска датчика")
        return
        
    try:
        # Выполняем калибровку
        calibrate_sensor(sensor)
        
        # Проверяем результат
        print("\nПроверка показаний после калибровки:")
        while True:
            data = sensor.get_all_data()
            print("\nПоказания датчика:")
            print(f"Ускорение (g): X={data['acceleration']['x']:.2f}, "
                  f"Y={data['acceleration']['y']:.2f}, "
                  f"Z={data['acceleration']['z']:.2f}")
            print(f"Углы (град): X={data['angle']['x']:.2f}, "
                  f"Y={data['angle']['y']:.2f}, "
                  f"Z={data['angle']['z']:.2f}")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nЗавершение работы...")
    finally:
        if 'sensor' in locals():
            sensor.stop()
            print("Датчик остановлен")

if __name__ == "__main__":
    main()