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
            'last(/Quanterra Q330 by collector/system.temp)>{$Q330.TEMP.MAX}',
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
        template = yaml.safe_load((ROOT / 'templates/quanterra_zabbix7.yaml').read_text())['zabbix_export']['templates'][0]
        keys = {'input.voltage', 'system.temp', 'sat.used', 'clock.quality',
                'media.site1.free.space', 'media.site2.free.space'}
        for item in template['items']:
            if item['key'] not in keys:
                continue
            with self.subTest(key=item['key']):
                expression = item['triggers'][0]['expression']
                self.assertNotIn('q330.collect.success', expression)
                self.assertIn(f"nodata(/{template['template']}/{item['key']},{{$COLLECTOR.NODATA}})=0", expression)

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
        self.assertEqual({i['key'] for i in device['items']}, set(KEYS.values()) | {'q330.collect.success', 'q330.collect.metrics'})
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
