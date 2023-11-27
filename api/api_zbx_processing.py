import re
import requests
from pyzabbix.api import ZabbixAPI
import configparser
import logging
import os
from utils import utilities
import datetime
import concurrent.futures

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


def get_ip_hostname_dict():
    """
    Retrieves a dictionary mapping IP addresses to hostnames for Zabbix-monitored devices.

    This function configures a connection to a Zabbix server using settings from 'config.ini'. It then queries the
    Zabbix API to obtain a list of devices associated with a specific template, identified by 'Template Quanterra'. A
    ping test is conducted for each IP address in this list to determine reachability. The function only includes
    those hosts that respond to the ping in the returned dictionary, thus ensuring that only active devices are
    considered.

    The function gracefully handles any exceptions during its operation, logging errors accordingly and ensuring
    the integrity of the process.

    :return: A dictionary mapping IP addresses to hostnames for reachable devices.
    :rtype: dict

    :raises Exception: Logs and returns an empty dictionary in case of any exception.
    """

    # Initialize the configuration parser
    config = configparser.ConfigParser()
    # Read the Zabbix configuration from 'config.ini' file
    config.read('config.ini')
    # Retrieve Zabbix server details from the configuration
    zabbix_url = config.get('zabbix', 'zabbix_url')
    zabbix_user = config.get('zabbix', 'zabbix_user')
    zabbix_password = config.get('zabbix', 'zabbix_password')
    try:
        # Establish a connection to the Zabbix server with provided credentials
        zapi = ZabbixAPI(url=zabbix_url, user=zabbix_user, password=zabbix_password)
        # Define the template name to be searched in Zabbix
        template_name = "Template Quanterra"
        # Fetch the template details using the API
        template = zapi.template.get(filter={"host": template_name})
        # Initialize an empty dictionary to hold IP-hostname mappings
        ip_hostname_dict = {}
        # Check if the template exists in Zabbix
        if not template:
            logger.error(f"No se encontró el template '{template_name}'")
        else:
            # Extract the template ID from the fetched details
            template_id = template[0]["templateid"]
            # Retrieve hosts associated with the specified template
            hosts = zapi.host.get(templateids=[template_id], selectInterfaces=["ip", "host"])
            # Create a set of IPs from the interfaces of fetched hosts
            ip_set = {host["interfaces"][0]["ip"] for host in hosts if host["interfaces"]}
            ip_list = list(ip_set)
            print(f"LISTA DE IPS: {ip_list}")
            # Perform a ping test on each IP address in the list
            ping_results = utilities.ping_multiple_stations(ip_list)
            # Map ping results (success/failure) to corresponding IP addresses
            ping_results_dict = {result[0]: result[1] for result in ping_results}
            # Set to keep track of IPs that have been processed
            processed_ips = set()
            # Iterate over the hosts to determine their reachability
            for host in hosts:
                hostname = host["host"]
                for interface in host["interfaces"]:
                    ip = interface["ip"]
                    if ip not in processed_ips:
                        # Mark the IP as processed
                        processed_ips.add(ip)
                        # Determine if the host is reachable
                        is_reachable = ping_results_dict.get(ip, (False, None))[0]
                        # Add reachable hosts to the dictionary
                        if is_reachable:
                            ip_hostname_dict[ip] = hostname
                            print(f"Reachable host: {hostname} with IP {ip}")
                        else:
                            print(f"Unreachable host: {hostname} with IP {ip}")
        # Logout from the Zabbix API session
        zapi.user.logout()
        return ip_hostname_dict

    except Exception as e:
        # Log any exceptions encountered during the process
        logger.error(f"Error retrieving IP-Hostname dictionary: {e}")
        return {}


def get_values_concurrently(ip_list, arguments):
    """
    Executes HTTP requests concurrently to multiple Quanterra devices to obtain metrics.

    This function leverages a thread pool executor to parallelize the data fetching process
    from multiple devices. It utilizes `get_values_with_error_handling` to handle any
    exceptions during the request.

    :param ip_list: A list of IP addresses of the devices.
    :type ip_list: list
    :param arguments: A list of metric arguments to retrieve from each device.
    :type arguments: list
    :return: A dictionary with the results from each device, keyed by IP address.
    :rtype: dict
    """

    # Initialize an empty dictionary to store the results
    results = {}
    # Use ThreadPoolExecutor for concurrent HTTP requests
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map each future to its corresponding IP address
        future_to_ip = {executor.submit(get_values_with_error_handling, ip, arguments): ip for ip in ip_list}
        # Process the results as they are completed
        for future in concurrent.futures.as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                # Obtain the result from the future
                result = future.result()
                # Ensure that no null results are added
                if result is not None:
                    results[ip] = result
            except Exception as e:
                # Log any errors encountered during fetching of values
                logger.error(f"Error fetching values for {ip}: {e}")
    print(f"RESUL {results}")
    return results


def get_values_with_error_handling(ip, arguments):
    """
    Retrieves values from a Quanterra device with error handling.

    This function attempts to fetch values from a specified Quanterra device. It handles
    common exceptions such as timeouts and request errors to ensure the program can continue
    running even if some devices are unreachable or return errors.

    :param ip: IP address of the Quanterra device.
    :type ip: str
    :param arguments: List of metric arguments to retrieve from the device.
    :type arguments: list
    :return: The results from the device or None in case of an error.
    :rtype: dict or None
    """

    try:
        # Attempt to get values from the device
        return get_values(ip, arguments)
    except requests.Timeout:
        # Log a timeout error and return None to indicate the device could not be reached
        logging.error(f"Timeout while trying to connect to {ip}, skipping to the next device.")
        return None  # Devuelve None para dispositivos con timeout
    except requests.exceptions.RequestException as e:
        # Log any request exceptions and return None
        logging.error(f"Connection error with {ip}: {e}")
        return None  # Return None for devices with connection errors
    except Exception as e:
        # Log any general errors and return None
        logging.error(f"General error processing device {ip}: {e}")
        return None  # Return None for any other errors


def get_values(ip, arguments):
    """
    Retrieves specified metrics from a Quanterra device via HTTP requests.

    This function connects to the Quanterra device using its IP address and fetches
    various metrics based on the provided arguments. It uses regular expressions to
    parse the retrieved HTML content and extract the relevant data.

    :param ip: IP address of the Quanterra device.
    :type ip: str
    :param arguments: A list of metric arguments to retrieve from the device.
    :type arguments: list
    :return: A dictionary containing the retrieved metric values.
    :rtype: dict
    """
    results = {}

    # Regular expressions for each argument, using raw strings (r"")
    patterns = {
        "StationCode": r"Station EC-(\w+)",
        "SerialNumber": r"Tag (\d+) - Station EC-(\w+)",
        "MediaSite1": r"MEDIA site 1 crc=0x\w+ (?:IN USE state: ACTIVE|IN USE state: READY|RESERVE state: \w+)  "
                      r"capacity=\d+\.?\d*Mb  free=(\d+\.\d+)%",
        "MediaSite2": r"MEDIA site 2 crc=0x\w+ (?:IN USE state: ACTIVE|IN USE state: READY|RESERVE state: \w+)  "
                      r"capacity=\d+\.?\d*Mb  free=(\d+\.\d+)%",
        "Q330Serial": r"Q330 Serial Number: (.+)",
        "ClockQuality": r"Clock Quality: (\d+)%",
        "InputVoltage": r"Input Voltage: (\d+\.\d+)V",
        "SystemTemp": r"System Temperature: (\d+)C",
        "MainCurrent": r"Main Current: (\d+)ma",
        "SatUsed": r"Sat. Used: (\d+)"
    }
    # Mapping arguments to result keys
    key_mapping = {
        "StationCode": "station.code",
        "SerialNumber": "serial.number",
        "MediaSite1": "media.site1.free.space",
        "MediaSite2": "media.site2.free.space",
        "Q330Serial": "q330.serial",
        "ClockQuality": "clock.quality",
        "InputVoltage": "input.voltage",
        "SystemTemp": "system.temp",
        "MainCurrent": "main.current",
        "SatUsed": "sat.used"
    }
    # Construct the base URL for the HTTP request
    url_base = f"http://{ip}:6381/stats.html"
    try:
        # Sending HTTP GET request to the device
        response = requests.get(url_base, timeout=20)
        # Raise an exception for HTTP request errors
        response.raise_for_status()
        # Extract the text content from the response
        response_text = response.text
        # Process each argument and extract data using regular expressions
        for arg in arguments:
            pattern = patterns.get(arg)
            if pattern:
                # Search for the pattern in the response text
                match = re.search(pattern, response_text)
                if match:
                    # Map the argument to the corresponding key and store the result
                    mapped_key = key_mapping.get(arg)
                    if mapped_key:
                        # Para MediaSite1 y MediaSite2, calcula el espacio ocupado
                        if arg in ["MediaSite1", "MediaSite2"]:
                            free_space = float(match.group(1))
                            results[mapped_key] = str(free_space)
                        else:
                            results[mapped_key] = match.group(1)
    except requests.Timeout:
        # Log a timeout error
        logging.error(f"Timeout while trying to connect to {url_base}")
    except requests.exceptions.RequestException as e:
        # Log any HTTP request errors
        logging.error(f"HTTP request error for {url_base}: {e}")
    except Exception as e:
        # Log any general errors
        logging.error(f"General error processing request for {ip}: {e}")
    print(results)
    return results


def transform_station_data(station_data, ip_hostname_map):
    """
    Transforms station data by mapping IP addresses to hostnames.

    This function takes a dictionary of station data keyed by IP addresses and
    a mapping of IP addresses to hostnames. It returns a new dictionary with
    hostnames as keys while preserving the data structure.

    :param station_data: A dictionary containing data for each station, keyed by IP address.
    :type station_data: dict
    :param ip_hostname_map: A dictionary mapping IP addresses to hostnames.
    :type ip_hostname_map: dict
    :return: A dictionary with transformed keys (hostnames) and the same data structure.
    :rtype: dict
    """
    transformed_data = {}

    # Iterate over each item in the station data
    for ip, data in station_data.items():
        # Retrieve the corresponding hostname from the IP-hostname mapping
        hostname = ip_hostname_map.get(ip)
        # If a hostname is found, use it as the key in the transformed data
        if hostname:
            transformed_data[hostname] = data

    return transformed_data
