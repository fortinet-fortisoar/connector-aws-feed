""" Copyright start
  Copyright (C) 2008 - 2022 Fortinet Inc.
  All rights reserved.
  FORTINET CONFIDENTIAL & FORTINET PROPRIETARY SOURCE CODE
  Copyright end """

import requests, datetime
from connectors.core.connector import get_logger, ConnectorError

logger = get_logger('aws-feed')


def check_health(config):
    try:
        resp = make_rest_call(config)
        if resp:
            return True
    except Exception as Err:
        logger.exception(Err)
        raise ConnectorError(Err)


def compare_last_and_current_time(last_pull_time, current_pull_time):
    try:
        try:
            last_pull_ts = datetime.datetime.strptime(str(last_pull_time), "%Y-%m-%d-%H-%M-%S").timestamp()
        except Exception as err:
            logger.debug('Err = {0}'.format(err))
            logger.debug('Now checking format {}'.format('%Y-%m-%dT%H:%M:%S.%fZ'))
            last_pull_ts = datetime.datetime.strptime(str(last_pull_time), "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
        latest_pull_ts = int(datetime.datetime.strptime(current_pull_time, "%Y-%m-%d-%H-%M-%S").timestamp())
        if last_pull_ts < latest_pull_ts:
            return True
        return False
    except Exception as Err:
        logger.exception(Err)
        raise ConnectorError(Err)


def make_rest_call(config):
    try:
        server_url = config.get('server_url')
        response = requests.get(server_url, verify=config.get('verify_ssl'))
        if response.ok:
            if 'json' in str(response.headers):
                return response.json()
            else:
                logger.debug('Response not in json format')
                return response.text
        else:
            raise ConnectorError(
                'Unable to access the feed URL. Check connectivity and retry. Error status: ' + response.status_code)
    except requests.exceptions.SSLError:
        logger.error('An SSL error occurred.')
        raise ConnectorError('An SSL error occurred.')
    except requests.exceptions.ConnectionError:
        logger.error('A connection error occurred.')
        raise ConnectorError('A connection error occurred.')
    except Exception as Err:
        logger.exception(Err)
        raise ConnectorError(Err)


def filter_resp(config, resp):
    try:
        aws_services = config.get('aws_services')
        aws_regions = config.get('aws_regions')

        if aws_services and aws_regions:
            prefixes = [item for item in resp.get('prefixes') if
                        item["service"] in aws_services and item["region"] in aws_regions]
            ipv6_prefixes = [item for item in resp.get('ipv6_prefixes') if
                             item["service"] in aws_services and item["region"] in aws_regions]

        elif aws_services:
            prefixes = [item for item in resp.get('prefixes') if item["service"] in aws_services]
            ipv6_prefixes = [item for item in resp.get('ipv6_prefixes') if item["service"] in aws_services]
        elif aws_regions:
            prefixes = [item for item in resp.get('prefixes') if item["region"] in aws_regions]
            ipv6_prefixes = [item for item in resp.get('ipv6_prefixes') if item["region"] in aws_regions]
        else:
            prefixes = resp.get('prefixes')
            ipv6_prefixes = resp.get('ipv6_prefixes')

        seen = set()
        prefixes_records = [x for x in prefixes if
                            [x['ip_prefix'].replace(" ", "") not in seen, seen.add(x['ip_prefix'].replace(" ", ""))][0]]
        ipv6_prefixes_record = [x for x in ipv6_prefixes if [x['ipv6_prefix'].replace(" ", "") not in seen,
                                                             seen.add(x['ipv6_prefix'].replace(" ", ""))][0]]
        resp['prefixes'] = prefixes_records
        resp['ipv6_prefixes'] = ipv6_prefixes_record
        return resp
    except Exception as Err:
        logger.exception(Err)
        raise ConnectorError(Err)


def get_indicators(config, params):
    try:
        resp = make_rest_call(config)
        last_pull_time = params.get("last_pull_time")
        if last_pull_time != "" and last_pull_time != None and last_pull_time != 0:
            flag = compare_last_and_current_time(last_pull_time, resp.get('createDate', ''))
        else:
            flag = True
        if flag:
            return filter_resp(config, resp)
        else:
            resp['prefixes'] = []
            resp['ipv6_prefixes'] = []
        return resp
    except Exception as Err:
        logger.exception(Err)
        raise ConnectorError(Err)


operations = {
    'get_indicators': get_indicators
}
