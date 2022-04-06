"""
Notion Objects


For using 'python assignment operator', only 'updateable' properties allow to assign. Other properties should be prohibited
to assign.

Fallow rules make python object safety from user assignment event.


- Only mutable properties defined 'in class' manually as 'MutableProperty' descriptor.
- Other properties are defined 'Immutable Property' dynamically.
- Some properties has own 'object' and 'array', which in python are 'dictionay' and 'list'. It's
  replace as '_DictionaryObject' and '_ListObject'. These are 'immutable' as default. But 'mutable' parameter makes
  these 'mutable' object.

"""

from notion_api.http_request import HttpRequest

import logging

from notion_api.object_basic import _notion_object_init_handler, _from_rich_text_array_to_plain_text, \
    _from_plain_text_to_rich_text_array, _NotionObject, _DictionaryObject
from notion_api.properties import ImmutableProperty, MutableProperty, _PagePropertyObject, \
    _DbPropertyObject, _log, database_properties_mapper, page_properties_mapper, _PropertyObject

_log = logging.getLogger(__name__)


class _NotionBasicObject(_NotionObject):
    """
    '_NotionBasicObject' for Database, Page and Block.
    """
    _instances = {}

    def __new__(cls, request, data, instance_id: str = None):
        """
        construct '_NotionBasicObject' class.

        check 'key' value and if instance is exist, reuse instance with renewed namespace.
        :param request:
        :param data:
        :param instance_id:
        """
        _log.debug(" ".join(map(str, ('_NotionBasicObject:', cls))))
        instance = super(_NotionBasicObject, cls).__new__(cls, data)

        if instance_id:
            org_namespace = dict(_NotionBasicObject._instances[instance_id].__dict__)

            # instance.__init__(data)

            _NotionBasicObject._instances[instance_id].__dict__ = instance.__dict__
            for k in set(org_namespace) - set(instance.__dict__):
                instance.__dict__[k] = org_namespace[k]

        else:
            instance_id = data['id']

            _NotionBasicObject._instances[instance_id] = instance

        return instance

    def __init__(self, request, data):
        _log.debug(" ".join(map(str, ('_NotionBasicObject:', self))))
        super().__init__(data)

    def _update(self, property_name, contents):
        url = self._api_url + self.id
        request, data = self._request.patch(url, {property_name: contents})
        # update property of object using 'id' value.
        cls: type(_NotionBasicObject) = type(self)
        cls(request, data, instance_id=data['id'])


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
        _log.debug(f"{self}, {obj}")
        return _from_rich_text_array_to_plain_text(getattr(obj, self.private_name))

    def __set__(self, obj, value):
        if type(value) == str:
            value = _from_plain_text_to_rich_text_array(value)

        super().__set__(obj, value)


"""
Page Property for Properties
"""

"""
Database Property for Properties
"""


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


class Database(_NotionBasicObject):

    _api_url = 'v1/databases/'

    id = ImmutableProperty()
    created_time = ImmutableProperty()
    title = TitleProperty()
    icon = MutableProperty()
    cover = MutableProperty()

    properties = PropertiesProperty(object_type='database')

    @_notion_object_init_handler
    def __init__(self, request, data):
        """
        initilize Database instance.

        Args:
            request: Notion._request
            data: returned from ._request
        """

        object_type = data['object']
        assert object_type == 'database', f"data type is not 'database'. (type: {object_type})"
        self._request: HttpRequest = request

        _log.debug(" ".join(map(str, ('Database:', self))))
        super().__init__(request, data)

    def _update(self, property_name, contents):
        url = self._api_url + self.id
        request, data = self._request.patch(url, {property_name: contents})
        # update property of object using 'id' value.
        _log.debug(f"{type(self).__init__}")
        type(self)(request, data, instance_id=data['id'])

    def query(self, filter=None, sorts=None,
              start_cursor=None, page_size=None):
        """
        Args:
            filter: query.filter
            sorts: query.sorts
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

    def get_as_tuples(self, queried_page_iterator: QueriedPageIterator, columns_select: list=[], header=True):
        """
        change QueriedPageIterator as simple values.
        :param queried_page_iterator: QueriedPageIterator()
        :param columns_select: ('column_name1', 'column_name2'...)
        :return: tuple(('title1', 'title2'...), (value1, value2,...)... )

        Usage:

        database.get_tuples(database.query())
        database.get_tuples(database.query(), ('column_name1', 'column_name2'), header=False)
        """
        result = list()

        if columns_select:
            keys = tuple(columns_select)
        else:
            keys = (*self.properties.keys(),)

        for page in queried_page_iterator:
            values = page.get_properties()
            result.append(tuple([values[k] for k in keys]))
        if not result:
            return tuple()

        if header:
            result = [keys] + result

        return tuple(result)

    def get_as_dictionaries(self, queried_page_iterator: QueriedPageIterator, columns_select: list=[]):
        """
        change QueriedPageIterator as simple values.
        :param queried_page_iterator: QueriedPageIterator()
        :param columns_select: ('column_name1', 'column_name2'...)
        :return: dict(('key1': 'value1', 'key2': 'value2'...), ... )

        Usage:

        database.get_tuples(database.query())
        database.get_tuples(database.query(), ('column_name1', 'column_name2'), header=False)
        """
        result = list()

        if columns_select:
            keys = tuple(columns_select)
        else:
            keys = (*self.properties.keys(),)

        for page in queried_page_iterator:
            values = page.get_properties()
            result.append({k: values[k] for k in keys})
        if not result:
            return tuple()

        return tuple(result)

    def create_page(self, properties: dict = {}):
        """
        Create 'new page' in the database.

        :param properties: receive 'dictionay' type for database property.
        :return: 'Page' object.
        """

        url = 'v1/pages/'

        payload = dict()
        payload['parent'] = {'database_id': self.id}

        # TODO: properties validation
        if properties:
            for key, value in properties.items():
                assert key in self.properties, f"'{key}' property not in the database '{self.title}'."
                

        payload['properties'] = dict(properties)

        return Page(*self._request.post(url, payload))


class Page(_NotionBasicObject):
    """
    Page Object
    """
    properties = PropertiesProperty(object_type='page')

    _api_url = 'v1/pages/'

    @_notion_object_init_handler
    def __init__(self, request, data):

        """

        Args:
            request: Notion._request
            data: returned from ._request
        """
        self._request = request
        object_type = data['object']
        assert object_type == 'page', f"data type is not 'database'. (type: {object_type})"
        super().__init__(request, data)

    def __repr__(self):
        return f"<Page at '{self.id}'>"

    def get_properties(self) -> dict:
        """
        return value of properties simply
        :return: {'key' : value, ...}
        """
        result = dict()
        for k, v in self.properties.items():
            v: _PagePropertyObject
            result[k] = v.get_value()

        return result


class PropertiesProperty(_DictionaryObject, ImmutableProperty):
    """
    'PropertiesProperty' for 'Database' and 'Page'. Mutable Type
    """
    def __new__(cls, object_type: str):

        super_cls = super(PropertiesProperty, cls)
        notion_ins = super_cls.__new__(cls)

        _log.debug("PropertiesProperty: " + str(cls))

        return notion_ins

    def __init__(self, object_type: str):
        """
        :param object_type: 'database' or 'page'.
        """
        assert object_type in ['database', 'page']
        self._parent_object_type = object_type
        super().__init__('properties')

    @property
    def _data(self):
        """
        override '_data' property to be a descriptor.
        :return:
        """
        return getattr(self._parent, self.private_name)

    def __set__(self, owner, value: dict):

        self.__set_name__(owner, self.name)

        if not self._check_assigned(owner):
            setattr(self._parent, self.private_name, dict())

        _log.debug(f'{self}, {owner}')
        mutable_status = self._mutable
        self._parent = owner
        self._mutable = True
        if self._parent_object_type == 'database':
            properties_mapper = database_properties_mapper
        elif self._parent_object_type == 'page':
            properties_mapper = page_properties_mapper
        else:
            raise NotImplemented(f"'{self._parent_object_type}' object is not implemented")

        for k, v in value.items():
            if v['type'] in properties_mapper:
                property_cls: _PropertyObject = properties_mapper.get(v['type'])
                property_ins: _PropertyObject = property_cls(self, v, parent_type=self._parent_object_type)
            else:
                if self._parent_object_type == 'database':
                    # _log.debug(f"self, v: {self}, {v}")
                    property_ins: _DbPropertyObject = _DbPropertyObject(self, v, parent_type=self._parent_object_type, force_new=True)

                elif self._parent_object_type == 'page':
                    property_ins: _PagePropertyObject = _PagePropertyObject(self, v, parent_type=self._parent_object_type,
                                                                        force_new=True)
            self.__setitem__(k, property_ins)
        self._mutable = mutable_status

    def _update(self, property_name, data):
        """
        generate 'update content' and call '_update' method of '_parent' object.

        :param property_name:
        :param data:
        :return:
        """
        _log.debug(f"self._parent: {self._parent}")
        self._parent._update('properties', {property_name:data})