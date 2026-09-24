import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Settings:
    url: str
    token: str = field(repr=False)
    server: str
    collector_host: str = 'Monitoring Data Collector'
    template: str = 'Quanterra Q330 by collector'
    host_filter: str = ''
    port: int = 10051
    device_port: int = 6381
    timeout: int = 20
    workers: int = 8
    interval: int = 60
    health_max_age: int = 300
    health_file: str = '/tmp/quanterra-health.json'
    log_file: str = 'logs/collector.log'

    @classmethod
    def from_env(cls):
        token = os.getenv('ZABBIX_TOKEN', '').strip()
        token_file = os.getenv('ZABBIX_TOKEN_FILE')
        if token_file:
            if token:
                raise ValueError('Set only ZABBIX_TOKEN or ZABBIX_TOKEN_FILE')
            token = Path(token_file).read_text().strip()
        required = {key: os.getenv(key, '').strip() for key in ('ZABBIX_URL', 'ZABBIX_SERVER')}
        if not token or not all(required.values()):
            raise ValueError('ZABBIX_URL, ZABBIX_SERVER and an API token are required')
        url = urlsplit(required['ZABBIX_URL'])
        if url.scheme not in {'http', 'https'} or not url.hostname or url.username or url.password:
            raise ValueError('ZABBIX_URL must be HTTP(S) without embedded credentials')
        kwargs = {}
        for name in ('port', 'device_port', 'timeout', 'workers', 'interval', 'health_max_age'):
            env = {'port': 'ZABBIX_PORT', 'device_port': 'Q330_PORT'}.get(name, 'COLLECTOR_' + name.upper())
            value = int(os.getenv(env, str(cls.__dataclass_fields__[name].default)))
            if value <= 0 or (name in {'port', 'device_port'} and value > 65535):
                raise ValueError(f'Invalid {env}')
            kwargs[name] = value
        for name in ('collector_host', 'template', 'health_file', 'log_file'):
            env = {'collector_host': 'COLLECTOR_HOST', 'template': 'ZABBIX_TEMPLATE'}.get(name, 'COLLECTOR_' + name.upper())
            kwargs[name] = os.getenv(env, str(cls.__dataclass_fields__[name].default)).strip()
            if not kwargs[name]:
                raise ValueError(f'Empty {env}')
        kwargs['host_filter'] = os.getenv('COLLECTOR_HOST_FILTER', '').strip()
        return cls(url=required['ZABBIX_URL'], token=token, server=required['ZABBIX_SERVER'], **kwargs)
