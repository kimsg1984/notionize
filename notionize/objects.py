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

from notionize.http_request import HttpRequest

from notionize.object_basic import NotionObject
from notionize.object_basic import UserObject
from notionize.object_basic import ObjectProperty
from notionize.object_adt import DictionaryObject
from notionize.properties_basic import PropertyObject
from notionize.properties_property import PropertiesProperty
from notionize.functions import notion_object_init_handler
from notionize.properties_basic import TitleProperty, PagePropertyObject, DbPropertyObject
from notionize.object_adt import ImmutableProperty, MutableProperty
from notionize.properties_db import DbPropertyRelation

from notionize.query import Query
from notionize.query import filter
from notionize.query import T_Filter
from notionize.query import T_Sorts

from typing import Optional
from typing import Any
from typing import Dict
from typing import List
from typing import Union
from typing import Set

from types import SimpleNamespace

_log = __import__('logging').getLogger(__name__)


class NotionBasicObject(NotionObject):
    """
    '_NotionBasicObject' with '_update' method which update information and refresh itself.
    """
    _instances: Dict[str, Any] = {}

    _api_url: str
    id: ImmutableProperty

    def __new__(cls, request: HttpRequest, data: Dict[str, Any], instance_id: Optional[str] = None
                , **kwargs) -> 'NotionBasicObject':
        """
        construct '_NotionBasicObject' class.

        check 'key' value and if instance is exist, reuse instance with renewed namespace.
        :param request:
        :param data:
        :param instance_id:
        """

        _log.debug(" ".join(map(str, ('NotionBasicObject:', cls))))
        instance: 'NotionBasicObject' = super(NotionBasicObject, cls).__new__(cls, data)  # type: ignore

        # assign 'new namespace' with 'unassigned descriptors'.
        if instance_id:
            NotionBasicObject._instances[instance_id].__dict__ = instance.__dict__
        else:
            instance_id = str(data['id'])
            NotionBasicObject._instances[instance_id] = instance

        return instance

    def __init__(self, request: HttpRequest, data: Dict[str, Any], instance_id: Optional[str] = None):
        """

        :param request:
        :param data:
        :param instance_id:
        """
        _log.debug(" ".join(map(str, ('NotionBasicObject:', self))))
        self._request: HttpRequest = request
        super().__init__(data)

    def _update(self, property_name: str, contents: Dict[str, Any]) -> None:
        url = self._api_url + str(self.id)
        request, data = self._request.patch(url, {property_name: contents})
        # update property of object using 'id' value.
        cls: type(NotionBasicObject) = type(self)  # type: ignore
        # update instance
        cls(request, data, instance_id=str(data['id']))


class QueriedPageIterator:
    """
    database Queried Page Iterator
    """

    def __init__(self, request: HttpRequest, url: str, payload: Dict[str, Any]):
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
        self._payload: Dict[str, Any] = dict(payload)

        request_post: HttpRequest
        result_data: Dict[str, Any]
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


"""
Where user objects appear in the API
User objects appear in the API in nearly all objects returned by the API, including:

[v] 'Database' object under 'created_by' and 'last_edited_by'.
[v] 'Page' object under created_by and last_edited_by and in people property items.
[v] 'Property' object when the property is a people property.
[ ] 'Block' object under created_by and last_edited_by.
[ ] 'Rich text' object, as user mentions.
"""


class User(NotionBasicObject, UserObject):
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


class UserProperty(ImmutableProperty):
    """
    User Property for Database, Page: 'created_by' and 'last_edited_by'
    """

    def __set__(self, owner: NotionBasicObject, value: Dict[str, Any]) -> None:
        obj = User(owner._request, value)
        super().__set__(owner, obj)


class Database(NotionBasicObject):

    _api_url = 'v1/databases/'

    id = ImmutableProperty()
    created_time = ImmutableProperty()
    created_by = UserProperty()
    last_edited_by = UserProperty()
    title = TitleProperty()
    icon = MutableProperty()
    cover = MutableProperty()

    properties: PropertiesProperty = PropertiesProperty(object_type='database')

    @notion_object_init_handler
    def __init__(self, request: HttpRequest, data: Dict[str, Any], update_relation: bool = True):
        """
         initilize Database instance.

        :param request: Notion._request
        :param data: returned from ._request
        :param update_relation: (bool) assign 'False' for 'database object' of checking relation reference
        """

        object_type = data['object']
        assert object_type == 'database', f"data type is not 'database'. (type: {object_type})"

        _log.debug(" ".join(map(str, ('Database:', self))))
        super().__init__(request, data)
        self._relation_reference: Dict[str, DictionaryObject] = dict()
        self._query_helper = Query(self.properties)
        if update_relation:
            self._update_relation_reference()

    def __str__(self) -> str:
        title = ''
        try:
            title = ": " + str(self.title)
        except:
            pass
        str_content = f"<'{self.__class__.__name__}{title}'>"
        return str_content

    def _update_relation_reference(self) -> None:
        """
        update relation reference to
        :return:
        """
        relation_db_id_set: Set[str] = set()
        prop: DbPropertyRelation
        for prop in self.properties.values():
            if prop.type == 'relation':
                relation_db_id_set.add(prop.relation['database_id'])

        for db_id in relation_db_id_set:
            db: 'Database' = Database(*self._request.get('v1/databases/' + db_id), update_relation=False)

            sub_prop: DbPropertyObject
            sub_prop_dict: Dict[str, str] = dict()

            for sub_prop in db.properties.values():
                sub_prop_dict[str(sub_prop.id)] = str(sub_prop.type)  # type: ignore

            self._relation_reference[db_id] = DictionaryObject('relation_properties', self, sub_prop_dict)

    def query(self, query_expression: str) -> QueriedPageIterator:
        """
        query with simple 'python expression'.

        :param query_expression:
        :return: 'pages iterator'
        """
        filter_ins: Union[filter, None] = self._query_helper.query_by_expression(query_expression)

        # todo: sorts implement
        sorts_ins: Union[filter, None] = None
        return self._filter_and_sort(notion_filter=filter_ins, sorts=sorts_ins)

    def _filter_and_sort(self, notion_filter: Optional[T_Filter] = None, sorts: Optional[T_Sorts] = None,
                         start_cursor: Optional[int] = None, page_size: Optional[int] = None) -> QueriedPageIterator:
        """
        Args:
            notion_filter: query.filter
            sorts: query.sorts
            start_cursor: string
            page_size: int (Max:100)

        Returns: 'pages iterator'
        """
        filter_obj: Dict[str, Any]
        sort_obj: List[Any]

        if notion_filter:
            notion_filter = notion_filter.get_body()
        else:
            notion_filter = {'or': []}

        if sorts:
           sort_obj = list(sorts.get_body())
        else:
            sort_obj = list()

        payload: Dict[str, Any] = dict()
        payload['filter'] = notion_filter
        payload['sorts'] = sort_obj

        if page_size:
            payload['page_size'] = page_size

        id_raw = str(self.id).replace('-', '')
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
        payload['properties'] = dict(properties)

        if properties:
            for key, value in properties.items():

                assert key in self.properties, f"'{key}' property not in the database '{self.title}'."
                db_property: DbPropertyObject = self.properties[key]
                assert db_property._mutable is True, f"{db_property}('{key}') property is 'Immutable Property'"
                assert type(value) in db_property._input_validation, f"type of '{value}' is '{type(value)}'. " \
                    f"{db_property}('{key}') property has type {db_property._input_validation}"

                value_converted = db_property._convert_to_update(value)
                payload['properties'][key] = value_converted

        return Page(*self._request.post(url, payload))


class Page(NotionBasicObject):
    """
    Page Object
    """
    properties = PropertiesProperty(object_type='page')
    id = ImmutableProperty()
    created_by = UserProperty()
    last_edited_by = UserProperty()

    _api_url = 'v1/pages/'

    @notion_object_init_handler
    def __init__(self, request: HttpRequest, data: Dict[str, Any]):

        """

        Args:
            request: Notion._request
            data: returned from ._request
        """

        object_type = data['object']
        assert object_type == 'page', f"data type is not 'database'. (type: {object_type})"
        super().__init__(request, data)

    def __repr__(self) -> str:
        return f"<Page at '{self.id}'>"

    def get_properties(self) -> Dict[str, Any]:
        """
        return value of properties simply
        :return: {'key' : value, ...}
        """
        result = dict()
        for k, v in self.properties.items():
            result[k] = v.get_value()

        return result


