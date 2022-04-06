"""
HTTP REQUEST

managing request

"""

import requests
import json
import logging

from notion_api import settings

_logger = logging.getLogger(__name__)


class HttpRequestError(Exception):
    pass


class HttpRequest:

    def __init__(self, secret_key, timeout=15):
        self.base_url = settings.BASE_URL
        self.__headers = {
            'Authorization': 'Bearer ' + secret_key,
            'Content-Type': 'application/json',
            'Notion-Version': settings.NOTION_VERSION
        }
        self.timeout = timeout

    def post(self, url, payload):
        return self._request('POST', url, payload)

    def get(self, url):
        result = self._request('GET', url, '')
        return result

    def patch(self, url, payload):
        return self._request('PATCH', url, payload)

    def _request(self, request_type, url, payload):
        """

        :param request_type: 'POST' or 'GET'
        :param url: fully assembled url
        :param payload:
        :return: python data type object(dictionay and list)
        """
        _logger.debug('url: ' + self.base_url + url)
        _logger.debug('payload:' + str(payload))
        payload_json = ''
        if payload:
            payload_json = json.dumps(payload)

        result = requests.request(request_type, self.base_url + url, headers=self.__headers, data=payload_json,
                                  timeout=self.timeout).text

        result = json.loads(result)
        _logger.debug(f"result: {result}")
        if result['object'] == 'error':
            status = result['status']
            code = result['code']
            message = result['message']
            raise HttpRequestError(f'[{status}] {code}: {message}, {payload}')

        return self, result
