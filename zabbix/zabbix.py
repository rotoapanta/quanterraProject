from pyzabbix import ZabbixMetric, ZabbixSender
import configparser
from utilities.json_reader import obtener_nombres_de_hosts_desde_json
from zabbix.api_util import get_host_ip


def obtener_ip_del_host():
    config = configparser.ConfigParser()
    config.read('C:/Users/rtoapanta/PycharmProjects/quanterraProject/config.ini')

    zabbix_url = config.get('zabbix', 'zabbix_api_url')
    auth_token = config.get('zabbix', 'auth_token')
    # Ruta al archivo JSON
    ruta_json = "C:/Users/rtoapanta/PycharmProjects/quanterraProject/json_files/host_codes.json"
    nombres_de_hosts = obtener_nombres_de_hosts_desde_json(ruta_json)
    print(nombres_de_hosts)
    direcciones_ips = []  # Aquí almacenaremos las direcciones IP
    for host_name in nombres_de_hosts:
        host_ip = get_host_ip(host_name, zabbix_url, auth_token)
        print(f"La dirección IP de {host_name} es: {host_ip}")
        direcciones_ips.append(host_ip)  # Agregamos la dirección IP a la lista

    return direcciones_ips  # Devolvemos la lista de direcciones IP


def enviar_datos_zabbix(zabbix_server, zabbix_port, keys, data):
    metrics = []

    # Crear paquete con los datos para cada clave (key)
    for key, value in data.items():
        if key in keys:
            zabbix_key = keys[key]
            host = data['station.code']  # Obtener el valor del station code
            metrics.append(ZabbixMetric(host + '_QA', zabbix_key, value))

    # Imprimir los datos que se van a enviar a Zabbix
    print("Datos a enviar a Zabbix:")
    for item in metrics:
        print(f"Host: {item.host}, Key: {item.key}, Value: {item.value}")

    # Enviar el paquete a Zabbix
    try:
        zabbix_sender = ZabbixSender(zabbix_server=zabbix_server, zabbix_port=zabbix_port)
        result = zabbix_sender.send(metrics)
        print(f"Datos enviados a Zabbix: {result}")
    except Exception as e:
        print(f"Error al enviar datos a Zabbix: {e}")

