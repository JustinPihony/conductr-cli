from conductr_cli import bundle_utils, conduct_url, validation, bundle_scale
import json
import requests
import logging
from conductr_cli.http import DEFAULT_HTTP_TIMEOUT


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_wait_timeout_error
def stop(args):
    """`conduct stop` command"""

    log = logging.getLogger(__name__)
    path = 'bundles/{}?scale=0'.format(args.bundle)
    url = conduct_url.url(path, args)
    response = requests.put(url, timeout=DEFAULT_HTTP_TIMEOUT)
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    response_json = json.loads(response.text)
    bundle_id = response_json['bundleId'] if args.long_ids else bundle_utils.short_id(response_json['bundleId'])

    log.info('Bundle stop request sent.')

    if not args.no_wait:
        bundle_scale.wait_for_scale(response_json['bundleId'], 0, args)

    log.info('Unload bundle with: conduct unload{} {}'.format(args.cli_parameters, bundle_id))
    log.info('Print ConductR info with: conduct info{}'.format(args.cli_parameters))

    return True
