import sys
import requests
import configparser
from utilities.extract_data import extraer_datos_zabbix
from zabbix.zabbix import enviar_datos_zabbix
from zabbix.zabbix import obtener_ip_del_host


def obtener_contenido_pagina(host_ip):
    # Leer la configuración desde config.ini
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Obtener el nombre del host desde la sección [zabbix]
    # ip_host = config.get('host', 'ip_host')

    # Construir la URL de la página web utilizando el nombre del host
    url_host = f"http://{host_ip}:6381/stats.html"
    print(f"URL {url_host}")

    # Realizar solicitud HTTP y obtener el contenido de la página
    try:
        response = requests.get(url_host)
        response.raise_for_status()  # Verificar si hubo errores en la solicitud
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener el contenido de la página: {e}")
        return None


if __name__ == "__main__":

    host_ips = obtener_ip_del_host()
    print(f"Direcciones IPs del host: {host_ips}")

    # Obtain the content of the webpage
    url = ""
    print(f"Dirección entrante: {host_ips}")
    page_content = obtener_contenido_pagina(host_ips)

    if page_content is None:
        exit()

    # Extract data from the webpage using the script "extract_data.py"
    data = extraer_datos_zabbix(page_content)

    # Read Zabbix configuration from config.ini
    config = configparser.ConfigParser()
    config.read('config.ini')

    zabbix_server = config.get('zabbix', 'zabbix_server')
    zabbix_port = int(config.get('zabbix', 'zabbix_port'))

    # Leer las claves (keys) para cada item desde config.ini
    keys = {
        'serial.number': config.get('zabbix', 'key_serial_number'),
        'station.code': config.get('zabbix', 'key_station_code'),
        'media.site1': config.get('zabbix', 'key_media_site1'),
        'media.site2': config.get('zabbix', 'key_media_site2'),
        'q330.serial': config.get('zabbix', 'key_q330_serial'),
        'clock.quality': config.get('zabbix', 'key_clock_quality'),
        'input.voltage': config.get('zabbix', 'key_input_voltage'),
        'system.temp': config.get('zabbix', 'key_system_temp'),
        'main.current': config.get('zabbix', 'key_main_current'),
        'sat.used': config.get('zabbix', 'key_sat_used'),
    }
    # Enviar datos a Zabbix utilizando el script "zabbix.py"
    enviar_datos_zabbix(zabbix_server, zabbix_port, keys, data)
