from conductr_cli.test.cli_test_case import CliTestCase, strip_margin
from conductr_cli import sandbox_run, logging_setup
from conductr_cli.sandbox_common import CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION


try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestSandboxRunCommand(CliTestCase):

    default_args = {
        'image_version': LATEST_CONDUCTR_VERSION,
        'conductr_roles': [],
        'envs': [],
        'image': CONDUCTR_DEV_IMAGE,
        'log_level': 'info',
        'nr_of_containers': 1,
        'ports': [],
        'features': [],
        'local_connection': True
    }

    def default_general_args(self, container_name):
        return ['-d', '--name', container_name]

    default_env_args = ['-e', 'AKKA_LOGLEVEL=info']
    default_port_args = ['-p', '9200:9200',
                         '-p', '5601:5601',
                         '-p', '9004:9004',
                         '-p', '9005:9005',
                         '-p', '9006:9006',
                         '-p', '9999:9999']
    default_positional_args = ['--discover-host-ip']

    def test_default_args(self):
        stdout = MagicMock()

        with \
                patch('conductr_cli.terminal.docker_images', return_value=''), \
                patch('conductr_cli.terminal.docker_pull', return_value=''), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]), \
                patch('conductr_cli.sandbox_common.resolve_host_ip', return_value='192.168.99.100'):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_run.run(MagicMock(**self.default_args))

        expected_stdout = strip_margin("""|Pulling down the ConductR development image..
                                          |Starting ConductR nodes..
                                          |Starting container cond-0..
                                          |""")
        expected_optional_args = self.default_general_args('cond-0') + self.default_env_args + self.default_port_args
        expected_image = '{}:{}'.format(CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION)
        expected_positional_args = self.default_positional_args

        self.assertEqual(expected_stdout, self.output(stdout))
        mock_docker_run.assert_called_once_with(expected_optional_args, expected_image, expected_positional_args)

    def test_multiple_container(self):
        stdout = MagicMock()
        nr_of_containers = 3

        with \
                patch('conductr_cli.terminal.docker_images', return_value='some-image'), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]), \
                patch('conductr_cli.sandbox_common.resolve_host_ip', return_value='192.168.99.100'):
            args = self.default_args.copy()
            args.update({'nr_of_containers': nr_of_containers})
            logging_setup.configure_logging(MagicMock(**args), stdout)
            sandbox_run.run(MagicMock(**args))

        expected_stdout = strip_margin("""|Starting ConductR nodes..
                                          |Starting container cond-0..
                                          |Starting container cond-1..
                                          |Starting container cond-2..
                                          |""")
        expected_image = '{}:{}'.format(CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION)

        self.assertEqual(expected_stdout, self.output(stdout))
        # Assert cond-0
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-0', '-e', 'AKKA_LOGLEVEL=info',
             '-p', '9200:9200', '-p', '5601:5601', '-p', '9004:9004', '-p', '9005:9005', '-p', '9006:9006',
             '-p', '9999:9999'],
            expected_image,
            self.default_positional_args
        )
        # Assert cond-1
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-1', '-e', 'AKKA_LOGLEVEL=info', '-e', 'SYSLOG_IP=10.10.10.10',
             '-p', '9210:9200', '-p', '5611:5601', '-p', '9014:9004', '-p', '9015:9005', '-p', '9016:9006',
             '-p', '9909:9999'],
            expected_image,
            self.default_positional_args + ['--seed', '10.10.10.10:9004']
        )
        # Assert cond-2
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-2', '-e', 'AKKA_LOGLEVEL=info', '-e', 'SYSLOG_IP=10.10.10.10',
             '-p', '9220:9200', '-p', '5621:5601', '-p', '9024:9004', '-p', '9025:9005', '-p', '9026:9006',
             '-p', '9919:9999'],
            expected_image,
            self.default_positional_args + ['--seed', '10.10.10.10:9004']
        )

    def test_with_custom_args(self):
        stdout = MagicMock()
        image_version = '1.1.0'
        conductr_roles = [['role1', 'role2']]
        envs = ['key1=value1', 'key2=value2']
        image = 'my-image'
        log_level = 'debug'
        nr_of_containers = 1
        ports = [3000, 3001]
        features = ['visualization', 'logging']

        with \
                patch('conductr_cli.terminal.docker_images', return_value='some-image'), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]), \
                patch('conductr_cli.sandbox_common.resolve_host_ip', return_value='192.168.99.100'):
            args = self.default_args.copy()
            args.update({
                'image_version': image_version,
                'conductr_roles': conductr_roles,
                'envs': envs,
                'image': image,
                'log_level': log_level,
                'nr_of_containers': nr_of_containers,
                'ports': ports,
                'features': features
            })
            logging_setup.configure_logging(MagicMock(**args), stdout)
            sandbox_run.run(MagicMock(**args))

        expected_stdout = strip_margin("""|Starting ConductR nodes..
                                          |Starting container cond-0 exposing 192.168.99.100:3000, 192.168.99.100:3001, 192.168.99.100:5601, 192.168.99.100:9200, 192.168.99.100:9999..
                                          |""")

        self.assertEqual(expected_stdout, self.output(stdout))
        mock_docker_run.assert_called_once_with(
            ['-d', '--name', 'cond-0', '-e', 'key1=value1', '-e', 'key2=value2', '-e', 'AKKA_LOGLEVEL=debug',
             '-e', 'CONDUCTR_FEATURES=visualization,logging', '-e', 'CONDUCTR_ROLES=role1,role2',
             '-p', '5601:5601', '-p', '9004:9004', '-p', '9005:9005', '-p', '9006:9006', '-p', '9999:9999',
             '-p', '9200:9200', '-p', '3000:3000', '-p', '3001:3001'],
            '{}:{}'.format(image, image_version),
            self.default_positional_args
        )

    def test_roles(self):
        stdout = MagicMock()
        nr_of_containers = 3
        conductr_roles = [['role1', 'role2'], ['role3']]

        with \
                patch('conductr_cli.terminal.docker_images', return_value='some-image'), \
                patch('conductr_cli.terminal.docker_ps', return_value=''), \
                patch('conductr_cli.terminal.docker_inspect', return_value='10.10.10.10'), \
                patch('conductr_cli.terminal.docker_run', return_value='') as mock_docker_run, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers', return_value=[]), \
                patch('conductr_cli.sandbox_common.resolve_host_ip', return_value='192.168.99.100'):
            args = self.default_args.copy()
            args.update({
                'nr_of_containers': nr_of_containers,
                'conductr_roles': conductr_roles
            })
            logging_setup.configure_logging(MagicMock(**args), stdout)
            sandbox_run.run(MagicMock(**args))

        expected_stdout = strip_margin("""|Starting ConductR nodes..
                                          |Starting container cond-0..
                                          |Starting container cond-1..
                                          |Starting container cond-2..
                                          |""")
        expected_image = '{}:{}'.format(CONDUCTR_DEV_IMAGE, LATEST_CONDUCTR_VERSION)

        self.assertEqual(expected_stdout, self.output(stdout))
        # Assert cond-0
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-0', '-e', 'AKKA_LOGLEVEL=info', '-e', 'CONDUCTR_ROLES=role1,role2',
             '-p', '9200:9200', '-p', '5601:5601', '-p', '9004:9004', '-p', '9005:9005', '-p', '9006:9006',
             '-p', '9999:9999'],
            expected_image,
            self.default_positional_args
        )
        # Assert cond-1
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-1', '-e', 'AKKA_LOGLEVEL=info', '-e', 'SYSLOG_IP=10.10.10.10',
             '-e', 'CONDUCTR_ROLES=role3',
             '-p', '9210:9200', '-p', '5611:5601', '-p', '9014:9004', '-p', '9015:9005', '-p', '9016:9006',
             '-p', '9909:9999'],
            expected_image,
            self.default_positional_args + ['--seed', '10.10.10.10:9004']
        )
        # Assert cond-2
        mock_docker_run.assert_any_call(
            ['-d', '--name', 'cond-2', '-e', 'AKKA_LOGLEVEL=info', '-e', 'SYSLOG_IP=10.10.10.10',
             '-e', 'CONDUCTR_ROLES=role1,role2',
             '-p', '9220:9200', '-p', '5621:5601', '-p', '9024:9004', '-p', '9025:9005', '-p', '9026:9006',
             '-p', '9919:9999'],
            expected_image,
            self.default_positional_args + ['--seed', '10.10.10.10:9004']
        )

    def test_containers_already_running(self):
        stdout = MagicMock()

        with \
                patch('conductr_cli.terminal.docker_images', return_value='some-image'), \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers',
                      return_value=['cond-0']):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_run.run(MagicMock(**self.default_args))

        expected_stdout = strip_margin("""|ConductR nodes {} already exists, leaving them alone.
                                          |""".format('cond-0'))

        self.assertEqual(expected_stdout, self.output(stdout))

    def test_scaling_down(self):
        stdout = MagicMock()

        with \
                patch('conductr_cli.terminal.docker_images', return_value='some-image'), \
                patch('conductr_cli.terminal.docker_rm', return_value='') as mock_docker_rm, \
                patch('conductr_cli.sandbox_common.resolve_running_docker_containers',
                      return_value=['cond-0', 'cond-1', 'cond-2']):
            logging_setup.configure_logging(MagicMock(**self.default_args), stdout)
            sandbox_run.run(MagicMock(**self.default_args))

        expected_stdout = strip_margin("""|Stopping ConductR nodes..
                                          |""".format('cond-0'))

        self.assertEqual(expected_stdout, self.output(stdout))
        mock_docker_rm.assert_called_once_with(['cond-1', 'cond-2'])
