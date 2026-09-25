"""Sender failures must propagate to the collector health check."""
from zabbix_utils import ItemValue, Sender


def send_data_to_zabbix(
    zabbix_server: str,
    zabbix_port: int,
    all_data: dict[str, dict[str, object]],
    timeout: int = 20,
) -> object:
    """Send a complete batch of collector metrics to Zabbix.

    Args:
        zabbix_server: Zabbix server hostname or IP address.
        zabbix_port: Zabbix trapper port.
        all_data: Metrics grouped by Zabbix host and item key.
        timeout: Maximum sender timeout in seconds.

    Returns:
        The result returned by ``zabbix_utils.Sender.send``.

    Raises:
        ValueError: If the metric batch is empty.
        RuntimeError: If Zabbix rejects or fails to acknowledge any metric.
    """
    metrics = [ItemValue(host, key, value) for host, data in all_data.items() for key, value in data.items()]
    if not metrics:
        raise ValueError('Refusing empty sender batch')
    result = Sender(server=zabbix_server, port=zabbix_port, timeout=timeout).send(metrics)
    if result.failed or result.processed != len(metrics) or result.total != len(metrics):
        raise RuntimeError('Zabbix rejected or did not acknowledge all metrics')
    return result
