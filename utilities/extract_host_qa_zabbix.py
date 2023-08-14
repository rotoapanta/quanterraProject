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

# Token de acceso
auth_token = auth_result['result']
print(auth_token)

# Obtener hosts que contienen "_QA" en el nombre
host_payload = {
    'jsonrpc': '2.0',
    'method': 'host.get',
    'params': {
        'output': ['host'],
        'search': {'name': '_QA'},
        'selectGroups': 'extend',
        'selectInterfaces': ['ip'],
    },
    'auth': auth_token,
    'id': 2,
}

response = requests.post(url, data=json.dumps(host_payload), headers=headers)
host_result = response.json()

# Extraer los nombres de host y eliminar el sufijo "_QA"
host_names = [host['host'].replace('_QA', '') for host in host_result['result']]

# Crear el diccionario con el formato deseado
output_data = {
    "hosts": host_names
}

# Almacenar en un archivo JSON
with open('C:/Users/rtoapanta/PycharmProjects/quanterraProject/json_files/host_codes.json', 'w') as json_file:
    json.dump(output_data, json_file, indent=4)

print(f"Se han almacenado {len(host_names)} hosts en el archivo 'hosts_qa.json'.")
