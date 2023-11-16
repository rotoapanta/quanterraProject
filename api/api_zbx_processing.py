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


# Función para obtener el diccionario IP - Hostname
def get_ip_hostname_dict():
    config = configparser.ConfigParser()
    config.read('config.ini')
    zabbix_url = config.get('zabbix', 'zabbix_url')
    zabbix_user = config.get('zabbix', 'zabbix_user')
    zabbix_password = config.get('zabbix', 'zabbix_password')
    try:
        # Configura la conexión a tu servidor Zabbix
        zapi = ZabbixAPI(url=zabbix_url, user=zabbix_user, password=zabbix_password)

        # Encuentra el template por nombre
        template_name = "Template Quanterra"
        template = zapi.template.get(filter={"host": template_name})

        ip_hostname_dict = {}

        if not template:
            logger.error(f"No se encontró el template '{template_name}'")
        else:
            template_id = template[0]["templateid"]
            # Encuentra los hosts asociados al template
            hosts = zapi.host.get(templateids=[template_id], selectInterfaces=["ip", "host"])

            # Hacer ping a las estaciones
            ip_set = {host["interfaces"][0]["ip"] for host in hosts if host["interfaces"]}
            ip_list = list(ip_set)
            print(f"LIST {ip_list}")

            ping_results = utilities.ping_multiple_stations(ip_list)

            # Mapear los resultados de ping a IPs
            ping_results_dict = {result[0]: result[1] for result in ping_results}

            # Conjunto para rastrear IPs procesadas
            processed_ips = set()

            # Procesar estaciones después de hacer ping
            for host in hosts:
                hostname = host["host"]
                for interface in host["interfaces"]:
                    ip = interface["ip"]
                    # Verificar si la IP ya ha sido procesada
                    if ip not in processed_ips:
                        processed_ips.add(ip)
                        is_reachable = ping_results_dict.get(ip, (False, None))[0]
                        if is_reachable:
                            ip_hostname_dict[ip] = hostname
                            print(f"Host alcanzable: {hostname} con IP {ip}")
                        else:
                            print(f"Host no alcanzable: {hostname} con IP {ip}")

            # Cerrar sesión en Zabbix
        zapi.user.logout()
        print(f"FUNCION {ip_hostname_dict}")
        return ip_hostname_dict

    except Exception as e:
        logger.error(f"Error al obtener el diccionario IP - Hostname: {e}")
        return {}


def get_values(ip, arguments):
    """
    The 'get_values' function retrieves specific metrics from a GPS NetRS device by making HTTP requests.
    It takes the IP address of the device and a list of requested arguments as parameters.

    The function performs the following steps:
    1. Constructs the base URL for device-specific data retrieval.
    2. Reads Zabbix server credentials from 'config.ini'.
    3. Iterates through the provided arguments, constructing specific URLs for data retrieval.
    4. Sends HTTP requests with authentication to the device and extracts the response data.
    5. Parses the response text using regular expressions to extract metric values.
    6. Populates a dictionary with metric values based on the provided arguments.
    7. Logs any errors that occur during request execution or data processing.
    8. Returns the dictionary of metric values.

    :param ip: The IP address of the GPS NetRS device.
    :type ip: str
    :param arguments: A list of metric arguments to retrieve from the device.
    :type arguments: list
    :returns: A dictionary containing the retrieved metric values.
    :rtype: dict
    :raises: Exception if any errors occur during the HTTP request, data processing, or value retrieval.
    """

    results = {}  # Define 'results' before the 'try' block

    # Define the regular expressions here, e.g., using raw strings (r"")
    patterns = {
        "StationCode": r"Station EC-(\w+)",
        "SerialNumber": r"Tag (\d+) - Station EC-(\w+)",
        "MediaSite1": r"MEDIA site 1 crc=0x\w+ (?:IN USE state: ACTIVE|IN USE state: READY|RESERVE state: \w+)  "
                      r"capacity=\d+\.?\d*Mb  free=(\d+\.\d+)%",
        "MediaSite2": r"MEDIA site 2 crc=0x\w+ (?:IN USE state: ACTIVE|IN USE state: READY|RESERVE state: \w+)  "
                      r"capacity=\d+\.?\d*Mb  free=(\d+\.\d+)%",
        "Q330Serial": r"Q330 Serial Number: (.+)",
        "ClockQuality": r"Clock Quality: (\d+)%",
        "InputVoltage": r"Input Voltage: (\d+\.\d+)V",
        "SystemTemp": r"System Temperature: (\d+)C",
        "MainCurrent": r"Main Current: (\d+)ma",
        "SatUsed": r"Sat. Used: (\d+)"
    }

    try:
        url_base = f"http://{ip}:6381/stats.html"
        results = {}
        for argument in arguments:
            full_url = f"{url_base}"
            try:
                response = requests.get(full_url, timeout=10)
                response.raise_for_status()
                response_text = response.text
                for arg, pattern in patterns.items():
                    match = re.search(pattern, response_text)
                    if match:
                        if arg == "StationCode":
                            results["station.code"] = match.group(1)
                        elif arg == "SerialNumber":
                            results["serial.number"] = match.group(1)
                        elif arg == "InputVoltage":
                            results["input.voltage"] = match.group(1)
                        elif arg == "SystemTemp":
                            results["system.temp"] = match.group(1)
                        elif arg == "SatUsed":
                            results["sat.used"] = match.group(1)
                        elif arg == "MediaSite1":
                            media_site1_value = float(match.group(1))
                            results["media.site1"] = media_site1_value
                            # Calcular el espacio ocupado
                            results["media.site1.space.occupied"] = 100 - media_site1_value
                        elif arg == "MediaSite2":
                            media_site2_value = float(match.group(1))
                            results["media.site2"] = media_site2_value
                            # Calcular el espacio ocupado
                            results["media.site2.space.occupied"] = 100 - media_site2_value
                        elif arg == "SatUsed":
                            results["sat.used"] = match.group(1)
                        elif arg == "Q330Serial":
                            results["q330.serial"] = match.group(1)
                        elif arg == "MainCurrent":
                            results["main.current"] = match.group(1)
                        elif arg == "ClockQuality":
                            results["clock.quality"] = match.group(1)
            except requests.Timeout:
                logging.error(f"Timeout al intentar conectarse a {full_url}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error al hacer la solicitud HTTP para {argument}: {e}")
            except Exception as e:
                logger.error(f"Error al procesar el argumento {argument} para {ip}: {e}")
    except Exception as e:
        logger.error(f"Error al obtener valores para {ip}: {e}")
    print(results)
    return results


def get_values_concurrently(ip_list, arguments):
    """
    Realiza solicitudes HTTP en paralelo a múltiples dispositivos GPS NetRS para obtener métricas.

    :param ip_list: Lista de direcciones IP de los dispositivos.
    :type ip_list: list
    :param arguments: Argumentos de métricas a recuperar de los dispositivos.
    :type arguments: list
    :return: Diccionario con los resultados de cada dispositivo.
    :rtype: dict
    """
    results = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Crear un futuro para cada llamada a get_values
        future_to_ip = {executor.submit(get_values, ip, arguments): ip for ip in ip_list}
        # Recopilar los resultados a medida que se completan las tareas
        for future in concurrent.futures.as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                results[ip] = future.result()
            except Exception as e:
                logger.error(f"Error al obtener valores para {ip}: {e}")
    print(f"RESUL {results}")
    return results


def transformar_datos_estaciones(datos_estaciones, mapeo_ip_hostname):
    datos_transformados = {}
    for ip, datos in datos_estaciones.items():
        hostname = mapeo_ip_hostname.get(ip)
        if hostname:
            datos_transformados[hostname] = datos
    return datos_transformados
