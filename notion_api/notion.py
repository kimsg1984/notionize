"""
Notion API


"""

import logging as _logging
_log = _logging.getLogger(__name__)
_logging.basicConfig(format='%(asctime)s [%(filename)s:%(lineno)s|%(levelname)s] %(funcName)s(): %(message)s')

from notion_api.http_request import HttpRequest
from notion_api.objects import Database
from notion_api.objects import Page


class Notion:
    f"""
    Notion 
    
    'Notion' is basic object of 'notion-api' module.
    """

    def __init__(self, secret_key):
        self.__secret_key = secret_key
        self._request = HttpRequest(secret_key)

    def get_database(self, database_id):
        """return Database Object from 'database_id'

        https://www.notion.so/myworkspace/a8aec43384f447ed84390e8e42c2e089?v=...
                                         |---------- Database ID --------|
        """
        result = self._request.get('v1/databases/' + database_id)
        return Database(*result)

    def get_page(self, page_id):
        return Page(*self._request.get('v1/pages/' + page_id))

    def get_block(self, block_id):
        pass

    def get_user(self, user_id):
        pass