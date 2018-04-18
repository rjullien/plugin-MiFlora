""""
Read data from Mi Flora plant sensor.

Reading from the sensor is handled by the command line tool "gatttool" that
is part of bluez on Linux.
No other operating systems are supported at the moment
inspired by #  https://github.com/open-homeautomation/miflora

usage:
cd [path plugin ou copy de ce script]/jeedom_MiFlora/3rparty
/usr/bin/python ./getMiFloraData.py C4:7C:8D:60:E8:21 2.6.6 0 hci0 high
"""

from threading import Lock
import re
import subprocess
import logging
import time
import math
import sys
logger = logging.getLogger(__name__)
lock = Lock()

# pylint: disable=too-many-arguments


def write_ble(mac, handle, value, write_adpater="hci0",
              write_security="high", retries=3):

    """
    Read from a BLE address

    @param: mac - MAC address in format XX:XX:XX:XX:XX:XX
    @param: handle - BLE characteristics handle in format 0xXX
    @param: value - value to write to the handle
    @param: timeout - timeout in seconds
    """
    global lock  # pylint: disable=global-statement
    attempt = 0
    delay = 10
    while attempt <= retries:
        try:
            cmd = "gatttool --adapter={} --device={} --char-write-req -a {} -n {} \
            --sec-level={} ".format(write_adpater, mac, handle, value, write_security)
            #print cmd
            #cmd = "gatttool --device={} --char-read -a {} 2>/dev/null".format(mac, handle)
            with lock:
                result = subprocess.check_output(cmd, shell=True)
            result = result.decode("utf-8").strip(' \n\t')
            #print("Got ",result," from gatttool")

        except subprocess.CalledProcessError as err:
            print("Error ", err.returncode, " from gatttool (", err.output, ")")

        attempt += 1
        # print("Waiting for ",delay," seconds before retrying")
        if attempt < retries:
            time.sleep(delay)
            delay *= 2

    return None

def read_ble(mac, handle, read_adpater="hci0", read_security="high",
             read_flora_debug=0, retries=3):
    """
    Read from a BLE address

    @param: mac - MAC address in format XX:XX:XX:XX:XX:XX
    @param: handle - BLE characteristics handle in format 0xXX
    @param: timeout - timeout in seconds
    """

    global lock  # pylint: disable=global-statement
    attempt = 0
    delay = 10
    while attempt <= retries:
        try:
            cmd = "gatttool --adapter={} --device={} --char-read -a {} \
            --sec-level={} 2>/dev/null".format(read_adpater, mac, handle, read_security)
            #print cmd
            with lock:
                result = subprocess.check_output(cmd,
                                                 shell=True)

            result = result.decode("utf-8").strip(' \n\t')
            # print("Got ",result, " from gatttool")
            # Parse the output
            res = re.search("( [0-9a-fA-F][0-9a-fA-F])+", result)

            if res:
                if read_flora_debug == "1":
                    return [int(x, 16) for x in res.group(0).split()]
                return result

        except subprocess.CalledProcessError as err:
            print("Error ", err.returncode, " from gatttool (", err.output, ")")

        # except subprocess.TimeoutExpired:
        #    print("Timeout while waiting for gatttool output")

        attempt += 1
        # print("Waiting for ",delay," seconds before retrying")
        if attempt < retries:
            time.sleep(delay)
            delay *= 2

    return None


def convert_temperature(rawValue):
    rawValueInt = rawValue[1] * 255 + rawValue[0]
    temperatureVal = 0.00000003044 * pow(rawValueInt, 3.0) - 0.00008038 * pow(rawValueInt,
                                                                           2.0) + rawValueInt * 0.1149 - 30.449999999999999
    return round(temperatureVal * 10) / 10


def convert_Lux(rawValue):
    rawValueInt = rawValue[0] * 1.0
    if rawValueInt>0:
    	sunlight = 0.08640000000000001 * (192773.17000000001 * math.pow(rawValueInt, -1.0606619))
    else:
    	sunlight = 0
    return sunlight


def convert_SoilEC(rawValue):
	rawValueInt = rawValue[1] * 255 + rawValue[0]
	soil_EC = (rawValueInt * 3.3) / (pow(2, 11) - 1)
	
	return soil_EC

def convert_SoilMoisture(rawValue):
	
	moisture = rawValue[0] * 1.0;
	#moisture = (moisture * 3.3) / (pow(2, 11) - 1)

	soilMoisture = 11.4293 + (0.0000000010698 * math.pow(moisture, 4.0) - 0.00000152538 * math.pow(moisture, 3.0) +  0.000866976 * math.pow(moisture, 2.0) - 0.169422 * moisture);

	soilMoisture = 100.0 * (0.0000045 * math.pow(soilMoisture, 3.0) - 0.00055 * math.pow(soilMoisture, 2.0) + 0.0292 * soilMoisture - 0.053);

	if soilMoisture < 0.0: 
		soilMoisture = 0.0
	elif soilMoisture > 60.0:
		soilMoisture = 60.0

	return round(soilMoisture, 1)


def convert_Battery(rawValue):
    rawValueInt = rawValue[0]
    return rawValueInt


def convert_Name(rawValue):
    # rawValueInt=rawValue[0]
    str1 = ''.join(chr(e) for e in rawValue)
    return str1


def convert_2Bytes(rawValue):
    rawValueInt = rawValue[1] * 255 + rawValue[0]
    return rawValueInt


print "Entering script"


timeout = 20
#mac_add = sys.argv[1]
#adpater = sys.argv[2]
#security = sys.argv[3]
firmware = "2.6.0"
flora_debug = "1"
adpater = "hci0"
security = "low"
mac_add = sys.argv[1]

print "Fetching :", mac_add


print "============="
print "Donnees de base :"
print "============="

# Gestion de la temperature de la terre
handlerd = "0x0034"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Soil Temperature brute:", result_flora
# avec convert_temperature 21.5, app: 22/23 live
temperature_terre = convert_temperature(result_flora)
print " -->Soil Temperature:", temperature_terre

# Gestion de la temperature de l'air
handlerd = "0x0037"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Air Temperature brute:", result_flora
temperature_air = convert_temperature(result_flora)
print " -->Air Temperature:", temperature_air

antoine = 8.07131 - (1730.63 / (233.426 + temperature_terre));
last_pressure = math.pow(10, antoine - 2)
# TODO: convert raw(0 - 1771) to 0 to 10(mS / cm)
# avec convert_Soil: 19,4% avec cette formule, app: 20/21%
#print " -->Last Pressure:", last_pressure

# Gestion des LUX
handlerd = "0x0025"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Lux brute:", result_flora
# 0.1 app: 0 moyenne 976 (semble bien etre la version live)
lux = convert_Lux(result_flora)
print " -->Lux:", lux

# Gestion de Soil ElectricalConductivity 
handlerd = "0x0031"
soil_EC_brut = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Soil EC brut:", soil_EC_brut
soilEC = convert_SoilEC(soil_EC_brut)
print " -->Soil EC:", soilEC, " (comment utiliser ?)"

# Gestion de Soil Moisture
handlerd = "0x003a"
soil_moisture_brut = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Soil Moisture brut: ", soil_moisture_brut
soil_moisture = convert_SoilMoisture(result_flora)
print " -->relativeHumidity:", soil_moisture

#moisture = soil_moisture * last_pressure;
#print " -->Moisture:", moisture


# Gestion de la batterie
# 0x004b
handlerd = "0x004b"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Batterie brut: ", result_flora
# 30 , app: courbe semble etre vers 35-37
batterie = convert_Battery(result_flora)
print " -->Batterie %: ", batterie


print "============="
print "Donnees de watering :"
print "============="


# Water Tank Level
# 0x008b
handlerd = "0x008b"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Water Tank Level Brut: ", result_flora
batterie = convert_Battery(result_flora)
print " -->Water Tank Level: ", batterie

# Watering Mode
handlerd = "0x0090"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Watering Mode: ", result_flora
batterie = convert_Battery(result_flora)
print " -->Watering Mode: ", batterie


# Watering Status
handlerd = "0x009a"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Watering Status: ", result_flora
batterie = convert_Battery(result_flora)
print " -->Watering Status: ", batterie


print "============="
print "Autres donnees :"
print "============="



"""
handlerd = "0x0028"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Inconnu brut: ", result_flora
# 30 , app: courbe semble etre vers 35-37
resultat = convert_Battery(result_flora)
print " -->Inconnu : ", resultat

handlerd = "0x002b"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Inconnu brut: ", result_flora
# 30 , app: courbe semble etre vers 35-37
resultat = convert_Battery(result_flora)
print " -->Inconnu : ", resultat

handlerd = "0x002e"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Inconnu brut: ", result_flora
# 30 , app: courbe semble etre vers 35-37
resultat = convert_Battery(result_flora)
print " -->Inconnu : ", resultat


handlerd = "0x0016"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Serial Number: ", result_flora
# 30 , app: courbe semble etre vers 35-37
resultat = convert_Name(result_flora)
print " -->Serial Number : ", resultat.encode('utf-8')

handlerd = "0x0012"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "System ID: ", result_flora
# 30 , app: courbe semble etre vers 35-37
resultat = convert_Battery(result_flora)
print " -->System ID : ", resultat


handlerd = "0x0005"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Appereance: ", result_flora
# 30 , app: courbe semble etre vers 35-37
resultat = convert_Battery(result_flora)
print " -->Appereance : ", resultat


# Livemeasure Period
handlerd = "0x003d"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Live measure Period Brut: ", result_flora
# 30 , app: courbe semble etre vers 35-37
resultat = convert_Battery(result_flora)
print " -->Live measure Period : ", resultat

# Led state, value is 1 or 0
handlerd = "0x003f"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "LED state: ", result_flora
resultat = convert_Battery(result_flora)
print " -->LED state : ", resultat

# Calibrated VWC
handlerd = "0x0041"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Calibrated VWC brut: ", result_flora
# 30 , app: courbe semble etre vers 35-37
resultat = convert_Battery(result_flora)
print " -->Calibrated VWC : ", resultat

# Calibrated air temperature
handlerd = "0x0044"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Calibrated air temperature: ", result_flora
# 30 , app: courbe semble etre vers 35-37
resultat = convert_temperature(result_flora)
print " -->Calibrated air temperature : ", resultat

"""

# Gestion du nom
handlerd = "0x0003"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Name brut: ", result_flora
Name = convert_Name(result_flora)
print " -->Name: ", Name

# Gestion du nom
handlerd = "0x0070"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Friendly Name brut: ", result_flora
Name = convert_Name(result_flora)
print " -->Friendly Name: ", Name

"""
# Couleur
handlerd = "0x0072"
result_flora = read_ble(mac_add, handlerd, adpater, security, flora_debug)
print "Couleur brut: ", result_flora
Name = convert_Name(result_flora)
print " -->Couleur: ", Name

"""