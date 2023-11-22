import logging
import os
from pyzabbix import ZabbixMetric, ZabbixSender
import datetime

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


def send_data_to_zabbix(zabbix_server, zabbix_port, all_data):
    """
    Envia los datos recopilados al servidor Zabbix.

    :param zabbix_server: URL o dirección IP del servidor Zabbix.
    :param zabbix_port: Puerto del servidor Zabbix.
    :param all_data: Diccionario con los datos recopilados de cada host.
    """
    metrics = []
    for host, data in all_data.items():
        for key, value in data.items():
            metrics.append(ZabbixMetric(host, key, value))

    try:
        zabbix_sender = ZabbixSender(zabbix_server=zabbix_server, zabbix_port=zabbix_port)
        result = zabbix_sender.send(metrics)
        logging.info(f"Datos enviados a Zabbix: {result}")
    except Exception as e:
        logging.error(f"Error al enviar datos a Zabbix: {e}")
