"""Read-only discovery and bounded HTTP collection."""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import requests
from zabbix_utils import ZabbixAPI
from collector.q330 import parse_stats

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Device:
    host: str
    address: str
    family: str = 'q330'


def discover_devices(settings):
    api = ZabbixAPI(url=settings.url, token=settings.token, timeout=settings.timeout)
    templates = api.template.get(output=['templateid'], filter={'host': settings.template})
    if len(templates) != 1:
        raise ValueError('Expected one visible device template')
    hosts = api.host.get(
        output=['host'], templateids=[templates[0]['templateid']], filter={'status': '0'},
        selectInterfaces=['ip', 'dns', 'useip', 'main', 'type'],
    )
    devices = []
    for host in hosts:
        interfaces = sorted(host['interfaces'], key=lambda i: (i['main'] != '1', i['type'] != '1'))
        address = ''
        if interfaces:
            interface = interfaces[0]
            address = interface['ip'] if interface['useip'] == '1' else interface['dns']
        devices.append(Device(host['host'], address))
    if not devices:
        raise ValueError('No monitored devices visible for the configured template')

    if settings.host_filter:
        allowed = {
            host.strip()
            for host in settings.host_filter.split(',')
            if host.strip()
        }
        devices = [
            device for device in devices
            if device.host in allowed
        ]
        if not devices:
            raise ValueError('No monitored devices matched COLLECTOR_HOST_FILTER')

    if any(device.host == settings.collector_host for device in devices):
        raise ValueError('Collector host must not have the device template')

    return devices


def get_values(ip, arguments=None, timeout=20, port=6381):
    """Fetch and parse PB44/Q330 statistics with bounded retries."""
    if not ip or any(char in ip for char in '/?#@'):
        raise ValueError('Invalid device address')

    address = f'[{ip}]' if ':' in ip and not ip.startswith('[') else ip
    url = f'http://{address}:{port}/stats.html'

    attempts = 3
    last_error = None

    for attempt in range(1, attempts + 1):
        try:
            with requests.get(
                url,
                timeout=(10, timeout),
                allow_redirects=False,
                headers={'Connection': 'close'},
            ) as response:
                response.raise_for_status()

                if response.status_code != 200:
                    raise ValueError('Unexpected device HTTP status')

                try:
                    return parse_stats(response.text, arguments)
                except ValueError as exc:
                    if str(exc) != 'No recognized Q330 metrics':
                        raise
                    last_error = exc

                    if attempt < attempts:
                        logger.warning(
                            'Q330 parser retry address=%s attempt=%d/%d error=%s',
                            address,
                            attempt,
                            attempts,
                            type(exc).__name__,
                        )

        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = exc

            if attempt < attempts:
                logger.warning(
                    'Q330 HTTP retry address=%s attempt=%d/%d error=%s',
                    address,
                    attempt,
                    attempts,
                    type(exc).__name__,
                )

    raise last_error


# New device families implement the same adapter signature.
ADAPTERS = {'q330': get_values}


def collect_devices(devices, settings):
    results = {}
    with ThreadPoolExecutor(max_workers=settings.workers) as executor:
        futures = {executor.submit(ADAPTERS[d.family], d.address, timeout=settings.timeout,
                                   port=settings.device_port): d for d in devices}
        for future in as_completed(futures):
            device = futures[future]
            try:
                results[device.host] = future.result()
            except Exception as exc:
                logger.warning('Collection failed host=%s error=%s', device.host, type(exc).__name__)
                results[device.host] = {}
    return results
