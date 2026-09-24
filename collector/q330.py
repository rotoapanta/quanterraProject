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
}
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


def parse_stats(html, arguments=None):
    parser = _Text()
    parser.feed(html)
    text = ''.join(parser.parts)
    values = {}
    for arg in KEYS if arguments is None else arguments:
        if arg not in PATTERNS:
            raise ValueError(f'Unknown Q330 metric: {arg}')
        match = re.search(PATTERNS[arg], text, re.I | re.S)
        if not match:
            continue
        value = match.group(1).strip()
        if arg in {'ClockQuality', 'MediaSite1', 'MediaSite2'} and not 0 <= float(value) <= 100:
            continue
        if arg in {'MainCurrent', 'InputVoltage'} and float(value) < 0:
            continue
        values[KEYS[arg]] = value
    if not values:
        raise ValueError('No recognized Q330 metrics')
    return values
