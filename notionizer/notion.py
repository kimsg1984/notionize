"""
Notion API


"""

import logging as _logging
_log = _logging.getLogger(__name__)
_logging.basicConfig(format='%(asctime)s [%(filename)s:%(lineno)s|%(levelname)s] %(funcName)s(): %(message)s')

from notionizer.http_request import HttpRequest
from notionizer.objects import Database
from notionizer.objects import Page
from notionizer.objects import User


class Notion:
    f"""
    Notion

    'Notion' is basic object of 'notionized' module.
    """

    def __init__(self, secret_key: str):
        self.__secret_key = secret_key
        self._request: HttpRequest = HttpRequest(secret_key)

    def get_database(self, database_id: str) -> Database:
        """
        get 'Database' Object by 'database_id'

        https://www.notion.so/myworkspace/a8aec43384f447ed84390e8e42c2e089?v=...
                                         |---------- Database ID --------|
        :param database_id:
        :return: Database
        """

        result = self._request.get('v1/databases/' + database_id)
        db_object: Database = Database(*result)
        return db_object

    def get_page(self, page_id: str) -> Page:
        """
        get 'Page' object by 'page id'
        :param page_id:
        :return: Page
        """
        page_object: Page = Page(*self._request.get('v1/pages/' + page_id))
        return page_object

    def get_user(self, user_id: str) -> User:
        """
        get 'User' object by 'user id'.
        :param user_id:
        :return: User
        """
        user_object: User = User(*self._request.get('v1/users/' + user_id))
        return user_object

    def get_all_users(self) -> list:
        """
        get a paginated list of 'Users for the workspace(user and bots)'.
        :return: List[User]
        """
        request: HttpRequest
        user_list = list()

        request, result = self._request.get('v1/users')

        for obj in result['results']:
            user_list.append(User(request, obj))
        return user_list

    def get_me(self) -> User:
        """
        get the 'bot User' itself associated with the API token
        :return: User
        """
        me: User = User(*self._request.get('v1/users/me'))
        return me

    def get_block(self, block_id: str):
        pass