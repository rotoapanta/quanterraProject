import logging
import os
from pyzabbix import ZabbixMetric, ZabbixSender
import datetime

# Get the current date in the desired format (Year-Month-Day)
current_date = datetime.date.today().strftime("%Y-%m-%d")
# Get the full path to the '_quanterra.log' file in the 'logs' folder
logs_folder = 'logs'
if not os.path.exists(logs_folder):
    os.makedirs(logs_folder)

# File name of the log file with the date
log_file = os.path.join(logs_folder, f'{current_date}_quanterra.log')
# Configure the error logging system
logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %('
                                                                   'message)s')
logger = logging.getLogger(__name__)


def send_data_to_zabbix(zabbix_server, zabbix_port, all_data):
    """
    Sends collected data metrics to a Zabbix server.

    This function prepares metrics from the collected data and sends them to a specified Zabbix server.
    It creates a ZabbixMetric object for each data point and transmits these metrics using ZabbixSender.

    :param zabbix_server: The IP address or hostname of the Zabbix server.
    :type zabbix_server: str
    :param zabbix_port: The port number on which the Zabbix server is listening.
    :type zabbix_port: int
    :param all_data: A dictionary containing the data to be sent. The keys are hostnames,
                     and values are dictionaries of metric data.
    :type all_data: dict
    :raises Exception: Captures any exceptions during the sending process and logs them.
    """

    # Initialize an empty list to store Zabbix metrics
    metrics = []
    # Iterate over all data items to create Zabbix metrics
    for host, data in all_data.items():
        for key, value in data.items():
            metrics.append(ZabbixMetric(host, key, value))

    try:
        # Initialize ZabbixSender with the server and port details
        zabbix_sender = ZabbixSender(zabbix_server=zabbix_server, zabbix_port=zabbix_port)
        # Send the metrics to the Zabbix server
        result = zabbix_sender.send(metrics)
        # Log the outcome of the transmission
        logging.info(f"Data sent to Zabbix: {result}")
    except Exception as e:
        # Log any exceptions that occur during data transmission
        logging.error(f"Error while sending data to Zabbix: {e}")

