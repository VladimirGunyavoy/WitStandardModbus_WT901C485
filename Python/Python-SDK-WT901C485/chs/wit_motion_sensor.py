import time
import platform
import threading
import lib.device_model as deviceModel
from lib.data_processor.roles.jy901s_dataProcessor import JY901SDataProcessor
from lib.protocol_resolver.roles.protocol_485_resolver import Protocol485Resolver

class WitMotionSensor:
    def __init__(self, port=None):
        self.device = deviceModel.DeviceModel(
            "MyJY901",
            Protocol485Resolver(),
            JY901SDataProcessor(),
            "51_0"
        )
        self.device.ADDR = 0x50
        
        # Установка порта
        if port:
            self.device.serialConfig.portName = port
        else:
            if platform.system().lower() == 'linux':
                self.device.serialConfig.portName = "/dev/ttyUSB0"
            else:
                self.device.serialConfig.portName = "COM7"
                
        self.device.serialConfig.baud = 230400
        
        # Данные с датчика
        self.current_data = {
            "acceleration": {"x": 0, "y": 0, "z": 0},
            "gyro": {"x": 0, "y": 0, "z": 0},
            "angle": {"x": 0, "y": 0, "z": 0},
            "magnetic": {"x": 0, "y": 0, "z": 0},
            "temperature": 0,
            "chiptime": 0
        }
        
        # Флаг работы потока
        self.running = True
        
    def calibrate(self):
        print("\n=== Калибровка акселерометра ===")
        print("Положите датчик на ровную поверхность")
        input("Нажмите Enter когда будете готовы...")
        self.device.AccelerationCalibration()
        print("Калибровка акселерометра завершена")
        
        print("\n=== Калибровка магнитного поля ===")
        print("1. Держите датчик на расстоянии от металлических предметов")
        print("2. Во время калибровки медленно поворачивайте датчик:")
        print("   - сделайте полный оборот вокруг оси X")
        print("   - сделайте полный оборот вокруг оси Y")
        print("   - сделайте полный оборот вокруг оси Z")
        input("Нажмите Enter чтобы начать...")
        
        self.device.BeginFiledCalibration()
        input("Выполните повороты датчика и нажмите Enter для завершения...")
        self.device.EndFiledCalibration()
        print("Калибровка магнитного поля завершена")
        
    def _update_callback(self, deviceModel):
        """Обновление данных при получении новых значений"""
        self.current_data["acceleration"]["x"] = deviceModel.getDeviceData("accX")
        self.current_data["acceleration"]["y"] = deviceModel.getDeviceData("accY")
        self.current_data["acceleration"]["z"] = deviceModel.getDeviceData("accZ")
        
        self.current_data["gyro"]["x"] = deviceModel.getDeviceData("gyroX")
        self.current_data["gyro"]["y"] = deviceModel.getDeviceData("gyroY")
        self.current_data["gyro"]["z"] = deviceModel.getDeviceData("gyroZ")
        
        self.current_data["angle"]["x"] = deviceModel.getDeviceData("angleX")
        self.current_data["angle"]["y"] = deviceModel.getDeviceData("angleY")
        self.current_data["angle"]["z"] = deviceModel.getDeviceData("angleZ")
        
        self.current_data["magnetic"]["x"] = deviceModel.getDeviceData("magX")
        self.current_data["magnetic"]["y"] = deviceModel.getDeviceData("magY")
        self.current_data["magnetic"]["z"] = deviceModel.getDeviceData("magZ")
        
        self.current_data["temperature"] = deviceModel.getDeviceData("temperature")
        self.current_data["chiptime"] = deviceModel.getDeviceData("Chiptime")
    
    def _read_thread(self):
        """Поток чтения данных"""
        while self.running:
            self.device.readReg(0x30, 41)
            time.sleep(0.01)
    
    def start(self):
        """Запуск работы с датчиком"""
        try:
            # Открываем устройство
            self.device.openDevice()
            
            # Регистрируем callback
            self.device.dataProcessor.onVarChanged.append(self._update_callback)
            
            # Запускаем поток чтения
            self.thread = threading.Thread(target=self._read_thread)
            self.thread.daemon = True  # Поток завершится вместе с основной программой
            self.thread.start()
            
            return True
        except Exception as e:
            print(f"Error starting sensor: {e}")
            return False
    
    def stop(self):
        """Остановка работы с датчиком"""
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)
        try:
            self.device.closeDevice()
        except:
            pass
    
    def get_acceleration(self):
        """Получить текущее ускорение"""
        return self.current_data["acceleration"]
    
    def get_gyro(self):
        """Получить текущие показания гироскопа"""
        return self.current_data["gyro"]
    
    def get_angle(self):
        """Получить текущие углы"""
        return self.current_data["angle"]
    
    def get_magnetic(self):
        """Получить текущие показания магнитометра"""
        return self.current_data["magnetic"]
    
    def get_temperature(self):
        """Получить текущую температуру"""
        return self.current_data["temperature"]
    
    def get_all_data(self):
        """Получить все текущие данные"""
        return self.current_data
    

def main():
    try:
        # Создаем объект датчика
        # Если датчик на другом порту, укажите его: WitMotionSensor("COM3") для Windows
        # или WitMotionSensor("/dev/ttyUSB1") для Linux
        sensor = WitMotionSensor()
        
        # Запускаем датчик
        if not sensor.start():
            print("Не удалось запустить датчик!")
            return
            
        print("Датчик запущен! Начинаем читать данные...")
        print("Для выхода нажмите Ctrl+C")
        
        # sensor.calibrate()
        
        # Основной цикл
        while True:
            # Получаем все данные с датчика
            data = sensor.get_all_data()
            
            # Выводим данные
            print("\nПоказания датчика:")
            print(f"Ускорение (g): X={data['acceleration']['x']:.2f}, Y={data['acceleration']['y']:.2f}, Z={data['acceleration']['z']:.2f}")
            print(f"Углы (град): X={data['angle']['x']:.2f}, Y={data['angle']['y']:.2f}, Z={data['angle']['z']:.2f}")
            print(f"Температура: {data['temperature']:.1f}°C")
            
            # Также можно получать отдельные параметры:
            acceleration = sensor.get_acceleration()
            angles = sensor.get_angle()
            temp = sensor.get_temperature()
            
            # Пауза перед следующим чтением
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nЗавершение работы...")
    finally:
        if 'sensor' in locals():
            sensor.stop()
            print("Датчик остановлен")

if __name__ == "__main__":
    main()