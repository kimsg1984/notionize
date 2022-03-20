"""
notion objects

"""

from notion_api.http_request import HttpRequest
from functools import wraps as _wraps


def _from_rich_text_array_to_plain_text(array):
    return ''.join([e['plain_text'] for e in array])


def _from_plain_text_to_rich_text_array(string):
    return [{"text": {"content": string}, 'plain_text':string}]


class NotionApiPropertyException(Exception):
    pass


def _notion_object_init_handler(init_function):
    """
    All notion object having '_update' method should be wrapped by this.
    If '__init__' method is called with  'key' keyword argument, wrapper will not execute it
    because '__new__' method execute with '__init__' to handle namespace.
    """

    @_wraps(init_function)
    def wrapper_function(*args, **kwargs):
        if 'key' not in kwargs:
            return init_function(*args, **kwargs)

    return wrapper_function


class ImmutableProperty:
    """
    default object for property for immutable like 'id' or  'type'.
    """

    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = '__property_' + name

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private_name)

    def _check_assigned(self, obj):
        return hasattr(obj, self.private_name)

    def __set__(self, obj, value):
        if not self._check_assigned(obj):
            setattr(obj, self.private_name, value)
        else:
            raise NotionApiPropertyException('Immutable property could not be assigned')


class MutableProperty(ImmutableProperty):
    """
    Property object for mutable, assigning event with update.
    """

    def __set__(self, obj, value):

        if not self._check_assigned(obj):
            setattr(obj, self.private_name, value)
        else:
            obj._update(self.public_name, value)
            # Mutable Property does not need to assign with 'setattr' function. '_update' method will
            # generate 'new instance' with 'updated data' and replace the whole namespace of current instance.


# Class for Database
class TitleProperty(MutableProperty):
    """
    Specific object for title of database.

    :: USAGE

    [1] print(db.title)
    'some title'

    [2] db.title = 'fixed title'
    ...

    """

    def __get__(self, obj, objtype=None):
        return _from_rich_text_array_to_plain_text(getattr(obj, self.private_name))

    def __set__(self, obj, value):
        if type(value) == str:
            value = _from_plain_text_to_rich_text_array(value)
        super().__set__(obj, value)

'''
class _DatabasePropertyObject:
    """
    Basic Object for Data Properties.
    """
    id = ImmutableProperty()
    type = MutableProperty()
    name = MutableProperty()


class TitleDatabasePropertyObject:
    title = TitleProperty()


class TextDatabasePropertyObject:
    rich_text = MutableProperty()
    # asdf


class _DatabaseSubPropertyObject:
    def _update(self):
        pass


class DatabaseSubPropertyNumberObject(_DatabaseSubPropertyObject):
    format = MutableProperty()


class NumberDatabasePropertyObject:
    """
    It has additional property 'number' which has only sub property 'format'.
    available type of format:
        number, number_with_commas, percent, dollar, canadian_dollar, euro, pound, yen, ruble, rupee, won, yuan, real,
        lira, rupiah, franc, hong_kong_dollar, new_zealand_dollar, krona, norwegian_krone, mexican_peso, rand,
        new_taiwan_dollar, danish_krone, zloty, baht, forint, koruna, shekel, chilean_peso, philippine_peso, dirham,
        colombian_peso, riyal, ringgit, leu, argentine_peso, uruguayan_peso.
    """

    number = DatabaseSubPropertyNumberObject()


class DatabaseSubPropertySelectObject(_DatabaseSubPropertyObject):
    format = MutableProperty()


class DatabasePropertiesProperty(MutableProperty):
    """
    Specific object for Properties of Database.
    """

    def create_property(self):
        raise NotImplemented

    def delete_property(self, property_name:str):
        raise NotImplemented

    def __get__(self, obj, objtype=None):
        return self

    def __set__(self, obj, value):

        if not self._check_assigned(obj):
            setattr(obj, self.private_name, value)
        else:
            obj._update(self.public_name, value)
            # Mutable Property does not need to assign with 'setattr' function. '_update' method will
            # generate 'new instance' with 'updated data' and replace the whole namespace of current instance.
'''

# Class for Notion


class _NotionObject(object):
    object = ImmutableProperty()
    id = ImmutableProperty()
    created_time = ImmutableProperty()
    last_edited_time = ImmutableProperty()
    parent = ImmutableProperty()
    url = ImmutableProperty()

    properties = MutableProperty()
    cover = MutableProperty()
    icon = MutableProperty()

    _instances = {}

    def __new__(cls, request, data, key: str=None):
        instance = super(_NotionObject, cls).__new__(cls)
        if key:
            org_namespace = dict(_NotionObject._instances[key].__dict__)
            cls.__init__(instance, request, data)
            # instance.__init__(request, data)
            _NotionObject._instances[key].__dict__ = instance.__dict__
            for k in set(org_namespace) - set(instance.__dict__):
                instance.__dict__[k] = org_namespace[k]

        else:
            key = data['id']
            _NotionObject._instances[key] = instance

        return instance


class Database(_NotionObject):
    title = TitleProperty()

    _api_url = 'v1/databases/'

    @_notion_object_init_handler
    def __init__(self, request, data):
        """
        Args:
            request: Notion._request
            data: returned from ._request
        """

        object_type = data['object']
        assert object_type == 'database', f"data type is not 'database'. (type: {object_type})"

        self._request = request
        for attr in data:
            setattr(self, attr, data[attr])

    def _refresh(self, data):
        pass

    def query(self, filter=None, sorts=None,
              start_cursor=None, page_size=None):
        """
        Args:
            filter: notion_filters.filter
            sorts: notion_filters.sorts
            start_cursor: string
            page_size: int (Max:100)

        Returns: 'pages iterator'

        """
        if filter:
            filter = filter._body
        else:
            filter = {'or':[]}

        if sorts:
           sorts = dict(sorts._body)
        else:
            sorts = []

        payload = dict()
        payload['filter'] = filter
        payload['sorts'] = sorts

        if page_size:
            payload['page_size'] = page_size

        id_raw = self.id.replace('-', '')
        url = f'{self._api_url}{id_raw}/query'
        return QueriedPageIterator(self._request, url, payload)

    def _update(self, property, contents):
        url = self._api_url + self.id
        print(self.id, {property: contents})
        request, data = self._request.patch(url, {property: contents})
        print(data)
        type(self)(request, data, key=data['id'])

    def __repr__(self):
        return f"<Database '{self.title}' at '{self.id}'>"


class Page(_NotionObject):
    """
    Page Object
    """
    cover = MutableProperty()
    _api_url = 'v1/pages/'

    def __init__(self, request, data):
        """

        Args:
            request: Notion._request
            data: returned from ._request
        """
        object_type = data['object']
        assert object_type == 'page', f"data type is not 'database'. (type: {object_type})"

        for attr in data:
            setattr(self, attr, data[attr])

    def __repr__(self):
        return f"<Page at '{self.id}'>"


# Else
class QueriedPageIterator:
    """
    database Queried Page Iterator
    """
    # self._request.post(url, payload))
    # return QueriedPageIterator(self, url, payload)
    def __init__(self, request: HttpRequest, url: str, payload: dict):
        """
        Automatically query next page.

        Warning: read all columns from huge database should be harm.

        Args:
            request: HttpRequest
            url: str
            payload: dict

        Usage:
            queried = db.query(filter=filter_base)
            for page in queried:
                ...

        """

        self._request: HttpRequest = request
        self._url: str = url
        self._payload: dict = dict(payload)

        request_post: HttpRequest
        result_data: dict
        request_post, result_data = request.post(url, payload)

        self._assign_data(result_data)

    def _assign_data(self, result_data: dict):

        self.object = result_data['object']
        self._results = result_data['results']
        self.next_cursor = result_data['next_cursor']
        self.has_more = result_data['has_more']

        self.results_iter = iter(self._results)

    def __iter__(self):
        self.results_iter = iter(self._results)
        return self

    def __next__(self):
        try:
            return Page(self._request, next(self.results_iter))
        except StopIteration:

            if self.has_more:
                self._payload['start_cursor'] = self.next_cursor
                request, result_data = self._request.post(self._url, self._payload)
                self._assign_data(result_data)
                return self.__next__()
            else:
                raise StopIteration


# database = ['object', 'id', 'cover', 'icon', 'created_time', 'last_edited_time', 'title', 'properties', 'parent', 'url']
# page = ['archived', 'cover', 'created_time', 'icon', 'id', 'last_edited_time', 'object', 'parent', 'properties', 'url']


object_map = {
    'database': Database,
    'page': Page,
}