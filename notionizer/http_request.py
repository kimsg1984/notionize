"""
HTTP REQUEST

managing request

"""

import requests  # type: ignore
import json
import logging

from notionizer import settings

from typing import Dict, Any, Tuple, TypeVar

_logger = logging.getLogger(__name__)


class HttpRequestError(Exception):
    pass


T_HttpRequest = TypeVar('T_HttpRequest', bound='HttpRequest')


class HttpRequest:

    def __init__(self, secret_key: str, timeout: int = 15):
        self.base_url = settings.BASE_URL
        self.__headers = {
            'Authorization': 'Bearer ' + secret_key,
            'Content-Type': 'application/json',
            'Notion-Version': settings.NOTION_VERSION
        }
        self.timeout = timeout

    def post(self: T_HttpRequest, url: str, payload: Dict[str, Any]) -> Tuple[T_HttpRequest, Dict[str, Any]]:
        return self._request('POST', url, payload)

    def get(self: T_HttpRequest, url: str) -> Tuple[T_HttpRequest, Dict[str, Any]]:
        return self._request('GET', url, {})

    def patch(self: T_HttpRequest, url: str, payload: Dict[str, Any]) -> Tuple[T_HttpRequest, Dict[str, Any]]:
        return self._request('PATCH', url, payload)

    def _request(self: T_HttpRequest, request_type: str, url: str, payload: Dict[str, Any]) -> Tuple[T_HttpRequest,
                                                                                                     Dict[str, Any]]:
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
        request_url: str = self.base_url + url
        result_json: str = requests.request(request_type, request_url, headers=self.__headers,
                                            data=payload_json, timeout=self.timeout).text

        result: Dict[str, Any] = json.loads(result_json)
        _logger.debug(f"result: {result}")
        if result['object'] == 'error':
            status = result['status']
            code = result['code']
            message = result['message']
            raise HttpRequestError(f'[{status}] {code}: {message}, {payload} from: {request_url}')

        return self, result
