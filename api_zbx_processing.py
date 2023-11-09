import re
import requests
from pyzabbix.api import ZabbixAPI
import configparser
import logging
import os
import subprocess

# Configura el registro de errores en un archivo llamado 'error.log' en la carpeta 'logs'
logs_folder = 'logs'
if not os.path.exists(logs_folder):
    os.makedirs(logs_folder)

log_file = '/home/rotoapanta/Documentos/Proyects/quanterraProject/logs/error.log'
logging.basicConfig(filename=log_file, level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Función para verificar la conectividad de un host
def check_host_connectivity(ip):
    try:
        result = subprocess.run(["ping", "-c", "1", ip], capture_output=True, text=True, check=True)
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except subprocess.CalledProcessError as e:
        return False, str(e)


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

            # Recopila las direcciones IP de los hosts y verifica su conectividad
            for host in hosts:
                for interface in host["interfaces"]:
                    ip = interface["ip"]
                    is_reachable, response_time = check_host_connectivity(ip)
                    if is_reachable:
                        hostname = host["host"]
                        ip_hostname_dict[ip] = hostname

        # Cierra la sesión
        zapi.user.logout()
        return ip_hostname_dict

    except Exception as e:
        logger.error(f"Error al obtener el diccionario IP - Hostname: {e}")
        return {}


a = get_ip_hostname_dict()
print(a)
