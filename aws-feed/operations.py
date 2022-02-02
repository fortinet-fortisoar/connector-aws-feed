""" Copyright start
  Copyright (C) 2008 - 2022 Fortinet Inc.
  All rights reserved.
  FORTINET CONFIDENTIAL & FORTINET PROPRIETARY SOURCE CODE
  Copyright end """

import requests
from connectors.core.connector import get_logger, ConnectorError

logger = get_logger('aws-feed')


def check_health(config):
    try:
        return get_indicators(config, {}, True)
    except Exception as Err:
        logger.exception(Err)
        raise ConnectorError(Err)


def get_indicators(config, params, flag=False):
    try:
        resp = {}
        server_url = config.get('server_url')
        response = requests.get(server_url, verify=config.get('verify_ssl'))
        if not response.ok:
            raise ConnectorError(
                'Unable to access the feed URL. Check connectivity and retry. Error status: ' + response.status_code)
        if flag:
            return True
        aws_services = config.get('aws_services')
        aws_regions = config.get('aws_regions')
        if 'json' in str(response.headers):
            resp = response.json()

        if aws_services and aws_regions:
            prefixes = [item for item in resp.get('prefixes') if
                        item["service"] in  aws_services and item["region"] in aws_regions]
            ipv6_prefixes = [item for item in resp.get('ipv6_prefixes') if
                        item["service"] in aws_services and item["region"] in aws_regions]

        elif aws_services:
            prefixes = [item for item in resp.get('prefixes') if item["service"] in aws_services]
            ipv6_prefixes = [item for item in resp.get('ipv6_prefixes') if item["service"] in aws_services]
        elif aws_regions:
            prefixes = [item for item in resp.get('prefixes') if item["region"] in aws_regions]
            ipv6_prefixes = [item for item in resp.get('ipv6_prefixes') if item["region"] in aws_regions]
        else:
            return resp
        resp['prefixes'] = prefixes
        resp['ipv6_prefixes'] = ipv6_prefixes
        return resp
    except Exception as Err:
        logger.exception(Err)
        raise ConnectorError(Err)

operations = {
    'get_indicators': get_indicators
}
