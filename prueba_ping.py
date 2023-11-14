import subprocess
import concurrent.futures
import logging

# Configura el sistema de registro de errores
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Función para hacer ping a múltiples estaciones
def ping_multiple_stations(ip_list):
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(ping_station, ip_list))

    # Results contendrá una lista de tuplas con el resultado de los pings
    for ip, result in zip(ip_list, results):
        if result[0]:  # Si el ping fue exitoso
            print(f"Ping exitoso a {ip}")
        else:
            print(f"Fallo en el ping a {ip}: {result[1]}")


# Función para hacer ping a una estación
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


# Ejemplo de uso
if __name__ == "__main__":
    # Lista de direcciones IP de las estaciones a las que deseas hacer ping
    ip_list = ["192.168.17.51", "192.168.17.52", "192.168.17.53", "192.168.6.53", "192.168.16.61", "192.168.16.68",
               "192.168.16.67", "192.168.16.66", "192.168.16.64", "192.168.16.71", "192.168.16.63", "192.168.16.65",
               "192.168.33.51", "192.168.33.54", "192.168.30.53", "192.168.30.60", "192.168.16.79", "192.168.6.59",
               "192.168.6.60", "192.168.6.66", "192.168.6.73"]  # Agrega aquí las direcciones IP
    ping_multiple_stations(ip_list)
