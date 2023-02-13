from typing import Dict, Any

import notionizer.object_adt
import notionizer.object_basic
import notionizer.functions
import notionizer.http_request

ImmutableProperty = notionizer.object_adt.ImmutableProperty
NotionUpdateObject = notionizer.object_basic.NotionUpdateObject
UserBaseObject = notionizer.object_basic.UserBaseObject
notion_object_init_handler = notionizer.functions.notion_object_init_handler
HttpRequest = notionizer.http_request.HttpRequest



_log = __import__('logging').getLogger(__name__)


class UserProperty(ImmutableProperty):
    """
    User Property for Database, Page: 'created_by' and 'last_edited_by'
    """

    def __set__(self, owner: NotionUpdateObject, value: Dict[str, Any]) -> None:
        obj = User(owner._request, value)
        super().__set__(owner, obj)


class User(NotionUpdateObject, UserBaseObject):
    """
    User Object
    """
    _api_url = 'v1/users/'

    @notion_object_init_handler
    def __init__(self, request: HttpRequest, data: Dict[str, Any]):
        """

        :param request:
        :param data:
        """
        self._update_event_status = False
        super().__init__(request, data)

    def update_info(self) -> None:
        """
        get all information of user. If already updated, stop and doesn't make request event.
        :return: None
        """
        if self._update_event_status:
            return

        url = self._api_url + str(self.id)
        request, data = self._request.get(url)
        _log.debug(f"{type(self).__init__}")
        type(self)(request, data, instance_id=data['id'])
