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

from functools import wraps as _wraps
import pprint as _pprint

from notion_api.http_request import HttpRequest
from collections.abc import MutableSequence as _MutableSequence
from collections.abc import MutableMapping as _MutableMapping

import logging

_log = logging.getLogger(__name__)


def _notion_object_init_handler(init_function):
    """
    All notion object having '_update' method should be wrapped by 'this decorator'.
    If '__init__' method is called with  'key' keyword argument, wrapper will not execute it
    because '__new__' method executes with '__init__' to handle namespace.
    """

    @_wraps(init_function)
    def wrapper_function(*args, **kwargs):
        if 'instance_id' not in kwargs:
            return init_function(*args, **kwargs)

    return wrapper_function


def _set_proper_descriptor(cls, key, value):
    """
    check the value type and assign property with proper descriptor.
    (only descriptor, not value)

    :param key:
    :param value:
    :return:
    """
    if type(value) in [str, bool, int, float] or (value is None):
        setattr(cls, key, ImmutableProperty(cls, key))

    elif key == 'rich_text':
        obj = RichTextProperty(cls, key)
        _log.debug(f"rich_text, {value}")
        setattr(cls, key, obj)

    elif type(value) == dict:
        obj = ObjectProperty(cls, key)
        setattr(cls, key, obj)

    elif type(value) == list:
        obj = ArrayProperty(cls, key)
        setattr(cls, key, obj)
    else:
        raise NotionApiPropertyException(f"could not assign proper descriptor: '{type(value)}'")


def _get_proper_object(key, value: object, parent):
    """
    check the type of object and return with some wrapper if it needed.

    - primitives(str, int, float, bool, None): return  'raw object'.
    - dictionary -> return as '_DictionaryImmutableObject'
    - list -> return as '_ListImmutableObject'

    :param value:
    :return:
    """
    # check parent has descriptor.
    if hasattr(parent, key):
        try:
            getattr(parent, key)
        except NotionApiPropertyUnassignedException:
            return value

    # parent has 'no descriptor' or has and already 'assigned own value'.
    if type(value) in [str, int, float, bool, None]:
        return value

    elif type(value) == dict:
        # _log.debug(f"key, value: object, parent: {key}, {value}, {parent}")
        dict_obj = _DictionaryObject(key, parent, data=value)
        return dict_obj
    elif type(value) == list:
        list_obj = _ListObject(key, parent, data=value)
        return list_obj
    else:
        return value


def _from_rich_text_array_to_plain_text(array):
    return ' '.join([e['plain_text'].replace(u'\xa0', u' ') for e in array])


def _from_plain_text_to_rich_text_array(string):
    return [{"text": {"content": string}, 'plain_text': string}]


def _pdir(obj, level='public'):
    attr_list = dir(obj)
    if level == 'hide':
        attr_list = [a for a in attr_list if a[:2] != '__']
    elif level == 'public':
        attr_list = [a for a in attr_list if a[0] != '_']
    return attr_list


class NotionApiPropertyException(Exception):
    pass


class NotionApiPropertyUnassignedException(NotionApiPropertyException):
    pass


class ImmutableProperty:
    """
    Descriptor for property. User assignment is prohibited.
    """

    def __init__(self, owner=None, name=''):
        """
        Initilize ImmutableProperty

        If it assigned with 'setattr()' function, 'owner' and 'name' parameter should be filled.

        :param owner: class
        :param name: string
        """

        if owner and name:
            self.__set_name__(owner, name)

    def __set_name__(self, owner, name):
        self._parent = owner
        self.public_name = name
        self.private_name = '__property_' + name

    def __get__(self, obj, objtype=None):
        if hasattr(self, 'private_name'):
            return getattr(obj, self.private_name)
        else:
            raise NotionApiPropertyUnassignedException('Value is not assigned.')

    def _check_assigned(self, obj):
        return hasattr(obj, self.private_name)

    def __set__(self, obj, value):
        if not self._check_assigned(obj):
            setattr(obj, self.private_name, value)
        else:
            self._update_event(obj, value)

    def _update_event(self, obj, value):
        raise NotionApiPropertyException('Immutable Property could not be assigned')


class MutableProperty(ImmutableProperty):
    """
    Descriptor for property with 'update' event.
    """
    def _update_event(self, obj, value):
        _log.debug(f"udate: self, obj, value {self}, {obj}, {value}")
        obj._update(self.public_name, value)


class _ListObject(_MutableSequence):

    def __init__(self, name, owner, data: list=None, mutable=False):

        self.name = name
        self._mutable = mutable
        self._data = list()

        if data:
            self.__set__(owner, data)

    def __repr__(self):
        return f"<'{self.__class__.__name__}(list_type{'-mutable' if self._mutable else ''})' at {hex(id(self))}>"

    def __get__(self, obj, objtype=None):
        return self

    def __set__(self, owner, value: list):

        assert type(value) == list
        # _log.debug(f"owner, value, {repr(owner)}, {repr(value)}")

        if self._data:
            raise NotionApiPropertyException("values of '_ListObject' already assigned")

        mutable_status = self._mutable

        self._mutable = True
        for e in value:
            # _log.debug(f"{e}")
            proper_obj = _get_proper_object(self.name, e, self)
            self._data.append(proper_obj)

        self._mutable = mutable_status

    def __delitem__(self, index):
        del self._data[index]

    def __getitem__(self, index):
        return self._data[index]

    def __setitem__(self, index, value):
        assert len(self._data) <= index, 'IndexError: list assignment index out of range'
        self._data[index] = value

    def __len__(self):
        return len(self._data)

    def insert(self, index, value):
        assert len(self._data) == index, 'Insert Event does not permit'
        self._data.append(value)


class _DictionaryObject(_MutableMapping):

    """
    '_DictionaryObject Descriptor' which used for 'Key-Value' pettern. Imutable is 'default'.
    """

    def __init__(self, name, owner: '_NotionObject'=None, data: dict=None, mutable=False):
        """
        Initilize '_DictionaryObject'.

        :param name: str (property name)
        :param owner: object (other name is parent)
        :param data: if it assigned, object doesn't need 'additianl assigning event'.
        :param mutable: bool (default: False)
        """

        self.name = name
        self._mutable = mutable

        # descriptor already has '_data' property.
        if not issubclass(type(self), ImmutableProperty):
            self._data = dict()

        if data:
            self.__set__(owner, data)

    def __str__(self):
        return f"<'{self.__class__.__name__}'>"

    def __repr__(self):
        return f"<'{self.__class__.__name__}(dict_type{'-mutable' if self._mutable else ''})' at {hex(id(self))}>"

    def __set__(self, owner, value: dict):
        """
        Allow only first event.

        :param owner:
        :param value:
        :return:
        """
        # _log.debug(f"owner, self.name, {owner}, {self.name}")


        if not self._data:

            mutable_status = self._mutable
            self._mutable = True
            for k, v in value.items():
                self.__setitem__(k, _get_proper_object(k, v, self))
            self._mutable = mutable_status
        else:
            _log.debug(f"{self.name}, {owner}, {self._data}")
            raise NotionApiPropertyException(f"values of '_DictionaryObject' already assigned")

    # Implement MutableMapping method

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __setitem__(self, key, value):

        data: dict = self._data

        if not self._mutable:
            raise NotionApiPropertyException('Immutable property could not be assigned')

        if key not in data:
            # create event
            data[key] = value
        else:
            data[key] = value
            # update event.

    def __delitem__(self, key):

        if self._mutable:
            del self._data[key]
            # remove update event.
        else:
            raise NotionApiPropertyException('Immutable property could not be assigned')

    def __len__(self):
        return len(self._data)

    def keys(self):
        return self._data.keys()


_notion_object_class = {}


def _create_notion_object_class(cls, mro_tuple:tuple=tuple(), namespace:dict={}, force_new=False):
    """
    Create new '_NotionObject' class. Check the name of 'cls'. If not exist,
    create and return. If exists, return already created it.

    :param cls: '_NotionObject' itself or 'subclass' of it.
    :param mro_tuple: if it is defined, replace this.
    :param namespace: if it is defined, replace this.
    :return: new or created class.
    """

    cls_name = cls.__name__
    if (cls_name in _notion_object_class) and (not force_new):
        new_cls = _notion_object_class[cls_name]
    else:
        if not mro_tuple:
            mro_tuple = (cls,)
        # _log.debug(f"{cls_name} {'(force_new)' if force_new else ''}")
        new_cls = type(cls_name, mro_tuple, namespace)
        _notion_object_class[cls_name] = new_cls

    return new_cls


class _NotionObject(object):
    """
    '_NotionObject' which set properties as 'descriptor' or 'specific object' and assigns value.
    """

    def __new__(cls, data, force_new=False):
        """
        construct '_NotionObject' class.

        before assign the object and property, '__new__' method set the proper descriptors.
        :param data:
        """
        # _log.debug(f"{cls}")
        new_cls = _create_notion_object_class(cls, force_new=force_new)

        for k, v in data.items():
            if k not in dir(new_cls):
                _set_proper_descriptor(new_cls, k, v)

        super_cls = super(_NotionObject, new_cls)
        notion_ins = super_cls.__new__(new_cls)

        return notion_ins

    def __init__(self, data, *args):
        """
        assign object and property to instance.
        :param data:
        """

        # value assignment event
        for k, v in data.items():
            setattr(self, k, v)

    def __str__(self):
        return f"<'{self.__class__.__name__}'>"

    def __repr__(self):
        return f"<'{self.__class__.__name__}' at {hex(id(self))}>"


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


class ObjectProperty(ImmutableProperty):
    """
    ObjectProperty which inherits '_NotionObject'.
    """

    def __set__(self, owner, value: dict):
        obj = _DictionaryObject(self.public_name, owner, value)
        super().__set__(owner, obj)


class ArrayProperty(ImmutableProperty):
    """
    ObjectProperty which inherits '_NotionObject'.
    """

    def __set__(self, owner, value: dict):
        obj = _ListObject(self.public_name, owner, value)
        super().__set__(owner, obj)


class RichTextProperty(ArrayProperty):
    def __set__(self, owner, value: dict):
        ImmutableProperty.__set__(self, owner, value)


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


class _PropertyObject(_NotionObject):
    """
    Basic Object for Data and Page Properties.
    """
    # to find which object is proper, uses '_type_defined' while assigning event.
    _type_defined = ''

    def __new__(cls, obj, data, parent_type, force_new=False):
        new_cls = super(_PropertyObject, cls)
        ins = new_cls.__new__(cls, data, force_new=force_new)

        return ins

    def __init__(self, parent: PropertiesProperty, data, parent_type, force_new=False):
        self._parent: PropertiesProperty = parent
        self._parent_type = parent_type
        super().__init__(data)

    def __repr__(self):
        return f"<'{self.__class__.__name__}: {self.name}' at {hex(id(self))}>"


"""
Page Property for Properties
"""


class _PagePropertyObject(_PropertyObject):
    """
    Basic Object for Data and Page Properties.
    """

    # to figure out which object is 'proper', uses '_type_defined' while assigning event.
    _type_defined = ''

    def _update(self, property_name, data):
        self._parent._update(self.name, {property_name: data})

    def get_value(self):

        value = getattr(self, self.type)
        if isinstance(value, dict):
            return value['name'].replace(u'\xa0', u' ')
        elif isinstance(value, (list, _ListObject)):
            return tuple([e['name'].replace(u'\xa0', u' ') for e in value])
        else:
            return value


class PagePropertyPhoneNumber(_PagePropertyObject):
    """
    'PagePropertyPhoneNumber'
    """
    _type_defined = 'phone_number'
    phone_number = MutableProperty()


class PagePropertySelect(_PagePropertyObject):
    """
    'PagePropertySelect'
    """
    _type_defined = 'select'


class PagePropertyCreatedTime(_PagePropertyObject):
    """
    'PagePropertyCreatedTime'
    """
    _type_defined = 'created_time'


class PagePropertyCreatedBy(_PagePropertyObject):
    """
    'PagePropertyCreatedBy'
    """
    _type_defined = 'created_by'


class PagePropertyRollup(_PagePropertyObject):
    """
    'PagePropertyRollup'
    """
    _type_defined = 'rollup'


class PagePropertyPeople(_PagePropertyObject):
    """
    'PagePropertyPeople'
    """
    _type_defined = 'people'


class PagePropertyMultiSelect(_PagePropertyObject):
    """
    'PagePropertyMultiSelect'
    """
    _type_defined = 'multi_select'


class PagePropertyNumber(_PagePropertyObject):
    """
    'PagePropertyNumber'
    """
    _type_defined = 'number'
    number = MutableProperty()


class PagePropertyLastEditedBy(_PagePropertyObject):
    """
    'PagePropertyLastEditedBy'
    """
    _type_defined = 'last_edited_by'


class PagePropertyCheckbox(_PagePropertyObject):
    """
    'PagePropertyCheckbox'
    """
    _type_defined = 'checkbox'
    checkbox = MutableProperty()


class PagePropertyEmail(_PagePropertyObject):
    """
    'PagePropertyEmail'
    """
    _type_defined = 'email'
    email = MutableProperty()


class PagePropertyRichText(_PagePropertyObject):
    """
    'PagePropertyRichText'
    """
    _type_defined = 'rich_text'

    def get_value(self):
        """
        parse 'rich_text' to plain 'string' and return
        """
        return _from_rich_text_array_to_plain_text(self.rich_text)


class PagePropertyUrl(_PagePropertyObject):
    """
    'PagePropertyUrl'
    """
    _type_defined = 'url'
    url = MutableProperty()


class PagePropertyLastEditedTime(_PagePropertyObject):
    """
    'PagePropertyLastEditedTime'
    """
    _type_defined = 'last_edited_time'


class PagePropertyFormula(_PagePropertyObject):
    """
    'PagePropertyFormula'
    """
    _type_defined = 'formula'


class PagePropertyRelation(_PagePropertyObject):
    """
    'PagePropertyRelation'
    """
    _type_defined = 'relation'


class PagePropertyDate(_PagePropertyObject):
    """
    'PagePropertyDate'
    """
    _type_defined = 'date'


class PagePropertyFiles(_PagePropertyObject):
    """
    'PagePropertyFiles'
    """
    _type_defined = 'files'


"""
Database Property for Properties
"""


class _DbPropertyObject(_PropertyObject):
    """
    Basic Object for Data and Page Properties.
    """
    # to find which object is proper, uses '_type_defined' while assigning event.
    _type_defined = ''

    name = MutableProperty()
    type = MutableProperty()

    def _update(self, property_name, data):
        if property_name == 'type':
            property_type = data
            self._parent._update(self.name, {property_name: property_type, property_type: {}})
        else:
            self._parent._update(self.name, {property_name: data})


class DbPropertyEmail(_DbPropertyObject):
    _type_defined = 'email'


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
        self._request = request

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


database_properties_mapper = dict()
page_properties_mapper = dict()

for key in dir():
    db_keyword = 'DbProperty'
    if key[:len(db_keyword)] == db_keyword:
        property_cls: _DbPropertyObject = globals()[key]
        database_properties_mapper[property_cls._type_defined] = property_cls

    page_keyword = 'PageProperty'
    if key[:len(page_keyword)] == page_keyword:
        property_cls: _PagePropertyObject = globals()[key]
        page_properties_mapper[property_cls._type_defined] = property_cls


