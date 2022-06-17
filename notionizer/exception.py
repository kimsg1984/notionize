
class NotionApiException(Exception):
    pass


class NotionApiPropertyException(NotionApiException):
    pass


class NotionApiPropertyUnassignedException(NotionApiPropertyException):
    pass


class NotionApiQueoryException(NotionApiException):
    pass
