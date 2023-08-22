import requests
import json

# URL de la API de Zabbix
url = 'http://192.168.1.115/zabbix/api_jsonrpc.php'

# Datos de autenticación
headers = {'Content-Type': 'application/json'}
auth_payload = {
    'jsonrpc': '2.0',
    'method': 'user.login',
    'params': {
        'user': 'rtoapanta',
        'password': 'TECNOLOGO',
    },
    'id': 1,
}

response = requests.post(url, data=json.dumps(auth_payload), headers=headers)
auth_result = response.json()

# Verificar si el inicio de sesión fue exitoso y obtener el token
if "result" in auth_result:
    # Token de acceso
    zabbix_token = auth_result["result"]
    print("Inicio de sesión exitoso. Token:", zabbix_token)

# Obtener hosts que contienen "_QA" en el nombre
host_payload = {
    'jsonrpc': '2.0',
    'method': 'host.get',
    'params': {
        'output': ['host', 'interfaces', 'items'],
        'search': {'name': '_QA'},
        'selectGroups': 'extend',
        'selectInterfaces': ['ip', 'useip'],
        'selectItems': ['key_', 'lastvalue'],
    },
    'auth': zabbix_token,
    'id': 2,
}

response = requests.post(url, data=json.dumps(host_payload), headers=headers)
host_result = response.json()

# Filtrar los hosts con conectividad usando el Template Module ICMP Ping
reachable_hosts = []
rejected_hosts = []

for host in host_result['result']:
    for interface in host['interfaces']:
        if interface.get('ip') and interface.get('useip') == "1":
            icmp_ping_item = next((item for item in host.get('items', []) if item.get('key_') == 'icmpping'), None)
            if icmp_ping_item and float(icmp_ping_item.get('lastvalue', 0)) == 1:
                reachable_hosts.append(host['host'])
                break
    else:
        rejected_hosts.append(host['host'])

# Eliminar el sufijo "_QA" de los nombres de host
reachable_hosts_without_suffix = [host_name[:-3] if host_name.endswith('_QA') else host_name for host_name in
                                  reachable_hosts]
rejected_hosts_without_suffix = [host_name[:-3] if host_name.endswith('_QA') else host_name for host_name in
                                 rejected_hosts]

# Crear los diccionarios con el formato deseado
output_data_reachable = {
    "hosts": reachable_hosts_without_suffix
}

output_data_rejected = {
    "hosts": rejected_hosts_without_suffix
}

# Almacenar en archivos JSON
output_file_path_reachable = ('C:/Users/rtoapanta/PycharmProjects/quanterraProject/json_files/connected_hosts_reachable'
                              '.json')
output_file_path_rejected = ('C:/Users/rtoapanta/PycharmProjects/quanterraProject/json_files/connected_hosts_rejected'
                             '.json')

with open(output_file_path_reachable, 'w') as json_file:
    json.dump(output_data_reachable, json_file, indent=4)

with open(output_file_path_rejected, 'w') as json_file:
    json.dump(output_data_rejected, json_file, indent=4)

print(
    f"Se han almacenado {len(reachable_hosts)} hosts con conectividad en el archivo 'connected_hosts_reachable.json'.")
print(f"Se han almacenado {len(rejected_hosts)} hosts rechazados en el archivo 'connected_hosts_rejected.json'.")
