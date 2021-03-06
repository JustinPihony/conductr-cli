from conductr_cli import bundle_utils, conduct_url, validation
from conductr_cli import bundle_scale
import json
import logging
import requests


@validation.handle_connection_error
@validation.handle_http_error
@validation.handle_wait_timeout_error
def run(args):
    """`conduct run` command"""

    log = logging.getLogger(__name__)

    if args.affinity is not None and args.api_version == '1':
        log.error('Affinity feature is only available for v1.1 onwards of ConductR')
        return
    elif args.affinity is not None:
        path = 'bundles/{}?scale={}&affinity={}'.format(args.bundle, args.scale, args.affinity)
    else:
        path = 'bundles/{}?scale={}'.format(args.bundle, args.scale)

    url = conduct_url.url(path, args)
    response = requests.put(url)
    validation.raise_for_status_inc_3xx(response)

    if log.is_verbose_enabled():
        log.verbose(validation.pretty_json(response.text))

    response_json = json.loads(response.text)
    bundle_id = response_json['bundleId'] if args.long_ids else bundle_utils.short_id(response_json['bundleId'])

    log.info('Bundle run request sent.')

    if not args.no_wait:
        bundle_scale.wait_for_scale(response_json['bundleId'], args.scale, args)

    log.info('Stop bundle with: conduct stop{} {}'.format(args.cli_parameters, bundle_id))
    log.info('Print ConductR info with: conduct info{}'.format(args.cli_parameters))

    return True
