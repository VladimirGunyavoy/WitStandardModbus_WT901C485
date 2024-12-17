# coding:UTF-8
"""
    Test file
"""
import time
import datetime
import platform
import threading
import lib.device_model as deviceModel
from lib.data_processor.roles.jy901s_dataProcessor import JY901SDataProcessor
from lib.protocol_resolver.roles.protocol_485_resolver import Protocol485Resolver
import signal
import sys

welcome = """
Welcome to the Wit-Motion sample program
"""
_writeF = None                    # Write file
_IsWriteF = False                # Write file flag
running = True  

def signal_handler(sig, frame):
    print('\nПрограмма завершается...')
    global _IsWriteF, _writeF
    if _IsWriteF:
        _IsWriteF = False
        _writeF.close()
    try:
        device.closeDevice()
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def readConfig(device):
    """
    Example of reading configuration information
    :param device: Device model
    :return:
    """
    tVals = device.readReg(0x02, 3)  # Read data content, return rate, communication rate
    if (len(tVals) > 0):
        print("Return result: " + str(tVals))
    else:
        print("No return")
    tVals = device.readReg(0x23, 2)  # Read the installation direction and algorithm
    if (len(tVals) > 0):
        print("Return result: " + str(tVals))
    else:
        print("No return")

def setConfig(device):
    """
    Example of setting configuration information
    :param device: Device model
    :return:
    """
    device.unlock()                # Unlock
    time.sleep(0.1)               # Sleep 100ms
    device.writeReg(0x03, 6)      # Set the transmission back rate to 10HZ
    time.sleep(0.1)               # Sleep 100ms
    device.writeReg(0x23, 0)      # Set installation direction: horizontal and vertical
    time.sleep(0.1)               # Sleep 100ms
    device.writeReg(0x24, 0)      # Set installation direction: nine axis, six axis
    time.sleep(0.1)               # Sleep 100ms
    device.save()                 # Save

def AccelerationCalibration(device):
    """
    Acceleration calibration
    :param device: Device model
    :return:
    """
    device.AccelerationCalibration()                 # Acceleration calibration
    print("Acceleration calibration completed")

def FiledCalibration(device):
    """
    Magnetic field calibration
    :param device: Device model
    :return:
    """
    device.BeginFiledCalibration()                   # Start field calibration
    if input("Please rotate slowly around XYZ axes one by one. After completing all three axes, end calibration (Y/N)?").lower() == "y":
        device.EndFiledCalibration()                 # End field calibration
        print("Field calibration completed")

def startRecord():
    """
    Start recording data
    :return:
    """
    global _writeF
    global _IsWriteF
    _writeF = open(str(datetime.datetime.now().strftime('%Y%m%d%H%M%S')) + ".txt", "w")    # Create a new file
    _IsWriteF = True                                                                        # Set write flag
    Tempstr = "Chiptime"
    Tempstr += "\tax(g)\tay(g)\taz(g)"
    Tempstr += "\twx(deg/s)\twy(deg/s)\twz(deg/s)"
    Tempstr += "\tAngleX(deg)\tAngleY(deg)\tAngleZ(deg)"
    Tempstr += "\tT(°)"
    Tempstr += "\tmagx\tmagy\tmagz"
    Tempstr += "\r\n"
    _writeF.write(Tempstr)
    print("Started recording data")

def endRecord():
    """
    End recording data
    :return:
    """
    global _writeF
    global _IsWriteF
    _IsWriteF = False             # Set write flag to false
    _writeF.close()               # Close file
    print("Ended recording data")

def onUpdate(deviceModel):
    """
    Data update event
    :param deviceModel: Device model
    :return:
    """
    print("Chip time:" + str(deviceModel.getDeviceData("Chiptime"))
         , " Temperature:" + str(deviceModel.getDeviceData("temperature"))
         , " Acceleration:" + str(deviceModel.getDeviceData("accX")) + "," + str(deviceModel.getDeviceData("accY")) + "," + str(deviceModel.getDeviceData("accZ"))
         , " Angular velocity:" + str(deviceModel.getDeviceData("gyroX")) + "," + str(deviceModel.getDeviceData("gyroY")) + "," + str(deviceModel.getDeviceData("gyroZ"))
         , " Angle:" + str(deviceModel.getDeviceData("angleX")) + "," + str(deviceModel.getDeviceData("angleY")) + "," + str(deviceModel.getDeviceData("angleZ"))
         , " Magnetic field:" + str(deviceModel.getDeviceData("magX")) + "," + str(deviceModel.getDeviceData("magY")) + "," + str(deviceModel.getDeviceData("magZ"))
          )
    if (_IsWriteF):    # Record data
        Tempstr = " " + str(deviceModel.getDeviceData("Chiptime"))
        Tempstr += "\t" + str(deviceModel.getDeviceData("accX")) + "\t" + str(deviceModel.getDeviceData("accY")) + "\t" + str(deviceModel.getDeviceData("accZ"))
        Tempstr += "\t" + str(deviceModel.getDeviceData("gyroX")) + "\t" + str(deviceModel.getDeviceData("gyroY")) + "\t" + str(deviceModel.getDeviceData("gyroZ"))
        Tempstr += "\t" + str(deviceModel.getDeviceData("angleX")) + "\t" + str(deviceModel.getDeviceData("angleY")) + "\t" + str(deviceModel.getDeviceData("angleZ"))
        Tempstr += "\t" + str(deviceModel.getDeviceData("temperature"))
        Tempstr += "\t" + str(deviceModel.getDeviceData("magX")) + "\t" + str(deviceModel.getDeviceData("magY")) + "\t" + str(deviceModel.getDeviceData("magZ"))
        Tempstr += "\r\n"
        _writeF.write(Tempstr)

        
        
def LoopReadThead(device):
    """
    Cyclic read data
    :param device:
    :return:
    """
    global running
    while running:                          # Changed from while(True)
        device.readReg(0x30, 41)            # Read data
        time.sleep(0.01)   

if __name__ == '__main__':
    try:
        print(welcome)
        device = deviceModel.DeviceModel(
            "MyJY901",
            Protocol485Resolver(),
            JY901SDataProcessor(),
            "51_0"
        )
        device.ADDR = 0x50
        if (platform.system().lower() == 'linux'):
            device.serialConfig.portName = "/dev/ttyUSB0"
        else:
            device.serialConfig.portName = "COM7"
        device.serialConfig.baud = 230400
        device.openDevice()
        readConfig(device)
        device.dataProcessor.onVarChanged.append(onUpdate)

        startRecord()
        t = threading.Thread(target=LoopReadThead, args=(device,))
        t.start()

        print("\nДля завершения программы нажмите Ctrl+C\n")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        signal_handler(signal.SIGINT, None)