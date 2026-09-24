import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time
from api.api_zbx_processing import discover_devices, iter_collected_devices
from collector.q330 import KEYS
from zabbix.zabbix_sender import send_data_to_zabbix

logger = logging.getLogger(__name__)
STARTED = time.monotonic()


def setup_logging(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s',
                        handlers=[logging.StreamHandler(), RotatingFileHandler(
                            path, maxBytes=5_000_000, backupCount=5, encoding='utf-8')], force=True)


def write_health(path, ok):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps({'ok': ok, 'completed_at': time.time()}))
    temporary.replace(target)


def healthy(path, max_age):
    try:
        data = json.loads(Path(path).read_text())
        age = time.time() - float(data['completed_at'])
        return data['ok'] is True and 0 <= age <= max_age
    except (OSError, ValueError, TypeError, KeyError):
        return False


def add_media_occupied(values):
    """Add media occupied percentage only for physically present media.

    A Q330/PB44 reports capacity=0 and free=0 for an absent media site.
    Such a site must not be represented as 100% occupied.
    """
    for site in (1, 2):
        capacity_key = f'media.site{site}.capacity'
        free_key = f'media.site{site}.free.space'
        occupied_key = f'media.site{site}.space.occupied'

        try:
            capacity = float(values[capacity_key])
            free = float(values[free_key])
        except (KeyError, TypeError, ValueError):
            continue

        if capacity <= 0:
            values.pop(occupied_key, None)
            continue

        if not 0 <= free <= 100:
            values.pop(occupied_key, None)
            continue

        values[occupied_key] = round(100.0 - free, 3)


def run_cycle(settings):
    started = time.monotonic()
    ok = False
    try:
        devices = discover_devices(settings)
        failed = 0

        media_keys = {
            'media.site1.free.space',
            'media.site2.free.space',
        }
        optional_keys = media_keys | {
            'media.site1.capacity',
            'media.site2.capacity',
        }
        required_keys = set(KEYS.values()) - optional_keys

        for device, values in iter_collected_devices(devices, settings):
            collected_metrics = len(values)
            add_media_occupied(values)

            has_required = required_keys.issubset(values)
            has_media = any(key in values for key in media_keys)

            complete = has_required and has_media

            failed += not complete
            values['q330.collect.success'] = int(complete)
            values['q330.collect.metrics'] = collected_metrics

            try:
                send_data_to_zabbix(
                    settings.server,
                    settings.port,
                    {device.host: values},
                    settings.timeout,
                )
            except Exception as exc:
                logger.error(
                    'Zabbix send failed host=%s error=%s',
                    device.host,
                    type(exc).__name__,
                )
                failed += complete
        metrics = {
            'collector.heartbeat': int(time.time()),
            'collector.uptime': round(time.monotonic() - STARTED, 3),
            'collector.cycle.duration': round(time.monotonic() - started, 3),
            'collector.devices.total': len(devices),
            'collector.devices.failed': failed,
            'collector.cycle.success': int(failed == 0),
        }
        send_data_to_zabbix(settings.server, settings.port, {settings.collector_host: metrics}, settings.timeout)
        # A device outage is reported to Zabbix; the collector itself is still operational.
        ok = True
        logger.info('Cycle complete devices=%d incomplete=%d', len(devices), failed)
        return failed == 0
    except Exception as exc:
        # Do not log API exception bodies: they may contain credentials or response data.
        logger.error('Collector cycle failed error=%s', type(exc).__name__)
        return False
    finally:
        write_health(settings.health_file, ok)
