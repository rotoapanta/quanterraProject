import configparser
import logging
import os
from api.api_zbx_processing import get_ip_hostname_dict, get_values_concurrently, transform_station_data
from zabbix.zabbix_sender import send_data_to_zabbix
import datetime


def main():
    """
    Main execution function for the Quanterra data processing script.

    This function performs several key operations:
    1. It sets up logging and retrieves the current date for log filename generation.
    2. Fetches the IP-Hostname mapping from Zabbix using the `get_ip_hostname_dict` function.
    3. Defines the metrics to be collected from each Quanterra device.
    4. Concurrently fetches data from devices using `get_values_concurrently`.
    5. Transforms the fetched data for Zabbix compatibility.
    6. Reads Zabbix configuration from 'config.ini' and sends data to Zabbix server.

    Any exceptions encountered during execution are logged, ensuring proper error handling and debugging capabilities.

    :return: None
    """

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
    # Add a startup message
    logger.info("Starting the program")
    try:
        # Obtain IP-Hostname mapping from Zabbix
        ip_hostname_dict = get_ip_hostname_dict()
        print(f"IP-Hostname Dictionary: {ip_hostname_dict}")
        # Define metrics to be collected
        arguments = ["StationCode", "SerialNumber", "InputVoltage", "SystemTemp", "SatUsed", "MediaSite1", "MediaSite2",
                     "Q330Serial", "MainCurrent", "ClockQuality"]
        # Concurrently fetch data from devices
        all_data = get_values_concurrently(list(ip_hostname_dict.keys()), arguments)
        # Transform data for Zabbix compatibility
        all_data_transformado = transform_station_data(all_data, ip_hostname_dict)
        print(all_data_transformado)
        # Read Zabbix configuration and send data
        config = configparser.ConfigParser()
        config.read('config.ini')
        zabbix_server = config.get('zabbix', 'zabbix_server')
        zabbix_port = int(config.get('zabbix', 'zabbix_port'))
        # Send data to Zabbix server
        try:
            send_data_to_zabbix(zabbix_server, zabbix_port, all_data_transformado)
        except Exception as e:
            logger.error(f"Error sending data to Zabbix: {e}")
    except Exception as e:
        logger.error(f"Main execution error: {e}")
    finally:
        logger.info("End of the program")  # Add a completion message


if __name__ == "__main__":
    main()
