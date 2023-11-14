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
    The 'send_data_to_zabbix' function sends collected data to a Zabbix server. It performs the following tasks:
    1. Constructs Zabbix metrics for the provided data.
    2. Attempts to send the metrics to the specified Zabbix server.
    3. Logs success or error messages.

    :param zabbix_server: The URL or IP address of the Zabbix server.
    :type zabbix_server: str
    :param zabbix_port: The port number used for communication with the Zabbix server.
    :type zabbix_port: int
    :param all_data: A dictionary containing the collected data for different hosts.
    :type all_data: dict
    :returns: None
    :raises: Exception (if any error occurs during the data sending process)
    """
    metrics = []

    for host, data in all_data.items():
        # Obtain the values for this station
        station_code = data['station.code']
        serial_number = data['serial.number']
        input_voltage = data['input.voltage']
        system_temp = data['system.temp']
        sat_used = data['sat.used']
        q330_serial = data['q330.serial']
        media_site1_space_occupied = data['media.site1.space.occupied']
        media_site2_space_occupied = data['media.site2.space.occupied']
        main_current = data['main.current']
        clock_quality = data['clock.quality']


        # Create metrics for each value
        metrics.append(ZabbixMetric(host, 'station.code', station_code))
        metrics.append(ZabbixMetric(host, 'serial.number', serial_number))
        metrics.append(ZabbixMetric(host, 'input.voltage', input_voltage))
        metrics.append(ZabbixMetric(host, 'system.temp', system_temp))
        metrics.append(ZabbixMetric(host, 'sat.used', sat_used))
        metrics.append(ZabbixMetric(host, 'q330.serial', q330_serial))
        metrics.append(ZabbixMetric(host, 'media.site1.space.occupied', media_site1_space_occupied))
        metrics.append(ZabbixMetric(host, 'media.site2.space.occupied', media_site2_space_occupied))
        metrics.append(ZabbixMetric(host, 'main.current', main_current))
        metrics.append(ZabbixMetric(host, 'clock.quality', clock_quality))
    try:
        # Create a ZabbixSender object and send the data to Zabbix
        zabbix_sender = ZabbixSender(zabbix_server=zabbix_server, zabbix_port=zabbix_port)
        result = zabbix_sender.send(metrics)
        logging.info(f"Datos enviados a Zabbix: {result}")
    except Exception as e:
        logging.error(f"Error al enviar datos a Zabbix: {e}")
