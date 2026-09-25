import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from uuid import UUID
from unittest.mock import patch, Mock
import requests
import yaml
from api.api_zbx_processing import Device, collect_devices, discover_devices, get_values
from collector.config import Settings
from collector.q330 import KEYS, parse_stats
from collector.runtime import healthy, run_cycle, write_health
from zabbix.zabbix_sender import send_data_to_zabbix

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'tests/fixtures/stats.html').read_text()


class ParserTests(unittest.TestCase):
    def test_legacy_values(self):
        self.assertEqual(parse_stats(HTML), {
            'station.code': 'TEST', 'serial.number': '001234', 'q330.serial': '010000AABBCC',
            'input.voltage': '13.4', 'system.temp': '25', 'main.current': '125',
            'clock.quality': '100', 'sat.used': '8',
            'media.site1.free.space': '74.5', 'media.site2.free.space': '100.0',
            'media.site1.capacity': '1024.0', 'media.site2.capacity': '1024.0'})

    def test_format_variants(self):
        html = HTML.replace('25C', '-2.5 °C').replace('13.4V', '13 V').replace('74.5%', '74%')
        html = html.replace('Input Voltage:', '<b>Input Voltage:</b>&nbsp;')
        html = html.replace('Station EC-TEST', 'Station XX-TEST-2')
        values = parse_stats(html)
        self.assertEqual(values['system.temp'], '-2.5')
        self.assertEqual(values['station.code'], 'TEST-2')
        self.assertEqual(values['input.voltage'], '13')
        self.assertEqual(values['media.site1.free.space'], '74')

    def test_partial_and_invalid(self):
        values = parse_stats('Input Voltage: 12V Clock Quality: 101%')
        self.assertEqual(values, {'input.voltage': '12'})
        with self.assertRaises(ValueError):
            parse_stats('<html>Login required</html>')

    def test_legacy_mediafree_format(self):
        html = '''
        PB44 Status PacketBaler44 Tag 6011 - Station EC-CSOL
        MEDIA GOOD
        MEDIA site 1 IN USE state: ACTIVE
        media capacity=61042.500Mb  mediafree=62.943%
        '''

        values = parse_stats(html)

        self.assertEqual(
            values['media.site1.free.space'],
            '62.943'
        )
        self.assertEqual(
            values['media.site1.capacity'],
            '61042.500'
        )
        self.assertNotIn(
            'media.site2.free.space',
            values
        )

    def test_media_capacity_does_not_cross_sites(self):
        values = parse_stats(
            'MEDIA site 1 capacity=61042.500Mb free=34.040%\n'
            'MEDIA site 2 capacity=0.000Mb free=0.000%'
        )

        self.assertEqual(values['media.site1.capacity'], '61042.500')
        self.assertEqual(values['media.site1.free.space'], '34.040')
        self.assertEqual(values['media.site2.capacity'], '0.000')
        self.assertEqual(values['media.site2.free.space'], '0.000')

    def test_media_does_not_cross_sites(self):
        values = parse_stats('MEDIA site 1 missing\nMEDIA site 2 free=40%')
        self.assertNotIn('media.site1.free.space', values)
        self.assertEqual(values['media.site2.free.space'], '40')

    def test_empty_serial_does_not_capture_next_field(self):
        for separator in ('\n', '\r\n', '<br>', '<br/>', '</div><div>'):
            with self.subTest(separator=separator):
                values = parse_stats('Q330 Serial Number: \t' + separator + 'Input Voltage: 13.4V')
                self.assertNotIn('q330.serial', values)
                self.assertEqual(values['input.voltage'], '13.4')

    def test_serial_accepts_inline_html_and_horizontal_spacing(self):
        values = parse_stats('<b>Q330 Serial Number:</b>&nbsp;\t010000AABBCC<br>Input Voltage: 13.4V')
        self.assertEqual(values['q330.serial'], '010000AABBCC')


    def test_advanced_health_metrics(self):
        html = """
        Clock Phase: -2 usec
        Antenna Current: 18 ma
        In View: 11
        Checksum Errors: 0

        PLL Status
        State: Lock
        Vco Control: 2199

        Boom positions: Ch1: -48 Ch2: 1 Ch3: 1 Ch4: 20 Ch5: 20 Ch6: 20

        upsvolts=11.315
        primaryvolts=11.427
        degc=33.727

        Data Gaps minute=1 Hour=2 Day=3
        Received Bps minute=974 Hour=1024.5 Day=1100
        Throughput minute=1.00 Hour=0.95 Day=0.85
        Sequence Errors minute=4 Hour=5 Day=6

        Data Latency: 1m43s
        Status Latency: 8s
        Packet Buffer Used: 396
        Packets Re-Sent: 189
        """

        values = parse_stats(html)

        expected = {
            'clock.phase': '-2',
            'gps.antenna.current': '18',
            'gps.sat.in.view': '11',
            'gps.checksum.errors': '0',
            'gps.pll.state': 'Lock',
            'gps.vco.control': '2199',

            'boom.ch1': '-48',
            'boom.ch2': '1',
            'boom.ch3': '1',
            'boom.ch4': '20',
            'boom.ch5': '20',
            'boom.ch6': '20',

            'pb44.ups.voltage': '11.315',
            'pb44.primary.voltage': '11.427',
            'pb44.temperature': '33.727',

            'data.gaps.minute': '1',
            'data.gaps.hour': '2',
            'data.gaps.day': '3',

            'data.received.bps.minute': '974',
            'data.received.bps.hour': '1024.5',
            'data.received.bps.day': '1100',

            'data.throughput.minute': '1.00',
            'data.throughput.hour': '0.95',
            'data.throughput.day': '0.85',

            'data.sequence.errors.minute': '4',
            'data.sequence.errors.hour': '5',
            'data.sequence.errors.day': '6',

            'data.latency': 103,
            'status.latency': 8,
            'packet.buffer.used': '396',
            'packets.resent': '189',
        }

        self.assertEqual(values, expected)
        self.assertEqual(len(values), 31)

    def test_advanced_health_metrics_are_optional(self):
        html = """
        Clock Phase: 0 us
        Antenna Current: 17 ma
        In View: 11
        Checksum Errors: 0

        PLL Status
        State: Lock
        Vco Control: 2142

        Boom positions: Ch1: 1 Ch2: 2 Ch3: 3 Ch4: 4 Ch5: 5 Ch6: 6

        upsvolts=11.345
        primaryvolts=11.726
        degc=35.914

        Packet Buffer Used: 0
        Packets Re-Sent: 0
        """

        values = parse_stats(html)

        # Simula un equipo que no publica las ventanas de calidad/latencia.
        for key in (
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
            'data.latency',
            'status.latency',
        ):
            self.assertNotIn(key, values)

        self.assertEqual(values['gps.pll.state'], 'Lock')
        self.assertEqual(values['packet.buffer.used'], '0')
        self.assertEqual(values['packets.resent'], '0')

    def test_latency_duration_conversion(self):
        cases = (
            ('Data Latency: 8s', 8),
            ('Data Latency: 1m43s', 103),
            ('Data Latency: 2h3m4s', 7384),
            ('Data Latency: 1d2h3m4s', 93784),
        )

        for html, expected in cases:
            with self.subTest(html=html):
                values = parse_stats(html)
                self.assertEqual(values['data.latency'], expected)

    def test_boom_channels_do_not_cross_other_lines(self):
        html = """
        Ch1: 999 Ch2: 999 Ch3: 999
        Boom positions: Ch1: -20 Ch2: -18 Ch3: -31 Ch4: 20 Ch5: 20 Ch6: 20
        Ch4: 999 Ch5: 999 Ch6: 999
        """

        values = parse_stats(html)

        self.assertEqual(values['boom.ch1'], '-20')
        self.assertEqual(values['boom.ch2'], '-18')
        self.assertEqual(values['boom.ch3'], '-31')
        self.assertEqual(values['boom.ch4'], '20')
        self.assertEqual(values['boom.ch5'], '20')
        self.assertEqual(values['boom.ch6'], '20')


class MediaOccupiedTests(unittest.TestCase):
    """Tests for media occupied percentage derived by the collector."""

    def test_present_media_calculates_occupied(self):
        from collector.runtime import add_media_occupied

        values = {
            "media.site1.capacity": "61042.500",
            "media.site1.free.space": "34.040",
        }

        add_media_occupied(values)

        self.assertEqual(
            values["media.site1.space.occupied"],
            65.960,
        )

    def test_absent_media_does_not_generate_occupied(self):
        from collector.runtime import add_media_occupied

        values = {
            "media.site2.capacity": "0.000",
            "media.site2.free.space": "0.000",
        }

        add_media_occupied(values)

        self.assertNotIn(
            "media.site2.space.occupied",
            values,
        )

    def test_two_present_media_are_calculated(self):
        from collector.runtime import add_media_occupied

        values = {
            "media.site1.capacity": "15264.500",
            "media.site1.free.space": "25.952",
            "media.site2.capacity": "30520.000",
            "media.site2.free.space": "50.154",
        }

        add_media_occupied(values)

        self.assertEqual(
            values["media.site1.space.occupied"],
            74.048,
        )
        self.assertEqual(
            values["media.site2.space.occupied"],
            49.846,
        )

    def test_invalid_or_incomplete_media_does_not_generate_occupied(self):
        from collector.runtime import add_media_occupied

        values = {
            "media.site1.capacity": "invalid",
            "media.site1.free.space": "50",
            "media.site2.capacity": "15264.500",
        }

        add_media_occupied(values)

        self.assertNotIn(
            "media.site1.space.occupied",
            values,
        )
        self.assertNotIn(
            "media.site2.space.occupied",
            values,
        )


    def test_total_media_vces(self):
        """VCES: one media almost full, but total storage is below 50%."""
        from collector.runtime import add_media_occupied

        values = {
            "media.site1.capacity": "15264.500",
            "media.site1.free.space": "99.998",
            "media.site2.capacity": "15264.000",
            "media.site2.free.space": "5.012",
        }

        add_media_occupied(values)

        self.assertEqual(
            values["media.site1.space.occupied"],
            0.002,
        )
        self.assertEqual(
            values["media.site2.space.occupied"],
            94.988,
        )
        self.assertEqual(
            values["media.total.space.occupied"],
            47.494,
        )

    def test_total_media_boni_different_capacities(self):
        """BONI: total occupation must be weighted by actual capacity."""
        from collector.runtime import add_media_occupied

        values = {
            "media.site1.capacity": "15264.500",
            "media.site1.free.space": "25.952",
            "media.site2.capacity": "30520.000",
            "media.site2.free.space": "50.154",
        }

        add_media_occupied(values)

        self.assertEqual(
            values["media.site1.space.occupied"],
            74.048,
        )
        self.assertEqual(
            values["media.site2.space.occupied"],
            49.846,
        )
        self.assertEqual(
            values["media.total.space.occupied"],
            57.915,
        )

    def test_total_media_single_present_site(self):
        """CASC: an absent second media must not affect total occupation."""
        from collector.runtime import add_media_occupied

        values = {
            "media.site1.capacity": "15264.500",
            "media.site1.free.space": "99.553",
            "media.site2.capacity": "0.000",
            "media.site2.free.space": "0.000",
        }

        add_media_occupied(values)

        self.assertEqual(
            values["media.site1.space.occupied"],
            0.447,
        )
        self.assertNotIn(
            "media.site2.space.occupied",
            values,
        )
        self.assertEqual(
            values["media.total.space.occupied"],
            0.447,
        )

    def test_total_media_not_generated_without_valid_media(self):
        """No valid physical media means no synthetic total value."""
        from collector.runtime import add_media_occupied

        values = {
            "media.site1.capacity": "0.000",
            "media.site1.free.space": "0.000",
            "media.site2.capacity": "invalid",
            "media.site2.free.space": "50",
        }

        add_media_occupied(values)

        self.assertNotIn(
            "media.total.space.occupied",
            values,
        )


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.settings = Settings('https://example.test', 'SECRET', 'example.test',
                                 health_file=str(Path(self.temp.name) / 'health.json'))

    @patch('api.api_zbx_processing.ZabbixAPI')
    def test_discovery_token_dns_shared_ip_and_no_interfaces(self, api_class):
        api = api_class.return_value
        api.template.get.return_value = [{'templateid': '1'}]
        iface = dict(ip='192.0.2.1', dns='device.test', useip='0', main='1', type='1')
        api.host.get.return_value = [dict(host='A', interfaces=[iface]),
                                     dict(host='B', interfaces=[iface]), dict(host='C', interfaces=[])]
        devices = discover_devices(self.settings)
        self.assertEqual(devices, [Device('A', 'device.test'), Device('B', 'device.test'), Device('C', '')])
        api_class.assert_called_once_with(url=self.settings.url, token='SECRET', timeout=20)
        api.logout.assert_not_called()
        self.assertEqual(api.host.get.call_args.kwargs['filter'], {'status': '0'})

    @patch('api.api_zbx_processing.ZabbixAPI')
    def test_discovery_host_filter_single(self, api_class):
        api = api_class.return_value
        api.template.get.return_value = [{'templateid': '1'}]
        api.host.get.return_value = [
            dict(host='PUYO_QA', interfaces=[
                dict(ip='192.168.6.52', dns='', useip='1', main='1', type='1')
            ]),
            dict(host='MORR_QA', interfaces=[
                dict(ip='192.168.6.53', dns='', useip='1', main='1', type='1')
            ]),
        ]

        settings = Settings(
            'https://example.test',
            'SECRET',
            'example.test',
            host_filter='PUYO_QA',
            health_file=str(Path(self.temp.name) / 'health.json'),
        )

        devices = discover_devices(settings)

        self.assertEqual(
            devices,
            [Device('PUYO_QA', '192.168.6.52')]
        )

    @patch('api.api_zbx_processing.ZabbixAPI')
    def test_discovery_host_filter_multiple(self, api_class):
        api = api_class.return_value
        api.template.get.return_value = [{'templateid': '1'}]
        api.host.get.return_value = [
            dict(host='PUYO_QA', interfaces=[
                dict(ip='192.168.6.52', dns='', useip='1', main='1', type='1')
            ]),
            dict(host='MORR_QA', interfaces=[
                dict(ip='192.168.6.53', dns='', useip='1', main='1', type='1')
            ]),
            dict(host='ARDO_QA', interfaces=[
                dict(ip='192.168.6.51', dns='', useip='1', main='1', type='1')
            ]),
        ]

        settings = Settings(
            'https://example.test',
            'SECRET',
            'example.test',
            host_filter='PUYO_QA, MORR_QA',
            health_file=str(Path(self.temp.name) / 'health.json'),
        )

        devices = discover_devices(settings)

        self.assertEqual(
            devices,
            [
                Device('PUYO_QA', '192.168.6.52'),
                Device('MORR_QA', '192.168.6.53'),
            ]
        )

    @patch('api.api_zbx_processing.ZabbixAPI')
    def test_discovery_host_filter_no_match_is_error(self, api_class):
        api = api_class.return_value
        api.template.get.return_value = [{'templateid': '1'}]
        api.host.get.return_value = [
            dict(host='PUYO_QA', interfaces=[
                dict(ip='192.168.6.52', dns='', useip='1', main='1', type='1')
            ])
        ]

        settings = Settings(
            'https://example.test',
            'SECRET',
            'example.test',
            host_filter='NO_EXISTE_QA',
            health_file=str(Path(self.temp.name) / 'health.json'),
        )

        with self.assertRaisesRegex(
            ValueError,
            'No monitored devices matched COLLECTOR_HOST_FILTER'
        ):
            discover_devices(settings)

    @patch('api.api_zbx_processing.ZabbixAPI')
    def test_discovery_empty_is_error(self, api_class):
        api_class.return_value.template.get.return_value = []
        with self.assertRaises(ValueError):
            discover_devices(self.settings)

    @patch('api.api_zbx_processing.requests.get')
    def test_http_and_timeout(self, get):
        response = get.return_value.__enter__.return_value
        response.status_code = 200
        response.text = HTML
        self.assertEqual(len(get_values('2001:db8::1')), 12)
        self.assertEqual(get.call_args.args[0], 'http://[2001:db8::1]:6381/stats.html')
        get.side_effect = requests.Timeout
        result = collect_devices([Device('A', '192.0.2.1')], self.settings)
        self.assertEqual(result, {'A': {}})

    @patch('api.api_zbx_processing.requests.get')
    def test_http_retry_recovers_after_timeout(self, get):
        response = Mock()
        response.status_code = 200
        response.text = HTML
        response.raise_for_status.return_value = None

        context = Mock()
        context.__enter__ = Mock(return_value=response)
        context.__exit__ = Mock(return_value=False)

        get.side_effect = [
            requests.Timeout(),
            context,
        ]

        values = get_values('192.0.2.1')

        self.assertEqual(len(values), 12)
        self.assertEqual(values['station.code'], 'TEST')
        self.assertEqual(get.call_count, 2)

    @patch('api.api_zbx_processing.requests.get')
    def test_http_retry_recovers_after_unrecognized_page(self, get):
        bad_response = Mock()
        bad_response.status_code = 200
        bad_response.text = '<html><body>Temporary PB44 page</body></html>'
        bad_response.raise_for_status.return_value = None

        bad_context = Mock()
        bad_context.__enter__ = Mock(return_value=bad_response)
        bad_context.__exit__ = Mock(return_value=False)

        good_response = Mock()
        good_response.status_code = 200
        good_response.text = HTML
        good_response.raise_for_status.return_value = None

        good_context = Mock()
        good_context.__enter__ = Mock(return_value=good_response)
        good_context.__exit__ = Mock(return_value=False)

        get.side_effect = [
            bad_context,
            good_context,
        ]

        values = get_values('192.0.2.1')

        self.assertEqual(len(values), 12)
        self.assertEqual(values['station.code'], 'TEST')
        self.assertEqual(get.call_count, 2)

    @patch('api.api_zbx_processing.requests.get')
    def test_http_errors_propagate(self, get):
        response = get.return_value.__enter__.return_value
        response.raise_for_status.side_effect = requests.HTTPError
        with self.assertRaises(requests.HTTPError):
            get_values('192.0.2.1')

    @patch('zabbix.zabbix_sender.Sender')
    def test_sender_rejects_partial_ack(self, sender):
        sender.return_value.send.return_value = Mock(processed=0, failed=1, total=1)
        with self.assertRaises(RuntimeError):
            send_data_to_zabbix('server', 10051, {'A': {'input.voltage': '12'}})
        sender.return_value.send.return_value = Mock(processed=1, failed=0, total=1)
        send_data_to_zabbix('server', 10051, {'A': {'input.voltage': '12'}})
        item = sender.return_value.send.call_args.args[0][0]
        self.assertEqual(item.to_json()['key'], 'input.voltage')

    @patch('collector.runtime.send_data_to_zabbix')
    @patch('collector.runtime.iter_collected_devices')
    @patch('collector.runtime.discover_devices')
    def test_cycle_device_failure_is_reported(self, discover, collect, send):
        discover.return_value = [Device('A', '192.0.2.1'), Device('B', '')]
        collect.return_value = iter([(Device('A', '192.0.2.1'), parse_stats(HTML)), (Device('B', ''), {})])
        self.assertFalse(run_cycle(self.settings))
        self.assertTrue(healthy(self.settings.health_file, 60))
        data_a = send.call_args_list[0].args[2]
        data_b = send.call_args_list[1].args[2]
        collector_data = send.call_args_list[2].args[2][self.settings.collector_host]

        self.assertEqual(data_a['A']['q330.collect.metrics'], 12)
        self.assertEqual(data_a['A']['q330.collect.success'], 1)

        self.assertEqual(data_b['B']['q330.collect.metrics'], 0)
        self.assertEqual(data_b['B']['q330.collect.success'], 0)

        self.assertEqual(collector_data['collector.devices.failed'], 1)
        self.assertEqual(collector_data['collector.devices.total'], 2)
        self.assertEqual(collector_data['collector.cycle.success'], 0)

    @patch('collector.runtime.send_data_to_zabbix', side_effect=RuntimeError)
    @patch('collector.runtime.iter_collected_devices', return_value=iter([(Device('A', '192.0.2.1'), parse_stats(HTML))]))
    @patch('collector.runtime.discover_devices', return_value=[Device('A', '192.0.2.1')])
    def test_sender_failure_marks_unhealthy(self, *_):
        self.assertFalse(run_cycle(self.settings))
        self.assertFalse(healthy(self.settings.health_file, 60))

    @patch('collector.runtime.send_data_to_zabbix')
    @patch('collector.runtime.iter_collected_devices')
    @patch('collector.runtime.discover_devices', return_value=[Device('A', '192.0.2.1')])
    def test_empty_serial_makes_cycle_incomplete(self, discover, collect, send):
        collect.return_value = iter([(Device('A', '192.0.2.1'), parse_stats(HTML.replace('010000AABBCC', '')))])
        self.assertFalse(run_cycle(self.settings))
        values = send.call_args_list[0].args[2]['A']
        self.assertNotIn('q330.serial', values)
        self.assertEqual(values['q330.collect.metrics'], 11)
        self.assertEqual(values['q330.collect.success'], 0)

    @patch('collector.runtime.send_data_to_zabbix')
    @patch('collector.runtime.iter_collected_devices')
    @patch('collector.runtime.discover_devices', return_value=[Device('A', '192.0.2.1')])
    def test_overheat_remains_monitorable_with_single_media(self, discover, collect, send):
        html = '\n'.join(
            line for line in HTML.splitlines()
            if 'MEDIA site 2' not in line
        )

        collect.return_value = iter([
            (Device('A', '192.0.2.1'), parse_stats(html.replace('25C', '80C')))
        ])

        self.assertTrue(run_cycle(self.settings))

        values = send.call_args_list[0].args[2]['A']

        self.assertEqual(values['system.temp'], '80')
        self.assertIn('media.site1.free.space', values)
        self.assertNotIn('media.site2.free.space', values)

        # Derived OCCUPIED metric must reach the Zabbix Sender payload.
        self.assertIn('media.site1.space.occupied', values)
        self.assertNotIn('media.site2.space.occupied', values)
        self.assertEqual(
            values['media.site1.space.occupied'],
            round(100.0 - float(values['media.site1.free.space']), 3),
        )

        # collect.metrics counts metrics collected from the Q330,
        # not locally derived metrics.
        self.assertEqual(values['q330.collect.metrics'], 10)
        self.assertEqual(values['q330.collect.success'], 1)

        template = yaml.safe_load(
            (ROOT / 'templates/quanterra_zabbix7.yaml').read_text()
        )['zabbix_export']['templates'][0]

        temperature = next(
            item for item in template['items']
            if item['key'] == 'system.temp'
        )

        expression = temperature['triggers'][0]['expression']

        self.assertNotIn(
            'q330.collect.success',
            expression
        )

        self.assertIn(
            'last(/Template Zabbix Trapper Quanterra/system.temp)>{$Q330.TEMP.MAX}',
            expression
        )

    @patch('collector.runtime.send_data_to_zabbix')
    @patch('collector.runtime.iter_collected_devices')
    @patch('collector.runtime.discover_devices', return_value=[Device('A', '192.0.2.1')])
    def test_single_media_site_is_complete(self, discover, collect, send):
        html = '\n'.join(
            line for line in HTML.splitlines()
            if 'MEDIA site 2' not in line
        )

        collect.return_value = iter([(Device('A', '192.0.2.1'), parse_stats(html))])

        self.assertTrue(run_cycle(self.settings))

        values = send.call_args_list[0].args[2]['A']

        self.assertIn('media.site1.free.space', values)
        self.assertNotIn('media.site2.free.space', values)
        self.assertEqual(values['q330.collect.metrics'], 10)
        self.assertEqual(values['q330.collect.success'], 1)


    @patch('collector.runtime.send_data_to_zabbix')
    @patch('collector.runtime.iter_collected_devices')
    @patch('collector.runtime.discover_devices', return_value=[Device('A', '192.0.2.1')])
    def test_two_media_sites_are_complete(self, discover, collect, send):
        collect.return_value = iter([
            (Device('A', '192.0.2.1'), parse_stats(HTML))
        ])

        self.assertTrue(run_cycle(self.settings))

        values = send.call_args_list[0].args[2]['A']

        self.assertIn('media.site1.free.space', values)
        self.assertIn('media.site2.free.space', values)

        # Both derived OCCUPIED metrics must reach the Sender payload.
        self.assertIn('media.site1.space.occupied', values)
        self.assertIn('media.site2.space.occupied', values)

        self.assertEqual(
            values['media.site1.space.occupied'],
            round(100.0 - float(values['media.site1.free.space']), 3),
        )
        self.assertEqual(
            values['media.site2.space.occupied'],
            round(100.0 - float(values['media.site2.free.space']), 3),
        )

        # collect.metrics counts source metrics only.
        self.assertEqual(values['q330.collect.metrics'], 12)
        self.assertEqual(values['q330.collect.success'], 1)


    @patch('collector.runtime.send_data_to_zabbix')
    @patch('collector.runtime.iter_collected_devices')
    @patch('collector.runtime.discover_devices', return_value=[Device('A', '192.0.2.1')])
    def test_no_media_site_is_incomplete(self, discover, collect, send):
        html = '\n'.join(
            line for line in HTML.splitlines()
            if 'MEDIA site 1' not in line
            and 'MEDIA site 2' not in line
        )

        collect.return_value = iter([(Device('A', '192.0.2.1'), parse_stats(html))])

        self.assertFalse(run_cycle(self.settings))

        values = send.call_args_list[0].args[2]['A']

        self.assertNotIn('media.site1.free.space', values)
        self.assertNotIn('media.site2.free.space', values)
        self.assertEqual(values['q330.collect.metrics'], 8)
        self.assertEqual(values['q330.collect.success'], 0)


    @patch('collector.runtime.send_data_to_zabbix')
    @patch('collector.runtime.iter_collected_devices')
    @patch('collector.runtime.discover_devices')
    def test_sender_failure_for_one_device_does_not_block_others(
            self, discover, collect, send):

        device_a = Device('A', '192.0.2.1')
        device_b = Device('B', '192.0.2.2')

        discover.return_value = [device_a, device_b]

        collect.return_value = iter([
            (device_a, parse_stats(HTML)),
            (device_b, parse_stats(HTML)),
        ])

        def sender_side_effect(server, port, data, timeout):
            if 'A' in data:
                raise RuntimeError('simulated sender failure')
            return Mock()

        send.side_effect = sender_side_effect

        self.assertFalse(run_cycle(self.settings))

        sent_hosts = [
            next(iter(call.args[2]))
            for call in send.call_args_list
        ]

        self.assertIn('A', sent_hosts)
        self.assertIn('B', sent_hosts)
        self.assertIn(self.settings.collector_host, sent_hosts)

        self.assertLess(
            sent_hosts.index('A'),
            sent_hosts.index('B'),
        )

        collector_data = send.call_args_list[-1].args[2][
            self.settings.collector_host
        ]

        self.assertEqual(
            collector_data['collector.devices.failed'],
            1,
        )

    def test_thresholds_use_only_their_own_recent_metric(self):
        template = yaml.safe_load(
            (ROOT / 'templates/quanterra_zabbix7.yaml').read_text()
        )['zabbix_export']['templates'][0]

        keys = {
            'input.voltage',
            'system.temp',
            'sat.used',
            'clock.quality',
        }

        for item in template['items']:
            if item['key'] not in keys:
                continue

            with self.subTest(key=item['key']):
                self.assertTrue(item.get('triggers'))

                for trigger in item['triggers']:
                    expression = trigger['expression']

                    self.assertNotIn(
                        'q330.collect.success',
                        expression,
                    )

                    self.assertIn(
                        f"nodata(/{template['template']}/{item['key']},"
                        "{$COLLECTOR.NODATA})=0",
                        expression,
                    )

    def test_media_occupied_triggers(self):
        template = yaml.safe_load(
            (ROOT / 'templates/quanterra_zabbix7.yaml').read_text()
        )['zabbix_export']['templates'][0]

        items = {
            item['key']: item
            for item in template['items']
        }

        # Per-site metrics remain available only as diagnostic telemetry.
        for site in (1, 2):
            for suffix in ('free.space', 'space.occupied'):
                key = f'media.site{site}.{suffix}'

                with self.subTest(key=key):
                    self.assertEqual(
                        items[key].get('triggers', []),
                        [],
                    )

        # Operational storage alarms are based only on the
        # capacity-weighted total occupation.
        key = 'media.total.space.occupied'

        self.assertIn(key, items)

        triggers = items[key].get('triggers', [])

        self.assertEqual(len(triggers), 2)

        warning = next(
            trigger for trigger in triggers
            if trigger['priority'] == 'WARNING'
        )

        high = next(
            trigger for trigger in triggers
            if trigger['priority'] == 'HIGH'
        )

        expected_warning = (
            f"last(/{template['template']}/{key})>=60 and "
            f"last(/{template['template']}/{key})<80"
        )

        expected_high = (
            f"last(/{template['template']}/{key})>=80"
        )

        self.assertEqual(
            warning['expression'],
            expected_warning,
        )

        self.assertEqual(
            high['expression'],
            expected_high,
        )

        for trigger in triggers:
            expression = trigger['expression']

            self.assertIn(key, expression)
            self.assertNotIn(
                'media.site1.space.occupied',
                expression,
            )
            self.assertNotIn(
                'media.site2.space.occupied',
                expression,
            )
            self.assertNotIn(
                'q330.collect.success',
                expression,
            )


    def test_health_missing_stale_corrupt_and_future(self):
        path = self.settings.health_file
        self.assertFalse(healthy(path, 60))
        write_health(path, True)
        self.assertTrue(healthy(path, 60))
        for timestamp in (time.time() - 100, time.time() + 100):
            Path(path).write_text(json.dumps({'ok': True, 'completed_at': timestamp}))
            self.assertFalse(healthy(path, 60))
        Path(path).write_text('bad')
        self.assertFalse(healthy(path, 60))

    def test_config_token_file_and_validation(self):
        token = Path(self.temp.name) / 'token'
        token.write_text('secret\n')
        env = {'ZABBIX_URL': 'https://example.test', 'ZABBIX_SERVER': 'server', 'ZABBIX_TOKEN_FILE': str(token)}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(Settings.from_env().token, 'secret')
            self.assertNotIn('secret', repr(Settings.from_env()))
            with patch.dict(os.environ, {'ZABBIX_TOKEN': 'conflict'}):
                with self.assertRaises(ValueError):
                    Settings.from_env()
            with patch.dict(os.environ, {'COLLECTOR_WORKERS': '0'}):
                with self.assertRaises(ValueError):
                    Settings.from_env()

    def test_templates_cover_metrics(self):
        export = yaml.safe_load((ROOT / 'templates/quanterra_zabbix7.yaml').read_text())['zabbix_export']
        self.assertEqual(export['version'], '7.0')
        def check_uuids(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key == 'uuid':
                        self.assertEqual(len(value), 32)
                        self.assertEqual(UUID(hex=value).version, 4)
                    else:
                        check_uuids(value)
            elif isinstance(node, list):
                for value in node:
                    check_uuids(value)
        check_uuids(export)
        device, collector = export['templates']
        expected_device_keys = set(KEYS.values()) | {
            'q330.collect.success',
            'q330.collect.metrics',
            'media.site1.space.occupied',
            'media.site2.space.occupied',
            'media.total.space.occupied',
        }
        self.assertEqual(
            {i['key'] for i in device['items']},
            expected_device_keys,
        )
        self.assertEqual(len(collector['items']), 6)
        ids = []
        for template in export['templates']:
            macros = {m['macro'] for m in template['macros']}
            for item in template['items']:
                ids.append(item['uuid'])
                self.assertEqual(item['type'], 'TRAP')
                self.assertIn(item['allowed_hosts'], macros)
                for trigger in item.get('triggers', []):
                    self.assertIn('/' + template['template'] + '/', trigger['expression'])
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == '__main__':
    unittest.main()
