import json
import os


def obtener_nombres_de_hosts_desde_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
        host_names = data["hosts"]
        # Agregar "_QA" al final de cada nombre de host
        host_names = [names + "_QA" for names in host_names]
    return host_names