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
    """Add per-site and total media occupied percentages.

    A Q330/PB44 reports capacity=0 and free=0 for an absent media site.
    Such a site is excluded from the total storage calculation.

    Total occupation is capacity-weighted so media sites with different
    capacities are represented correctly.
    """
    total_capacity = 0.0
    total_used = 0.0

    for site in (1, 2):
        capacity_key = f'media.site{site}.capacity'
        free_key = f'media.site{site}.free.space'
        occupied_key = f'media.site{site}.space.occupied'

        try:
            capacity = float(values[capacity_key])
            free = float(values[free_key])
        except (KeyError, TypeError, ValueError):
            values.pop(occupied_key, None)
            continue

        if capacity <= 0:
            values.pop(occupied_key, None)
            continue

        if not 0 <= free <= 100:
            values.pop(occupied_key, None)
            continue

        occupied = round(100.0 - free, 3)
        values[occupied_key] = occupied

        total_capacity += capacity
        total_used += capacity * occupied / 100.0

    total_key = 'media.total.space.occupied'

    if total_capacity > 0:
        values[total_key] = round(
            total_used / total_capacity * 100.0,
            3,
        )
    else:
        values.pop(total_key, None)


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

            # Advanced timing / GPS health.
            'clock.phase',
            'gps.antenna.current',
            'gps.sat.in.view',
            'gps.checksum.errors',
            'gps.pll.state',
            'gps.vco.control',

            # Sensor boom positions.
            'boom.ch1',
            'boom.ch2',
            'boom.ch3',
            'boom.ch4',
            'boom.ch5',
            'boom.ch6',

            # PB44 power / environment.
            'pb44.ups.voltage',
            'pb44.primary.voltage',
            'pb44.temperature',

            # Data quality.
            'data.gaps.minute',
            'data.gaps.hour',
            'data.gaps.day',
            'data.received.bps.minute',
            'data.received.bps.hour',
            'data.received.bps.day',
            'data.throughput.minute',
            'data.throughput.hour',
            'data.throughput.day',
            'data.sequence.errors.minute',
            'data.sequence.errors.hour',
            'data.sequence.errors.day',

            # Transport / performance.
            'data.latency',
            'status.latency',
            'packet.buffer.used',
            'packets.resent',
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
