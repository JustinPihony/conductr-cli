from unittest import TestCase
from urllib.error import URLError
from conductr_cli.resolvers import uri_resolver
import os

try:
    from unittest.mock import patch, MagicMock  # 3.3 and beyond
except ImportError:
    from mock import patch, MagicMock


class TestResolveBundle(TestCase):
    def test_resolve_success(self):
        os_path_exists_mock = MagicMock(return_value=True)
        cache_path_mock = MagicMock(return_value='/bundle-cached-path')
        get_url_mock = MagicMock(return_value=('bundle-name', '/bundle-url-resolved'))
        urlretrieve_mock = MagicMock(return_value=('mock-bundle-file', ()))

        with patch('os.path.exists', os_path_exists_mock), \
                patch('conductr_cli.resolvers.uri_resolver.cache_path', cache_path_mock), \
                patch('conductr_cli.resolvers.uri_resolver.get_url', get_url_mock), \
                patch('conductr_cli.resolvers.uri_resolver.urlretrieve', urlretrieve_mock):
            is_resolved, bundle_name, bundle_file = uri_resolver.resolve_bundle('/cache-dir', '/bundle-url')
            self.assertTrue(is_resolved)
            self.assertEqual('bundle-name', bundle_name)
            self.assertEqual('mock-bundle-file', bundle_file)

        os_path_exists_mock.assert_called_with('/cache-dir')
        cache_path_mock.assert_called_with('/cache-dir', '/bundle-url')
        get_url_mock.assert_called_with('/bundle-url')
        urlretrieve_mock.assert_called_with('/bundle-url-resolved', '/bundle-cached-path')

    def test_resolve_success_create_cache_dir(self):
        os_path_exists_mock = MagicMock(return_value=False)
        os_mkdirs_mock = MagicMock(return_value=())
        cache_path_mock = MagicMock(return_value='/bundle-cached-path')
        get_url_mock = MagicMock(return_value=('bundle-name', '/bundle-url-resolved'))
        urlretrieve_mock = MagicMock(return_value=('mock-bundle-file', ()))

        with patch('os.path.exists', os_path_exists_mock), \
                patch('os.makedirs', os_mkdirs_mock), \
                patch('conductr_cli.resolvers.uri_resolver.cache_path', cache_path_mock), \
                patch('conductr_cli.resolvers.uri_resolver.get_url', get_url_mock), \
                patch('conductr_cli.resolvers.uri_resolver.urlretrieve', urlretrieve_mock):
            is_resolved, bundle_name, bundle_file = uri_resolver.resolve_bundle('/cache-dir', '/bundle-url')
            self.assertTrue(is_resolved)
            self.assertEqual('bundle-name', bundle_name)
            self.assertEqual('mock-bundle-file', bundle_file)

        os_path_exists_mock.assert_called_with('/cache-dir')
        os_mkdirs_mock.assert_called_with('/cache-dir')
        cache_path_mock.assert_called_with('/cache-dir', '/bundle-url')
        get_url_mock.assert_called_with('/bundle-url')
        urlretrieve_mock.assert_called_with('/bundle-url-resolved', '/bundle-cached-path')

    def test_resolve_not_found(self):
        os_path_exists_mock = MagicMock(return_value=True)
        cache_path_mock = MagicMock(return_value='/bundle-cached-path')
        urlretrieve_mock = MagicMock(side_effect=URLError('no_such.bundle'))
        get_url_mock = MagicMock(return_value=('bundle-name', '/bundle-url-resolved'))

        with patch('os.path.exists', os_path_exists_mock), \
                patch('conductr_cli.resolvers.uri_resolver.cache_path', cache_path_mock), \
                patch('conductr_cli.resolvers.uri_resolver.get_url', get_url_mock), \
                patch('conductr_cli.resolvers.uri_resolver.urlretrieve', urlretrieve_mock):
            is_resolved, bundle_name, bundle_file = uri_resolver.resolve_bundle('/cache-dir', '/bundle-url')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        os_path_exists_mock.assert_called_with('/cache-dir')
        cache_path_mock.assert_called_with('/cache-dir', '/bundle-url')
        get_url_mock.assert_called_with('/bundle-url')
        urlretrieve_mock.assert_called_with('/bundle-url-resolved', '/bundle-cached-path')


class TestLoadFromCache(TestCase):
    def test_file(self):
        is_resolved, bundle_name, bundle_file = uri_resolver.load_from_cache('/cache-dir', '/tmp/bundle.zip')
        self.assertFalse(is_resolved)
        self.assertIsNone(bundle_name)
        self.assertIsNone(bundle_file)

    def test_uri_found(self):
        exists_mock = MagicMock(return_value=True)

        with patch('os.path.exists', exists_mock):
            is_resolved, bundle_name, bundle_file = uri_resolver.load_from_cache('/cache-dir',
                                                                                 'http://site.com/path/bundle-file.zip')
            self.assertTrue(is_resolved)
            self.assertEqual('bundle-file.zip', bundle_name)
            self.assertEqual('/cache-dir/bundle-file.zip', bundle_file)

        exists_mock.assert_called_with('/cache-dir/bundle-file.zip')

    def test_uri_not_found(self):
        exists_mock = MagicMock(return_value=False)

        with patch('os.path.exists', exists_mock):
            is_resolved, bundle_name, bundle_file = uri_resolver.load_from_cache('/cache-dir',
                                                                                 'http://site.com/path/bundle-file.zip')
            self.assertFalse(is_resolved)
            self.assertIsNone(bundle_name)
            self.assertIsNone(bundle_file)

        exists_mock.assert_called_with('/cache-dir/bundle-file.zip')


class TestGetUrl(TestCase):
    def test_url(self):
        filename, url = uri_resolver.get_url(
            'https://site.com/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip')
        self.assertEqual(
            'bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', filename)
        self.assertEqual(
            'https://site.com/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', url)

    def test_file(self):
        filename, url = uri_resolver.get_url(
            'bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip')
        self.assertEqual(
            'bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', filename)
        self.assertEqual(
            'file://' + os.getcwd() +
            '/bundle-1.0-e78ed07d4a895e14595a21aef1bf616b1b0e4d886f3265bc7b152acf93d259b5.zip', url)


class TestCachePath(TestCase):
    def test_cache_path_file(self):
        result = uri_resolver.cache_path('/cache-dir', '/var/test/file.zip')
        self.assertEqual('/cache-dir/file.zip', result)

    def test_cache_path_url(self):
        result = uri_resolver.cache_path('/cache-dir', 'http://some-site.com/path/test/file.zip')
        self.assertEqual('/cache-dir/file.zip', result)