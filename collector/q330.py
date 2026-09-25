"""Pure Q330 parser. Legacy Zabbix keys remain stable."""
import re
from html.parser import HTMLParser

KEYS = {
    'StationCode': 'station.code', 'SerialNumber': 'serial.number',
    'MediaSite1': 'media.site1.free.space', 'MediaSite2': 'media.site2.free.space',
    'MediaSite1Capacity': 'media.site1.capacity',
    'MediaSite2Capacity': 'media.site2.capacity',
    'Q330Serial': 'q330.serial', 'ClockQuality': 'clock.quality',
    'InputVoltage': 'input.voltage', 'SystemTemp': 'system.temp',
    'MainCurrent': 'main.current', 'SatUsed': 'sat.used',

    # Advanced timing / GPS health
    'ClockPhase': 'clock.phase',
    'AntennaCurrent': 'gps.antenna.current',
    'SatInView': 'gps.sat.in.view',
    'GPSChecksumErrors': 'gps.checksum.errors',
    'PLLState': 'gps.pll.state',
    'VcoControl': 'gps.vco.control',

    # Sensor boom positions
    'BoomCh1': 'boom.ch1',
    'BoomCh2': 'boom.ch2',
    'BoomCh3': 'boom.ch3',
    'BoomCh4': 'boom.ch4',
    'BoomCh5': 'boom.ch5',
    'BoomCh6': 'boom.ch6',

    # PB44 power / environment
    'PB44UPSVoltage': 'pb44.ups.voltage',
    'PB44PrimaryVoltage': 'pb44.primary.voltage',
    'PB44Temperature': 'pb44.temperature',

    # Data quality
    'DataGapsMinute': 'data.gaps.minute',
    'DataGapsHour': 'data.gaps.hour',
    'DataGapsDay': 'data.gaps.day',
    'ReceivedBpsMinute': 'data.received.bps.minute',
    'ReceivedBpsHour': 'data.received.bps.hour',
    'ReceivedBpsDay': 'data.received.bps.day',
    'ThroughputMinute': 'data.throughput.minute',
    'ThroughputHour': 'data.throughput.hour',
    'ThroughputDay': 'data.throughput.day',
    'SequenceErrorsMinute': 'data.sequence.errors.minute',
    'SequenceErrorsHour': 'data.sequence.errors.hour',
    'SequenceErrorsDay': 'data.sequence.errors.day',

    # Transport / performance
    'DataLatency': 'data.latency',
    'StatusLatency': 'status.latency',
    'PacketBufferUsed': 'packet.buffer.used',
    'PacketsResent': 'packets.resent',
}
NUMBER = r'([+-]?\d+(?:\.\d+)?)'
PATTERNS = {
    'StationCode': r'\bStation\s+[\w]+-([\w-]+)',
    'SerialNumber': r'\bTag\s+(\d+)\s*-\s*Station',
    # Horizontal whitespace only: an empty field must not consume the next line.
    'Q330Serial': r'Q330\s+Serial\s+Number[^\S\r\n]*:[^\S\r\n]*([^\s]+)',
    'ClockQuality': r'Clock\s+Quality\s*:\s*' + NUMBER + r'\s*%',
    'InputVoltage': r'Input\s+Voltage\s*:\s*' + NUMBER + r'\s*V\b',
    'SystemTemp': r'System\s+Temperature\s*:\s*' + NUMBER + r'\s*°?C\b',
    'MainCurrent': r'Main\s+Current\s*:\s*' + NUMBER + r'\s*ma\b',
    'SatUsed': r'Sat\.?\s+Used\s*:\s*(\d+)\b',

    # Advanced timing / GPS health
    'ClockPhase': r'Clock\s+Phase\s*:\s*' + NUMBER + r'\s*(?:usec|us|µs)\b',
    'AntennaCurrent': r'Antenna\s+Current\s*:\s*' + NUMBER + r'\s*ma\b',
    'SatInView': r'\bIn\s+View\s*:\s*(\d+)\b',
    'GPSChecksumErrors': r'\bChecksum\s+Errors\s*:\s*(\d+)\b',
    'PLLState': r'PLL\s+Status(?:(?!\n\s*\n).)*?\bState\s*:\s*([A-Za-z][A-Za-z0-9_-]*)',
    'VcoControl': r'\bVco\s+Control\s*:\s*' + NUMBER + r'\b',

    # PB44 power / environment
    'PB44UPSVoltage': r'\bupsvolts\s*=\s*' + NUMBER + r'\b',
    'PB44PrimaryVoltage': r'\bprimaryvolts\s*=\s*' + NUMBER + r'\b',
    'PB44Temperature': r'\bdegc\s*=\s*' + NUMBER + r'\b',

    # Data quality windows
    'DataGapsMinute': r'Data\s+Gaps\s+minute\s*=\s*(\d+)',
    'DataGapsHour': r'Data\s+Gaps\s+minute\s*=\s*\d+\s+Hour\s*=\s*(\d+)',
    'DataGapsDay': r'Data\s+Gaps\s+minute\s*=\s*\d+\s+Hour\s*=\s*\d+\s+Day\s*=\s*(\d+)',

    'ReceivedBpsMinute': r'Received\s+Bps\s+minute\s*=\s*' + NUMBER,
    'ReceivedBpsHour': r'Received\s+Bps\s+minute\s*=\s*[+-]?\d+(?:\.\d+)?\s+Hour\s*=\s*' + NUMBER,
    'ReceivedBpsDay': r'Received\s+Bps\s+minute\s*=\s*[+-]?\d+(?:\.\d+)?\s+Hour\s*=\s*[+-]?\d+(?:\.\d+)?\s+Day\s*=\s*' + NUMBER,

    'ThroughputMinute': r'Throughput\s+minute\s*=\s*' + NUMBER,
    'ThroughputHour': r'Throughput\s+minute\s*=\s*[+-]?\d+(?:\.\d+)?\s+Hour\s*=\s*' + NUMBER,
    'ThroughputDay': r'Throughput\s+minute\s*=\s*[+-]?\d+(?:\.\d+)?\s+Hour\s*=\s*[+-]?\d+(?:\.\d+)?\s+Day\s*=\s*' + NUMBER,

    'SequenceErrorsMinute': r'Sequence\s+Errors\s+minute\s*=\s*(\d+)',
    'SequenceErrorsHour': r'Sequence\s+Errors\s+minute\s*=\s*\d+\s+Hour\s*=\s*(\d+)',
    'SequenceErrorsDay': r'Sequence\s+Errors\s+minute\s*=\s*\d+\s+Hour\s*=\s*\d+\s+Day\s*=\s*(\d+)',

    # Transport / performance
    'PacketBufferUsed': r'Packet\s+Buffer\s+Used\s*:\s*(\d+)',
    'PacketsResent': r'Packets\s+Re-Sent\s*:\s*(\d+)',
}
for channel in range(1, 7):
    # Restrict matching to the Boom positions line so similarly named
    # channels elsewhere on stats.html cannot be captured accidentally.
    PATTERNS[f'BoomCh{channel}'] = (
        r'Boom\s+positions\s*:\s*'
        r'([^\r\n]*)'
    )


for site in (1, 2):
    site_prefix = (
        rf'MEDIA\s+site\s+{site}\b'
        rf'(?:(?!MEDIA\s+site).)*?'
    )

    PATTERNS[f'MediaSite{site}'] = (
        site_prefix
        + rf'\b(?:free|mediafree)\s*=\s*'
        + NUMBER
        + r'\s*%'
    )

    PATTERNS[f'MediaSite{site}Capacity'] = (
        site_prefix
        + rf'\b(?:capacity|media\s+capacity)\s*=\s*'
        + NUMBER
        + r'\s*(?:MB|Mb)\b'
    )


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def handle_starttag(self, tag, attrs):
        if tag in {'br', 'p', 'div', 'tr', 'td', 'pre'}:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in {'p', 'div', 'tr', 'td', 'pre'}:
            self.parts.append('\n')


def _parse_duration_seconds(value):
    """Convert Q330/PB44 duration strings such as 1m43s to seconds."""
    value = value.strip().lower()

    match = re.fullmatch(
        r'(?:(\d+)d)?'
        r'(?:(\d+)h)?'
        r'(?:(\d+)m)?'
        r'(?:(\d+)s)?',
        value,
    )

    if not match or not any(part is not None for part in match.groups()):
        raise ValueError(f'Invalid duration: {value!r}')

    days, hours, minutes, seconds = (
        int(part or 0) for part in match.groups()
    )

    return (
        days * 86400
        + hours * 3600
        + minutes * 60
        + seconds
    )


def parse_stats(html, arguments=None):
    parser = _Text()
    parser.feed(html)
    text = ''.join(parser.parts)
    values = {}

    selected = KEYS if arguments is None else arguments

    # Boom positions are parsed separately because all six channels share
    # one source line.
    boom_match = re.search(
        r'Boom\s+positions\s*:\s*([^\r\n]*)',
        text,
        re.I,
    )
    boom_values = {}
    if boom_match:
        boom_line = boom_match.group(1)
        for channel in range(1, 7):
            match = re.search(
                rf'\bCh{channel}\s*:\s*([+-]?\d+(?:\.\d+)?)',
                boom_line,
                re.I,
            )
            if match:
                boom_values[f'BoomCh{channel}'] = match.group(1)

    for arg in selected:
        if arg not in KEYS:
            raise ValueError(f'Unknown Q330 metric: {arg}')

        if arg.startswith('BoomCh'):
            value = boom_values.get(arg)
            if value is None:
                continue
            values[KEYS[arg]] = value
            continue

        if arg in {'DataLatency', 'StatusLatency'}:
            label = (
                'Data\\s+Latency'
                if arg == 'DataLatency'
                else 'Status\\s+Latency'
            )
            match = re.search(
                label + r'\s*:\s*((?:(?:\d+)d)?(?:(?:\d+)h)?'
                r'(?:(?:\d+)m)?(?:(?:\d+)s)?)\b',
                text,
                re.I,
            )
            if not match or not match.group(1):
                continue

            try:
                values[KEYS[arg]] = _parse_duration_seconds(
                    match.group(1)
                )
            except ValueError:
                continue
            continue

        match = re.search(PATTERNS[arg], text, re.I | re.S)
        if not match:
            continue

        value = match.group(1).strip()

        if (
            arg in {'ClockQuality', 'MediaSite1', 'MediaSite2'}
            and not 0 <= float(value) <= 100
        ):
            continue

        if (
            arg in {
                'MainCurrent',
                'InputVoltage',
                'AntennaCurrent',
                'PB44UPSVoltage',
                'PB44PrimaryVoltage',
            }
            and float(value) < 0
        ):
            continue

        values[KEYS[arg]] = value

    if not values:
        raise ValueError('No recognized Q330 metrics')

    return values
