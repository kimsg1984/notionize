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

from notionizer.http_request import HttpRequest

from notionizer.object_basic import NotionObject
from notionizer.object_basic import UserObject
from notionizer.object_adt import DictionaryObject
from notionizer.properties_property import PropertiesProperty
from notionizer.functions import notion_object_init_handler
from notionizer.functions import from_plain_text_to_rich_text_array
from notionizer.properties_basic import TitleProperty, DbPropertyObject
from notionizer.object_adt import ImmutableProperty, MutableProperty
from notionizer.properties_db import DbPropertyRelation

from notionizer.query import Query
from notionizer.query import filter
from notionizer.query import T_Filter
from notionizer.query import T_Sorts

from typing import Optional
from typing import Any
from typing import Dict
from typing import List
from typing import Union
from typing import Set


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
                sub_prop_dict[str(sub_prop.id)] = str(sub_prop.type)

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


    def create_database(self,
                        title: str = '',
                        emoji: str = '',
                        cover: str = '',
                        parent: str = '',
                        properties: list = []
                        ) -> Database:

        """

        :param title:
        :param emoji:
        :param cover:
        :param parent:
        :param properties:
        :return: Database

        [Usage]

        from notionizer import Property as Prop
        from notionizer import NumberFormat as NumForm
        from notionizer import OptionColor as OptColor

        db = page.create_database(
            title='DB Title',
            emoji="🎉",
            cover="https://web.image.path/image.jpg",
            properties

            notion.create_database("title", properties = [
                Prop.RichText("text filed"),
                Prop.Number("number", format = NumForm.dollar),
                Prop.Select("select", option = {'opt1': OptColor.blue, 'opt2': OptColor.red}),
                Prop.MultiSelect("multi select", option = {'opt1': OptColor.blue, 'opt2': OptColor.red}),
                ...
                ]
            )
        )

        """

        data: Dict[str, Any] = {'parent': {'type': 'page_id'}, 'properties': {}}
        if parent:
            data['parent']['page_id'] = parent
        else:
            data['parent']['page_id'] = self.id

        if title:
            data['title'] = from_plain_text_to_rich_text_array(title)

        if emoji:
            data['icon'] = {'type': 'emoji'}
            data['icon']['emoji'] = emoji

        if cover:
            data['cover'] = {'type': 'external'}
            data['cover']['external'] = {'url': cover}

        # properties validation
        prop_names = sorted(p.name for p in properties)
        prop_types = sorted(p.prop_type for p in properties)
        assert len(properties) == len(set(prop_names)), f"please check duplicated name of property: {str(prop_names)}"

        # title property should be included.
        if 'title' not in prop_types:
            default_name = 'Name'
            unused_name = default_name
            index = 0
            while unused_name in prop_names:
                index += 1
                unused_name = default_name + str(index).zfill(2)

            data['properties'][unused_name] = {"title": {}}

        for p in properties:
            data['properties'][p.name] = {p.prop_type: {}}

            for opt in p.arguments.keys():
                if opt == 'options':
                    data['properties'][p.name][p.prop_type]['options'] = []
                    for name, color in p.arguments[opt].items():
                        data['properties'][p.name][p.prop_type]['options'].append({'name': name, 'color': color})
                else:
                    data['properties'][p.name][p.prop_type][opt] = p.arguments[opt]

        db_object: Database = Database(*self._request.post('v1/databases/', data))
        return db_object


class OptionColor:
    """
    Enum using for Select and Multi-Select
    """
    default = 'default'
    gray = 'gray'
    brown = 'brown'
    orange = 'orange'
    yellow = 'yellow'
    green = 'green'
    blue = 'blue'
    purple = 'purple'
    pink = 'pink'
    red = 'red'


class NumberFormat:
    """
    Enum using for format of Number
    """
    number = 'number'
    number_with_commas = 'number_with_commas'
    percent = 'percent'
    dollar = 'dollar'
    canadian_dollar = 'canadian_dollar'
    euro = 'euro'
    pound = 'pound'
    yen = 'yen'
    ruble = 'ruble'
    rupee = 'rupee'
    won = 'won'
    yuan = 'yuan'
    real = 'real'
    lira = 'lira'
    rupiah = 'rupiah'
    franc = 'franc'
    hong_kong_dollar = 'hong_kong_dollar'
    new_zealand_dollar = 'new_zealand_dollar'
    krona = 'krona'
    norwegian_krone = 'norwegian_krone'
    mexican_peso = 'mexican_peso'
    rand = 'rand'
    new_taiwan_dollar = 'new_taiwan_dollar'
    danish_krone = 'danish_krone'
    zloty = 'zloty'
    baht = 'baht'
    forint = 'forint'
    koruna = 'koruna'
    shekel = 'shekel'
    chilean_peso = 'chilean_peso'
    philippine_peso = 'philippine_peso'
    dirham = 'dirham'
    colombian_peso = 'colombian_peso'
    riyal = 'riyal'
    ringgit = 'ringgit'
    leu = 'leu'
    argentine_peso = 'argentine_peso'
    uruguayan_peso = 'uruguayan_peso'


class RollupFunction:
    """
    Enum using for rollup funtion parameter
    """

    count = "count"
    count_values = "count_values"
    empty = "empty"
    not_empty = "not_empty"
    unique = "unique"
    show_unique = "show_unique"
    percent_empty = "percent_empty"
    percent_not_empty = "percent_not_empty"
    sum = "sum"
    average = "average"
    median = "median"
    min = "min"
    max = "max"
    range = "range"
    earliest_date = "earliest_date"
    latest_date = "latest_date"
    date_range = "date_range"
    checked = "checked"
    unchecked = "unchecked"
    percent_checked = "percent_checked"
    percent_unchecked = "percent_unchecked"
    count_per_group = "count_per_group"
    percent_per_group = "percent_per_group"
    show_original = "show_original"


class Property:
    """
    A group of property types defined for database creating.

    [Usage]

    from notionizer import Property as Prop
    notion.create_database("title", properties = [Prop.Checkbox("prop. name"), ...])
    """

    class Title:
        def __init__(self, name):

            self.name = name
            self.prop_type = 'title'
            self.arguments = {}

    class RichText:
        def __init__(self, name):

            self.name = name
            self.prop_type = 'rich_text'
            self.arguments = {}

    class Number:
        def __init__(self, name, format=''):
            """

            :param name:
            :param format:

            [Usage]
            from notionizer import NumberFormat as NumForm
            notion.create_database("title", properties = [Prop.Number("number", format = NumForm.dollar), ...])
            """
            self.name = name
            self.prop_type = 'number'
            self.arguments = {}

            if format:
                self.arguments['format'] = format

    class Select:
        def __init__(self, name, options={}):
            """

            :param name:
            :param options: dictionary

            [Usage]

            from notionizer import OptionColor as OptColor

            notion.create_database("title", properties = [
                Prop.Select(
                    "prop. name",
                    options={'option name': OptColor.red}
                ), ...
                ]
            )
            """
            self.name = name
            self.prop_type = 'select'
            self.arguments = {}

            if options:
                self.arguments['options'] = options

    class MultiSelect:
        def __init__(self, name, options={}):
            """
            :param name:
            :param options: dictionary

            [Usage]

            from notionizer import OptionColor as OptColor
            notion.create_database("title", properties = [
                Prop.MultiSelect(
                    "prop. name",
                    options={'option name': OptColor.red}
                ), ...
                ]
            )
            """
            self.name = name
            self.prop_type = 'multi_select'
            self.arguments = {}

            if options:
                self.arguments['options'] = options

    class Date:
        def __init__(self, name):

            self.name = name
            self.prop_type = 'date'
            self.arguments = {}

    class People:
        def __init__(self, name):

            self.name = name
            self.prop_type = 'people'
            self.arguments = {}

    class Files:
        def __init__(self, name):

            self.name = name
            self.prop_type = 'files'
            self.arguments = {}

    class Checkbox:
        def __init__(self, name):

            self.name = name
            self.prop_type = 'checkbox'
            self.arguments = {}

    class Url:
        def __init__(self, name):

            self.name = name
            self.prop_type = 'url'
            self.arguments = {}

    class Email:
        def __init__(self, name):

            self.name = name
            self.prop_type = 'email'
            self.arguments = {}

    class PhoneNumber:
        def __init__(self, name):

            self.name = name
            self.prop_type = 'phone_number'
            self.arguments = {}

    class Formula:
        def __init__(self, name):

            self.name = name
            self.prop_type = 'formula'
            self.arguments = {}

    class Relation:
        def __init__(self, name, database_id):
            """

            :param name:
            :param database_id: UUID(str)

            [Usage]
            notion.create_database("title", properties = [Prop.Relation("relation", "668d797c-76fa-4934-9b05-ad288df2d136"), ...])
            """
            self.name = name
            self.prop_type = 'relation'
            self.arguments = {}
            self.arguments['database_id'] = database_id

    class Rollup:
        def __init__(self, name, rollup_property_name, relation_property_name, function):
            """

            :param name:
            :param rollup_property_name: property name from relation(str)
            :param relation_property_name: relation property name (str)
            :param function: count_all, count_values, count_unique_values, count_empty, count_not_empty, percent_empty, percent_not_empty, sum, average, median, min, max, range, show_original (str)

            [Usage]


            from notionizer import RollupFunction as RFunc
            notion.create_database("title", properties = [
                Prop.Rollup(
                    "rollup",
                    rollup_property_name = "name",
                    relation_property_name = "Meals",
                    function = RFunc.count,
                    ), ...
                ])
            """
            self.name = name
            self.prop_type = 'rollup'
            self.arguments = {}
            self.arguments['rollup_property_name'] = rollup_property_name
            self.arguments['relation_property_name'] = relation_property_name
            self.arguments['function'] = function

