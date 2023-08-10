import requests
import json


def get_host_ip(host_name, zabbix_url, auth_token):
    headers = {
        'Content-Type': 'application/json',
    }

    data = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["hostid"],
            "filter": {
                "host": host_name
            }
        },
        "auth": auth_token,
        "id": 1
    }

    response = requests.post(zabbix_url, headers=headers, data=json.dumps(data))
    result = response.json()

    host_id = result["result"][0]["hostid"]

    data = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["interfaces"],
            "selectInterfaces": ["ip"],
            "hostids": host_id
        },
        "auth": auth_token,
        "id": 1
    }

    response = requests.post(zabbix_url, headers=headers, data=json.dumps(data))
    result = response.json()

    host_ip = result["result"][0]["interfaces"][0]["ip"]
    return host_ip
