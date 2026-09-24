"""Sender failures must propagate to the collector health check."""
from zabbix_utils import ItemValue, Sender


def send_data_to_zabbix(zabbix_server, zabbix_port, all_data, timeout=20):
    metrics = [ItemValue(host, key, value) for host, data in all_data.items() for key, value in data.items()]
    if not metrics:
        raise ValueError('Refusing empty sender batch')
    result = Sender(server=zabbix_server, port=zabbix_port, timeout=timeout).send(metrics)
    if result.failed or result.processed != len(metrics) or result.total != len(metrics):
        raise RuntimeError('Zabbix rejected or did not acknowledge all metrics')
    return result
