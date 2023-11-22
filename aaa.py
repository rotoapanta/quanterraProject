import re
import requests
from pyzabbix.api import ZabbixAPI
import configparser
import logging
import os
from utils import utilities
import datetime
import concurrent.futures

# Get the current date in the desired format (Year-Month-Day)
current_date = datetime.date.today().strftime("%Y-%m-%d")
# Get the full path to the '_gps_netrs.log' file in the 'logs' folder
logs_folder = 'logs'
if not os.path.exists(logs_folder):
    os.makedirs(logs_folder)

# File name of the log file with the date
log_file = os.path.join(logs_folder, f'{current_date}_gps_netrs.log')
# Configure the error logging system
logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %('
                                                                   'message)s')
logger = logging.getLogger(__name__)


def get_values(ip, arguments):
    results = {}

    # Definición de las expresiones regulares para cada argumento
    patterns = {
        "StationCode": r"Station EC-(\w+)",
        "SerialNumber": r"Tag (\d+) - Station EC-(\w+)",
        "MediaSite": r"MEDIA site \d+ crc=0x\w+ .* capacity=\d+\.?\d*Mb  free=(\d+\.\d+)%",
        "Q330Serial": r"Q330 Serial Number: (.+)",
        "ClockQuality": r"Clock Quality: (\d+)%",
        "InputVoltage": r"Input Voltage: (\d+\.\d+)V",
        "SystemTemp": r"System Temperature: (\d+)C",
        "MainCurrent": r"Main Current: (\d+)ma",
        "SatUsed": r"Sat. Used: (\d+)"
    }

    # Mapeo de argumentos a claves del resultado
    key_mapping = {
        "StationCode": "station.code",
        "SerialNumber": "serial.number",
        "MediaSite1": "media.site1.space.occupied",
        "MediaSite2": "media.site2.space.occupied",
        "Q330Serial": "q330.serial",
        "ClockQuality": "clock.quality",
        "InputVoltage": "input.voltage",
        "SystemTemp": "system.temp",
        "MainCurrent": "main.current",
        "SatUsed": "sat.used"
    }

    try:
        url_base = f"http://{ip}:6381/stats.html"
        response = requests.get(url_base, timeout=10)
        response.raise_for_status()
        response_text = response.text

        # Procesar MediaSite1 y MediaSite2
        media_matches = re.findall(patterns["MediaSite"], response_text)
        if len(media_matches) >= 2:
            results[key_mapping["MediaSite1"]] = str(100 - float(media_matches[0]))
            results[key_mapping["MediaSite2"]] = str(100 - float(media_matches[1]))
        elif len(media_matches) == 1:
            results[key_mapping["MediaSite1"]] = str(100 - float(media_matches[0]))
            results[key_mapping["MediaSite2"]] = "No disponible"

        # Procesar otros argumentos
        for argument in arguments:
            if argument not in ["MediaSite1", "MediaSite2"]:
                pattern = patterns.get(argument)
                match = re.search(pattern, response_text)
                if match:
                    result_key = key_mapping.get(argument, argument)
                    results[result_key] = match.group(1)

    except Exception as e:
        logger.error(f"Error processing argument {argument} for {ip}: {e}")

    return results


# Ejemplo de cómo usar la función
#ip = "192.168.17.52"
#ip = "192.168.16.67"
#ip = "192.168.6.53"
#ip = "192.168.217.47"
#ip = "192.168.6.67"
ip = "192.168.6.73"
arguments = ["StationCode", "SerialNumber", "InputVoltage", "SystemTemp", "SatUsed", "MediaSite1", "MediaSite2",
             "Q330Serial", "MainCurrent", "ClockQuality"]
resultados = get_values(ip, arguments)

print(resultados)
