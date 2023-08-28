import sys
import requests
import configparser
from utilities.extract_data import extraer_datos_zabbix
from zabbix.zabbix import enviar_datos_zabbix
from zabbix.zabbix import obtener_ip_del_host


def obtener_contenido_pagina(host_ip):
    # Construir la URL de la página web utilizando la dirección IP del host
    url_host = f"http://{host_ip}:6381/stats.html"
    #print(f"URL {url_host}")

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

    # Lista para almacenar los contenidos de las páginas
    all_page_contents = []

    # Obtener los contenidos de las páginas para cada dirección IP
    for host_ip in host_ips:
        page_content = obtener_contenido_pagina(host_ip)
        if page_content is not None:
            all_page_contents.append(page_content)

    if not all_page_contents:
        print("No se pudieron obtener los contenidos de las páginas.")
        sys.exit(1)

    # Procesar y enviar los datos a Zabbix para cada estación
    for idx, page_content in enumerate(all_page_contents, start=1):
        data = extraer_datos_zabbix(page_content)

        print(f"Procesando datos para la estación {host_ips[idx-1]}:")
        for key, value in data.items():
            print(f"Key: {key}, Value: {value}")

        # Leer la configuración de Zabbix desde config.ini
        config = configparser.ConfigParser()
        config.read('config.ini')

        zabbix_server = config.get('zabbix', 'zabbix_server')
        zabbix_port = int(config.get('zabbix', 'zabbix_port'))

        # Leer las claves (keys) desde config.ini
        keys = {
            'serial.number': config.get('zabbix', 'key_serial_number'),
            'station.code': config.get('zabbix', 'key_station_code'),
            'media.site1.space.occupied': config.get('zabbix', 'key_media_site1_space_occupied'),
            'media.site2.space.occupied': config.get('zabbix', 'key_media_site2_space_occupied'),
            'q330.serial': config.get('zabbix', 'key_q330_serial'),
            'clock.quality': config.get('zabbix', 'key_clock_quality'),
            'input.voltage': config.get('zabbix', 'key_input_voltage'),
            'system.temp': config.get('zabbix', 'key_system_temp'),
            'main.current': config.get('zabbix', 'key_main_current'),
            'sat.used': config.get('zabbix', 'key_sat_used'),
        }

        # Enviar datos a Zabbix utilizando el script "zabbix.py"
        enviar_datos_zabbix(zabbix_server, zabbix_port, keys, data)
