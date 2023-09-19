import os
import configparser
from pyzabbix import ZabbixMetric, ZabbixSender
from utils.json_reader import obtener_nombres_de_hosts_desde_json
from zabbix.api_util import get_host_ip


# Obtener la dirección IP de un host
def obtener_ip_del_host():
    # Obtener la ruta del archivo de configuración
    config_file_path = obtener_ruta_configuracion()
    # Obtener la configuración desde el archivo
    config = obtener_configuracion(config_file_path)

    # Obtener la URL y el token de autenticación de Zabbix
    zabbix_url = config.get('zabbix', 'zabbix_api_url')
    auth_token = config.get('zabbix', 'auth_token')

    # Obtener la ruta al directorio de archivos JSON
    json_directory = obtener_ruta_json()

    # Obtener los nombres de los hosts desde un archivo JSON
    nombres_de_hosts = obtener_nombres_de_hosts_desde_json(json_directory)

    # Obtener las direcciones IP de los hosts
    direcciones_ips = obtener_direcciones_ip(zabbix_url, auth_token, nombres_de_hosts)

    return direcciones_ips


# Obtener la ruta del archivo de configuración
def obtener_ruta_configuracion():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    project_directory = os.path.dirname(script_directory)
    return os.path.join(project_directory, 'config.ini')


# Obtener la configuración desde el archivo de configuración
def obtener_configuracion(config_file_path):
    config = configparser.ConfigParser()
    config.read(config_file_path)
    return config


# Obtener la ruta del archivo JSON que contiene los nombres de los hosts
def obtener_ruta_json():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    project_directory = os.path.dirname(script_directory)
    return os.path.join(project_directory, 'json_files/hosts_reachable.json')


# Obtener las direcciones IP de los hosts
def obtener_direcciones_ip(zabbix_url, auth_token, nombres_de_hosts):
    direcciones_ips = []
    for host_name in nombres_de_hosts:
        host_ip = get_host_ip(host_name, zabbix_url, auth_token)
        print(f"La dirección IP de {host_name} es: {host_ip}")
        direcciones_ips.append(host_ip)
    return direcciones_ips


# Enviar datos a Zabbix
def enviar_datos_zabbix(zabbix_server, zabbix_port, keys, data):
    # Obtener las métricas a enviar a Zabbix
    metrics = obtener_metricas_para_enviar(keys, data)
    # Imprimir las métricas
    imprimir_metricas(metrics)

    try:
        # Crear un objeto ZabbixSender y enviar los datos a Zabbix
        zabbix_sender = ZabbixSender(zabbix_server=zabbix_server, zabbix_port=zabbix_port)
        result = zabbix_sender.send(metrics)
        print(f"Datos enviados a Zabbix: {result}")
    except Exception as e:
        print(f"Error al enviar datos a Zabbix: {e}")


# Obtener las métricas a enviar a Zabbix
def obtener_metricas_para_enviar(keys, data):
    metrics = []

    for key, value in data.items():
        if key in keys:
            zabbix_key = keys[key]
            host = data['station.code']
            metrics.append(ZabbixMetric(host + '_QA', zabbix_key, value))

    return metrics


# Imprimir las métricas a enviar a Zabbix
def imprimir_metricas(metrics):
    print("Datos a enviar a Zabbix:")
    for item in metrics:
        print(f"Host: {item.host}, Key: {item.key}, Value: {item.value}")