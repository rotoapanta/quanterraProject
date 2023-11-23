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
        return ip_hostname_dict

    except Exception as e:
        logger.error(f"Error al obtener el diccionario IP - Hostname: {e}")
        return {}


def process_devices(device_list, arguments):
    for device_ip in device_list:
        try:
            get_values(device_ip, arguments)
        except requests.Timeout:
            logging.error(f"Timeout al intentar conectarse a {device_ip}, saltando al siguiente dispositivo.")
            continue  # Continúa con el siguiente dispositivo
        except requests.exceptions.RequestException as e:
            logging.error(f"Error en la conexión con {device_ip}: {e}")
            continue  # Continúa con el siguiente dispositivo
        except Exception as e:
            logging.error(f"Error general al procesar el dispositivo {device_ip}: {e}")
            continue  # Continúa con el siguiente dispositivo


def get_values(ip, arguments):
    results = {}

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

    url_base = f"http://{ip}:6381/stats.html"
    results = {}

    try:
        response = requests.get(url_base, timeout=30)
        response.raise_for_status()
        response_text = response.text

        for arg in arguments:
            pattern = patterns.get(arg)
            if pattern:
                match = re.search(pattern, response_text)
                if match:
                    mapped_key = key_mapping.get(arg)
                    if mapped_key:
                        results[mapped_key] = match.group(1)
    except requests.Timeout:
        logging.error(f"Timeout al intentar conectarse a {url_base}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al hacer la solicitud HTTP para {url_base}: {e}")
    except Exception as e:
        logging.error(f"Error al procesar la solicitud para {ip}: {e}")

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
