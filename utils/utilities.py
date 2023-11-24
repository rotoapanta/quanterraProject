import subprocess
import concurrent.futures
import logging
import os
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


def ping_multiple_stations(ip_list):
    """
    Pings multiple IP addresses concurrently and returns the results.

    This function creates a thread pool and dispatches ping requests to each IP address in the list.
    It records whether each ping was successful and logs the result. The function is useful for checking
    the reachability of multiple hosts in parallel.

    :param ip_list: A list of IP addresses to ping.
    :type ip_list: list[str]
    :return: A list of tuples containing the IP address and a tuple with a boolean indicating
             success and the ping output or error message.
    :rtype: list[tuple[str, tuple[bool, str]]]
    """

    # Initialize an empty list to store the results
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        # Mapping each IP to a future (asynchronous operation)
        futures = {executor.submit(ping_station, ip): ip for ip in ip_list}
        for future in concurrent.futures.as_completed(futures):
            ip = futures[future]
            try:
                # Retrieve the result of the ping operation
                result = future.result()
                # Log and append the result based on the ping success
                if result[0]:   # If the ping was successful
                    logger.info(f"Successful ping to {ip}")
                    results.append((ip, result[1]))
                else:
                    logger.error(f"Ping failed to {ip}: {result[1]}")
            except Exception as e:
                # Log any exceptions encountered during the ping
                logger.error(f"Error pinging {ip}: {e}")
    # Return the list of results
    return results


def ping_station(ip):
    """
    Executes a ping command to a single IP address.

    This function attempts to ping the specified IP address once and captures the output.
    It returns a boolean indicating the success of the ping and the output or error message.

    :param ip: The IP address to ping.
    :type ip: str
    :return: A tuple containing a boolean indicating success and the ping output or error message.
    :rtype: tuple[bool, str]
    """
    try:
        # Execute the ping command with a single attempt
        result = subprocess.run(["ping", "-c", "1", ip], capture_output=True, text=True, check=True)
        if result.returncode == 0:
            # Log and return the successful ping information
            logger.info(f"Successful connection to {ip}")
            return True, result.stdout
        else:
            # Log and return the failed ping information
            logger.error(f"Connection failed to {ip}: {result.stderr}")
            return False, result.stderr
    except subprocess.CalledProcessError as e:
        # Handle exceptions thrown by the subprocess module
        logger.error(f"Error executing ping command for {ip}: {e}")
        return False, str(e)
    except Exception as e:
        # Catch any unexpected exceptions during the ping operation
        logger.error(f"Unexpected error pinging {ip}: {e}")
        return False, str(e)
