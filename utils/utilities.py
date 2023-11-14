import subprocess
import concurrent.futures
import logging
import os
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


def ping_multiple_stations(ip_list):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(ping_station, ip): ip for ip in ip_list}
        for future in concurrent.futures.as_completed(futures):
            ip = futures[future]
            try:
                result = future.result()
                if result[0]:  # Si el ping fue exitoso
                    logger.info(f"Ping exitoso a {ip}")
                    results.append((ip, result[1]))
                else:
                    logger.error(f"Fallo en el ping a {ip}: {result[1]}")
            except Exception as e:
                logger.error(f"Error al hacer ping a {ip}: {e}")
    print(f" RESULTADO {results}")
    return results


def ping_station(ip):
    try:
        result = subprocess.run(["ping", "-c", "1", ip], capture_output=True, text=True, check=True)
        if result.returncode == 0:
            logger.info(f"Conexión exitosa a {ip}")
            return True, result.stdout
        else:
            logger.error(f"Fallo en la conexión a {ip}: {result.stderr}")
            return False, result.stderr
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al ejecutar el comando 'ping' para {ip}: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Error inesperado al hacer ping a {ip}: {e}")
        return False, str(e)
