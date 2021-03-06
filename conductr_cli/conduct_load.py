from pyhocon import ConfigFactory, ConfigTree
from pyhocon.exceptions import ConfigMissingException
from conductr_cli import bundle_utils, conduct_url, validation
from conductr_cli.exceptions import MalformedBundleError
from conductr_cli import resolver, bundle_installation
from functools import partial

import json
import logging
import requests


LOAD_HTTP_TIMEOUT = 30


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_invalid_config
@validation.handle_no_file
@validation.handle_bad_zip
@validation.handle_malformed_bundle
@validation.handle_bundle_resolution_error
@validation.handle_wait_timeout_error
@validation.handle_conduct_load_read_timeout_error
def load(args):
    if args.api_version == '1':
        return load_v1(args)
    else:
        return load_v2(args)


def load_v1(args):
    log = logging.getLogger(__name__)

    log.info('Retrieving bundle...')
    custom_settings = args.custom_settings
    resolve_cache_dir = args.resolve_cache_dir
    bundle_name, bundle_file = resolver.resolve_bundle(custom_settings, resolve_cache_dir, args.bundle)

    configuration_name, configuration_file = (None, None)
    if args.configuration is not None:
        log.info('Retrieving configuration...')
        configuration_name, configuration_file = resolver.resolve_bundle(custom_settings, resolve_cache_dir, args.configuration)

    bundle_conf = ConfigFactory.parse_string(bundle_utils.conf(bundle_file))
    overlay_bundle_conf = None if configuration_file is None else \
        ConfigFactory.parse_string(bundle_utils.conf(configuration_file))

    with_bundle_configurations = partial(apply_to_configurations, bundle_conf, overlay_bundle_conf)

    url = conduct_url.url('bundles', args)
    files = get_payload(bundle_name, bundle_file, with_bundle_configurations)
    if configuration_file is not None:
        files.append(('configuration', (configuration_name, open(configuration_file, 'rb'))))

    log.info('Loading bundle to ConductR...')
    response = requests.post(url, files=files, timeout=LOAD_HTTP_TIMEOUT)
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    response_json = json.loads(response.text)
    bundle_id = response_json['bundleId'] if args.long_ids else bundle_utils.short_id(response_json['bundleId'])

    if not args.no_wait:
        bundle_installation.wait_for_installation(response_json['bundleId'], args)

    log.info('Bundle loaded.')
    log.info('Start bundle with: conduct run{} {}'.format(args.cli_parameters, bundle_id))
    log.info('Unload bundle with: conduct unload{} {}'.format(args.cli_parameters, bundle_id))
    log.info('Print ConductR info with: conduct info{}'.format(args.cli_parameters))

    if not log.is_info_enabled() and log.is_quiet_enabled():
        log.quiet(response_json['bundleId'])

    return True


def apply_to_configurations(base_conf, overlay_conf, method, key):
    if overlay_conf is None:
        return method(base_conf, key)
    else:
        try:
            return method(overlay_conf, key)
        except ConfigMissingException:
            return method(base_conf, key)


def get_payload(bundle_name, bundle_file, bundle_configuration):
    return [
        ('nrOfCpus', bundle_configuration(ConfigTree.get_string, 'nrOfCpus')),
        ('memory', bundle_configuration(ConfigTree.get_string, 'memory')),
        ('diskSpace', bundle_configuration(ConfigTree.get_string, 'diskSpace')),
        ('roles', ' '.join(bundle_configuration(ConfigTree.get_list, 'roles'))),
        ('bundleName', bundle_configuration(ConfigTree.get_string, 'name')),
        ('system', bundle_configuration(ConfigTree.get_string, 'system')),
        ('bundle', (bundle_name, open(bundle_file, 'rb')))
    ]


def load_v2(args):
    log = logging.getLogger(__name__)

    log.info('Retrieving bundle...')
    custom_settings = args.custom_settings
    resolve_cache_dir = args.resolve_cache_dir
    bundle_name, bundle_file = resolver.resolve_bundle(custom_settings, resolve_cache_dir, args.bundle)
    bundle_conf = bundle_utils.zip_entry('bundle.conf', bundle_file)

    if bundle_conf is None:
        raise MalformedBundleError('Unable to find bundle.conf within the bundle file')
    else:
        configuration_name, configuration_file, bundle_conf_overlay = (None, None, None)
        if args.configuration is not None:
            log.info('Retrieving configuration...')
            configuration_name, configuration_file = resolver.resolve_bundle(custom_settings, resolve_cache_dir,
                                                                             args.configuration)
            bundle_conf_overlay = bundle_utils.zip_entry('bundle.conf', configuration_file)

        files = [('bundleConf', ('bundle.conf', bundle_conf))]
        if bundle_conf_overlay is not None:
            files.append(('bundleConfOverlay', ('bundle.conf', bundle_conf_overlay)))
        files.append(('bundle', (bundle_name, open(bundle_file, 'rb'))))
        if configuration_file is not None:
            files.append(('configuration', (configuration_name, open(configuration_file, 'rb'))))

        url = conduct_url.url('bundles', args)

        log.info('Loading bundle to ConductR...')
        response = requests.post(url, files=files, timeout=LOAD_HTTP_TIMEOUT)
        validation.raise_for_status_inc_3xx(response)

        if log.is_verbose_enabled():
            log.verbose(validation.pretty_json(response.text))

        response_json = json.loads(response.text)
        bundle_id = response_json['bundleId'] if args.long_ids else bundle_utils.short_id(response_json['bundleId'])

        if not args.no_wait:
            bundle_installation.wait_for_installation(response_json['bundleId'], args)

        log.info('Bundle loaded.')
        log.info('Start bundle with: conduct run{} {}'.format(args.cli_parameters, bundle_id))
        log.info('Unload bundle with: conduct unload{} {}'.format(args.cli_parameters, bundle_id))
        log.info('Print ConductR info with: conduct info{}'.format(args.cli_parameters))

        if not log.is_info_enabled() and log.is_quiet_enabled():
            log.quiet(response_json['bundleId'])

    return True
