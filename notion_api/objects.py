"""
notion objects
"""
from functools import wraps as _wraps
import pprint as _pprint

from notion_api.http_request import HttpRequest
from collections import UserDict as _UserDict


def _from_rich_text_array_to_plain_text(array):
    return ''.join([e['plain_text'].replace(u'\xa0', u'') for e in array])


def _from_plain_text_to_rich_text_array(string):
    return [{"text": {"content": string}, 'plain_text':string}]


def pdir(obj, level='public'):
    attr_list = dir(obj)
    if level == 'hide':
        attr_list = [a for a in attr_list if a[:2] != '__']
    elif level == 'public':
        attr_list = [a for a in attr_list if a[0] != '_']
    return attr_list


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
        self._object = owner

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
            self._update_event(obj, value)

    def _update_event(self, obj, value):
        # TODO: branch Object.

        # print('obj', obj, pdir(obj, 'hide'))
        if issubclass(type(obj), _NotionObject):
            pass
        elif issubclass(type(obj), _PropertyObject):
            pass
        elif issubclass(type(obj), ImmutableProperty):
            pass

        else:
            raise NotionApiPropertyException(f"Unimplmented branch: '{type(obj)}'")

        obj._update(self.public_name, value)
        # raise NotionApiPropertyException('Immutable property could not be assigned')


class MutableProperty(ImmutableProperty):
    """
    Property object for mutable, assigning event with update.
    """

    # def __set__(self, obj, value):
    #
    #     if not self._check_assigned(obj):
    #         setattr(obj, self.private_name, value)
    #     else:
    #         obj._update(self.public_name, value)
    #         # Mutable Property does not need to assign with 'setattr' function. '_update' method will
    #         # generate 'new instance' with 'updated data' and replace the whole namespace of current instance.




""" 
Classes for Page, Database
"""

# https://developers.notion.com/reference/property-object


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


# Property

class _PropertyObject:
    """
    Basic Object for Data Properties.
    """
    # to find which object is proper, uses '_type_defined' while assigning event.
    _type_defined = ''
    id = ImmutableProperty()
    type = ImmutableProperty()

    # after split bewteen DB and Page object, 'key' parameter should be removed.
    def __init__(self, obj, data, object_type, key=''):

        self._object: _NotionObject = obj
        self._object_type = object_type
        # Used for Page.
        self._key = key

        for attr in data:
            setattr(self, attr, data[attr])

    def __repr__(self):
        if self._object_type == 'database':
            return f"<'{self.__class__.__name__}': '{self.name}'>"
        elif self._object_type == 'page':
            return f"<'{self.__class__.__name__}: {self._key}'>"

    def _update(self, property_name, data):
        self._object._update('properties', {property_name: data})

    def get_value(self):
        value =  getattr(self, self._type_defined)
        if isinstance(value, dict):

            return value['name'].replace(u'\xa0', u'')
        elif isinstance(value, list):
            return [e['name'].replace(u'\xa0', u'') for e in value]
        else:
            return value


class PropertyTitle(_PropertyObject):
    _type_defined = 'title'
    title = TitleProperty()


class PropertyText(_PropertyObject):
    _type_defined = 'rich_text'
    rich_text = MutableProperty()

    def get_value(self):
        return _from_rich_text_array_to_plain_text(self.rich_text)


class _DatabaseChildPropertyObject:
    """
    Some property has child property.
    example) number.format
    """
    def _update(self):
        pass


class DatabaseChildPropertyNumberObject(_DatabaseChildPropertyObject):
    format = MutableProperty()


class PropertyNumber(_PropertyObject):
    """
    It has additional property 'number' which has only sub property 'format'.
    available type of format:
        number, number_with_commas, percent, dollar, canadian_dollar, euro, pound, yen, ruble, rupee, won, yuan, real,
        lira, rupiah, franc, hong_kong_dollar, new_zealand_dollar, krona, norwegian_krone, mexican_peso, rand,
        new_taiwan_dollar, danish_krone, zloty, baht, forint, koruna, shekel, chilean_peso, philippine_peso, dirham,
        colombian_peso, riyal, ringgit, leu, argentine_peso, uruguayan_peso.
    """
    _type_defined = 'number'
    number = DatabaseChildPropertyNumberObject()


class DatabaseChildPropertySelectObject(_DatabaseChildPropertyObject):
    name = MutableProperty()
    id = ImmutableProperty()
    color = MutableProperty()


class PropertySelect(_PropertyObject):
    _type_defined = 'select'
    select = DatabaseChildPropertySelectObject()


class PropertyMultiSelect(_PropertyObject):
    _type_defined = 'multi_select'
    """
    in reference (https://developers.notion.com/reference/property-object#multi-select-configuration)
    defined 'options' but actually notions uses 'multi_select'   
    """
    multi_select = MutableProperty()


class PropertyDate(_PropertyObject):
    _type_defined = 'date'
    date = ImmutableProperty()

    def get_value(self):
        content = ''
        if not self.date:
            return content
        if self.date['start']:
            content += self.date['start']
        if self.date['end']:
            content += '~' + self.date['end']
        return content


class PropertyPeople(_PropertyObject):
    _type_defined = 'people'
    people = ImmutableProperty()


class PropertyFile(_PropertyObject):
    _type_defined = 'files'
    files = ImmutableProperty()


class PropertyCheckbox(_PropertyObject):
    _type_defined = 'checkbox'
    checkbox = ImmutableProperty()


class PropertyUrl(_PropertyObject):
    _type_defined = 'url'
    url = ImmutableProperty()


class PropertyEmail(_PropertyObject):
    _type_defined = 'email'
    email = ImmutableProperty()


class PropertyPhoneNumber(_PropertyObject):
    _type_defined = 'phone_number'
    phone_number = ImmutableProperty()


class DatabaseChildPropertyFormulaObject(_DatabaseChildPropertyObject):
    expression = MutableProperty()


class PropertyFormular(_PropertyObject):
    _type_defined = 'formula'
    formula = DatabaseChildPropertyFormulaObject()

    def get_value(self):
        return self.formula[self.formula['type']]

class DatabaseChildPropertyRelationObject(_DatabaseChildPropertyObject):
    database_id = ImmutableProperty()
    synced_property_id = MutableProperty()
    synced_property_name = MutableProperty()


class PropertyRelation(_PropertyObject):
    _type_defined = 'relation'
    relation = DatabaseChildPropertyFormulaObject()


class DatabaseChildPropertyRollupObject(_DatabaseChildPropertyObject):
    relation_property_name = MutableProperty()
    relation_property_id = MutableProperty()
    rollup_property_name = MutableProperty()
    rollup_property_id = MutableProperty()
    function = MutableProperty()


class PropertyRollup(_PropertyObject):
    _type_defined = 'rollup'
    rollup = DatabaseChildPropertyRollupObject()

    def get_value(self):
        return self.rollup['array']


class PropertyCreatedTime(_PropertyObject):
    _type_defined = 'created_time'
    created_time = ImmutableProperty()


class PropertyCreatedBy(_PropertyObject):
    _type_defined = 'created_by'
    created_by = ImmutableProperty()


class PropertyLastEditedTime(_PropertyObject):
    _type_defined = 'last_edited_time'
    last_edited_time = ImmutableProperty()


class PropertyLastEditedBy(_PropertyObject):
    _type_defined = 'last_edited_by'
    last_edited_by = ImmutableProperty()


"""
Database Properties
"""


class _DbPropertyObject:
    name = MutableProperty()
    type = MutableProperty()


class DbPropertyTitle(PropertyTitle, _DbPropertyObject):
    pass


class DbPropertyText(PropertyText, _DbPropertyObject):
    pass


class DbPropertyNumber(PropertyNumber, _DbPropertyObject):
    pass


class DbPropertySelect(PropertySelect, _DbPropertyObject):
    pass


class DbPropertyMultiSelect(PropertyMultiSelect, _DbPropertyObject):
    pass


class DbPropertyDate(PropertyDate, _DbPropertyObject):
    pass


class DbPropertyPeople(PropertyPeople, _DbPropertyObject):
    pass


class DbPropertyFile(PropertyFile, _DbPropertyObject):
    pass


class DbPropertyCheckbox(PropertyCheckbox, _DbPropertyObject):
    pass


class DbPropertyUrl(PropertyUrl, _DbPropertyObject):
    pass


class DbPropertyEmail(PropertyEmail, _DbPropertyObject):
    pass


class DbPropertyPhoneNumber(PropertyPhoneNumber, _DbPropertyObject):
    pass


class DbPropertyFormular(PropertyFormular, _DbPropertyObject):
    pass


class DbPropertyRelation(PropertyRelation, _DbPropertyObject):
    pass


class DbPropertyRollup(PropertyRollup, _DbPropertyObject):
    pass


class DbPropertyCreatedTime(PropertyCreatedTime, _DbPropertyObject):
    pass


class DbPropertyCreatedBy(PropertyCreatedBy, _DbPropertyObject):
    pass


class DbPropertyLastEditedTime(PropertyLastEditedTime, _DbPropertyObject):
    pass


class DbPropertyLastEditedBy(PropertyLastEditedBy, _DbPropertyObject):
    pass


class _DictionaryObject(_UserDict):
    """
    Use for 'Key-Value' pettern: Properties..
    """

    def __init__(self, name):
        self.name = name
        self.data = dict()

    def __str__(self):

        content = ''
        for k, v in self.data.items():
            if 30 < len(content):
                content += '...'
                break
            flake = ''
            if content:
                flake += ', '

            flake += f"'{k}'"
            content += flake

        return f'<{self.name}: {content}>'

    def __repr__(self):
        return f'<{self.name}: \n{_pprint.pformat(self.data)}>'

    # Implement MutableMapping method
    def __setitem__(self, key, value):
        # TODO: update event.
        self.data[key] = value

    def __delitem__(self, key):
        # TODO: remove update event.
        del self.data[key]


class PropertiesProperty(ImmutableProperty):

    def __init__(self, object_type):
        self._object_type = object_type

    def __set__(self, obj, value):
        # TODO: should parse each element to proper object and store

        if not self._check_assigned(obj):

            data = _DictionaryObject(self.__class__.__name__)
            for k, v in value.items():
                if self._object_type == 'database':
                    data[k] = database_properties_mapper[v['type']](obj, v, object_type=self._object_type)

                elif self._object_type == 'page':
                    data[k] = page_properties_mapper[v['type']](obj, v, object_type=self._object_type, key=k)
                else:
                    raise NotImplemented(f"'{self._object_type}' object is not implemented")

            setattr(obj, self.private_name, data)
        else:
            obj._update(self.public_name, value)


# Class for Notion

class _NotionObject(object):
    object = ImmutableProperty()
    id = ImmutableProperty()
    created_time = ImmutableProperty()
    last_edited_time = ImmutableProperty()

    _api_url = 'v1/databases/'

    _instances = {}

    def __new__(cls, request, data, key: str=None):
        instance = super(_NotionObject, cls).__new__(cls)
        if key:
            org_namespace = dict(_NotionObject._instances[key].__dict__)
            # cls.__init__(instance, request, data)
            instance.__init__(request, data)
            _NotionObject._instances[key].__dict__ = instance.__dict__
            for k in set(org_namespace) - set(instance.__dict__):
                instance.__dict__[k] = org_namespace[k]

        else:
            key = data['id']
            _NotionObject._instances[key] = instance

        return instance

    def _update(self, property_name, contents):
        url = self._api_url + self.id
        request, data = self._request.patch(url, {property_name: contents})
        # update property of object using 'id' value.
        type(self)(request, data, key=data['id'])


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


class Database(_NotionObject):
    title = TitleProperty()
    parent = ImmutableProperty()
    url = ImmutableProperty()

    cover = MutableProperty()
    icon = MutableProperty()
    properties = PropertiesProperty(object_type='database')

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

    def _update(self, property_name, contents):
        url = self._api_url + self.id
        request, data = self._request.patch(url, {property_name: contents})
        # update property of object using 'id' value.
        type(self)(request, data, key=data['id'])

    def __repr__(self):
        return f"<Database '{self.title}' at '{self.id}'>"

    def create(self):
        pass

    def get_tuples(self, queried_page_iterator: QueriedPageIterator, columns_select: list=[], header=True):
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


class Page(_NotionObject):
    """
    Page Object
    """

    archived = ImmutableProperty()

    parent = ImmutableProperty()
    url = ImmutableProperty()

    cover = MutableProperty()
    icon = MutableProperty()
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

        for attr in data:
            setattr(self, attr, data[attr])

    def __repr__(self):
        return f"<Page at '{self.id}'>"

    def get_properties(self) -> dict:
        """
        return value of properties simply
        :return: {'key' : value, ...}
        """
        result = dict()
        for k, v in self.properties.items():
            v: _PropertyObject
            result[k] = v.get_value()

        return result


# Else


# database = ['object', 'id', 'cover', 'icon', 'created_time', 'last_edited_time', 'title', 'properties', 'parent', 'url']
# page = ['archived', 'cover', 'created_time', 'icon', 'id', 'last_edited_time', 'object', 'parent', 'properties', 'url']
# block =
database_properties_mapper = dict()
page_properties_mapper = dict()


for key in dir():
    db_keyword = 'DbProperty'
    if key[:len(db_keyword)] == db_keyword:
        property_cls: _PropertyObject = globals()[key]
        database_properties_mapper[property_cls._type_defined] = property_cls

    page_keyword = 'Property'
    if key[:len(page_keyword)] == page_keyword:
        property_cls: _PropertyObject = globals()[key]
        page_properties_mapper[property_cls._type_defined] = property_cls


object_map = {
    'database': Database,
    'page': Page,
}