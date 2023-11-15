import configparser
import logging
import os
from api.api_zbx_processing import get_ip_hostname_dict, get_values, get_values_concurrently
from zabbix.zabbix_sender import send_data_to_zabbix
import datetime


def main():
    """
    The 'main' function serves as the entry point of the GPS NetRS monitoring program. It performs the following tasks:
    1. Obtains the current date in the desired format (Year-Month-Day).
    2. Configures the error logging system and creates log files.
    3. Calls the 'get_ip_hostname_dict' function to retrieve the IP - Hostname dictionary.
    4. Defines a list of common arguments as strings.
    5. Creates a dictionary to store data for each host.
    6. Iterates through the IP - Hostname dictionary, calling 'get_values' function for each host and collecting data.
    7. Reads Zabbix configuration from 'config.ini'.
    8. Sends collected data to Zabbix using the 'send_data_to_zabbix' function.
    9. Logs errors and completion messages.

    This function does not accept any parameters.

    :returns: None
    :raises: subprocess.CalledProcessError (if command execution fails), Exception (if any other error occurs during
    execution)
    """
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

    logger.info("Inicio del programa")  # Add a startup message
    try:
        # Call the function to obtain the IP - Hostname dictionary
        ip_hostname_dict = get_ip_hostname_dict()
        # Define common arguments as a string
        arguments = ["StationCode", "SerialNumber", "InputVoltage", "SystemTemp", "SatUsed", "MediaSite1",
                     "MediaSite2", "Q330Serial", "MainCurrent", "ClockQuality"]

        # Llamar a la función para obtener los datos de manera concurrente
        all_data = get_values_concurrently(ip_hostname_dict.keys(), arguments)
        print("1")
        print(all_data)
        print("2")
        # Read Zabbix configuration from config.ini
        config = configparser.ConfigParser()
        config.read('config.ini')

        zabbix_server = config.get('zabbix', 'zabbix_server')
        zabbix_port = int(config.get('zabbix', 'zabbix_port'))

        try:
            # Send data to Zabbix using the "zabbix.py" script
            send_data_to_zabbix(zabbix_server, zabbix_port, all_data)
        except Exception as e:
            logger.error(f"Error al enviar datos a Zabbix: {e}")
    except Exception as e:
        logger.error(f"Error en la ejecución principal: {e}")
    finally:
        logger.info("Fin del programa")  # Add a completion message


if __name__ == "__main__":
    main()