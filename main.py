#!/usr/bin/env python3
"""Command-line entry point for the Quanterra Zabbix collector."""
import argparse
import os
import signal
import threading
import time
from collector.config import Settings
from collector.runtime import healthy, run_cycle, setup_logging, write_health


def main() -> int:
    """Run the collector once, continuously, or as a health check.

    Returns:
        Process exit code suitable for command-line and container execution.
    """
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
            cycle_started = time.monotonic()
            success = run_cycle(settings)

            if not args.daemon:
                return 0 if success else 1

            elapsed = time.monotonic() - cycle_started
            remaining = max(0.0, settings.interval - elapsed)

            if remaining:
                stop.wait(remaining)
    finally:
        if args.daemon:
            write_health(settings.health_file, False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
