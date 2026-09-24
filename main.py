#!/usr/bin/env python3
import argparse
import os
import signal
import threading
from collector.config import Settings
from collector.runtime import healthy, run_cycle, setup_logging, write_health


def main():
    parser = argparse.ArgumentParser(description='Q330 collector for Zabbix 7')
    parser.add_argument('--daemon', action='store_true', help='Repeat collection until SIGTERM/SIGINT')
    parser.add_argument('--healthcheck', action='store_true', help='Exit 0 only for a recent successful pipeline')
    args = parser.parse_args()
    if args.healthcheck:
        return 0 if healthy(os.getenv('COLLECTOR_HEALTH_FILE', '/tmp/quanterra-health.json'),
                            int(os.getenv('COLLECTOR_HEALTH_MAX_AGE', '300'))) else 1
    try:
        settings = Settings.from_env()
        setup_logging(settings.log_file)
    except (ValueError, OSError) as exc:
        print(f'Configuration error ({type(exc).__name__}); check environment and secret file.')
        return 2
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    write_health(settings.health_file, False)
    try:
        while not stop.is_set():
            success = run_cycle(settings)
            if not args.daemon:
                return 0 if success else 1
            stop.wait(settings.interval)
    finally:
        if args.daemon:
            write_health(settings.health_file, False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
