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
from collections import UserDict as _UserDict
from collections.abc import MutableSequence as _MutableSequence

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
        if 'key' not in kwargs:
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

    if type(value) in [str, bool, None, int, float]:
        setattr(cls, key, ImmutableProperty(cls, key))

    elif type(value) == dict:
        dict_obj = _DictionaryObject(key, cls)
        setattr(cls, key, dict_obj)

    elif type(value) == list:
        list_obj = _ListObject(key, cls)
        return list_obj
    else:
        setattr(cls, key, value)


def _get_proper_object(key, value: object, parent):
    """
    check the type of object and return with some wrapper if it needed.

    - primitives(str, int, float, bool, None): return  'raw object'.
    - dictionary -> return as '_DictionaryImmutableObject'
    - list -> return as '_ListImmutableObject'

    :param value:
    :return:
    """
    # _log.debug(f"key, value: object, parent, {key}, {value}, {parent}")
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
        dict_obj = _DictionaryObject(key, parent, data=value)
        return dict_obj
    elif type(value) == list:
        list_obj = _ListObject(key, parent, data=value)
        return list_obj
    else:
        return value


def _from_rich_text_array_to_plain_text(array):
    return ''.join([e['plain_text'].replace(u'\xa0', u'') for e in array])


def _from_plain_text_to_rich_text_array(string):
    return [{"text": {"content": string}, 'plain_text':string}]


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
        # _log.debug(" .join((map(str, '__set_name__(self, owner, name)', self, owner, name))))
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
        # TODO: update
        _log.debug(" ".join(map(str, ('udate: self, obj, value', self, obj, value))))
        obj._update(self.public_name, value)


class _ListObject(_MutableSequence):

    def __init__(self, name, owner, data: list=None, mutable=False):
        self.name = name
        self.data = list()
        self._parent = owner
        self._mutable = mutable
        if data:
            self.__set__(owner, data)

    def __delitem__(self, index):
        del self.data[index]

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)

    def __setitem__(self, index, value):
        assert len(self.data) <= index, 'IndexError: list assignment index out of range'
        self.data[index] = value

    def insert(self, index, value):
        assert len(self.data) == index, 'Insert Event does not permit'
        self.data.append(value)

    def __set__(self, owner, value: list):

        assert type(value) == list

        for e in value:
            self.data.append(_get_proper_object(self.name, e, self))

    def __str__(self):
        return f"<'{self.name}' list property: {str(self.data)}>"


class _DictionaryObject(_UserDict):
    """
    '_DictionaryObject' which used for 'Key-Value' pettern. Imutable is 'default'.
    """

    def __init__(self, name, owner, data: dict=None, mutable=False):
        """
        Initilize '_DictionaryObject'.

        :param name: str (property name)
        :param owner: object (other name is parent)
        :param data: if it assigned, object doesn't need 'additianl assigning event'.
        :param mutable: bool (default: False)
        """
        # _log.debug(f"_DictionaryObject '{name}', data: {bool(data)}")

        self.name = name
        self.data = dict()
        self._parent = owner
        self._mutable = mutable
        if data:
            self.__set__(owner, data)

    # def __str__(self):
    #     content = ''
    #     for k, v in self.data.items():
    #         if 30 < len(content):
    #             content += '...'
    #             break
    #         flake = ''
    #         if content:
    #             flake += ', '
    #
    #         flake += f"'{k}'"
    #         content += flake
    #     return f'<{self.name}: {content}>'

    def __repr__(self):
        content = ''
        # keys = ", ".join(f"'{k}'" for k in self.data.keys())
        # return f'<{self.name}(dict_type): {keys}>'
        return f'<DictionaryObject({self.name}) at {hex(id(self))}>'

    def __set__(self, owner, value: dict):
        for k, v in value.items():
            self.__setitem__(k, _get_proper_object(k, v, self))

    # Implement MutableMapping method
    def __setitem__(self, key, value):
        if key.lower() == 'email':
            _log.debug(f"{self}(parent:{self._parent}), '{key}':'{value}', attr: {key in self.data}")

        if key not in self.data:
            self.data[key] = value
        elif self._mutable:
            self.data[key] = value
            # TODO: update event.
        else:
            raise NotionApiPropertyException('Immutable property could not be assigned')

    def __delitem__(self, key):
        if self._mutable:
            del self.data[key]
            # TODO: remove update event.
        else:
            raise NotionApiPropertyException('Immutable property could not be assigned')

    def __getitem__(self, key):
        # _log.debug(f'{self.name} {key}')
        return self.data[key]

    def keys(self):
        return self.data.keys()


class _NotionObject(object):
    """
    '_NotionObject' which set properties as 'descriptor' or 'specific object' and assigns value.
    """

    def __new__(cls, data):
        """
        construct '_NotionObject' class.

        before assign the object and property, '__new__' method set the proper descriptors.
        :param data:
        """
        _log.debug(f'_NotionObject: {cls}')

        for k, v in data.items():
            if k not in dir(cls):
                _set_proper_descriptor(cls, k, v)

        super_cls = super(_NotionObject, cls)
        notion_ins = super_cls.__new__(cls)

        return notion_ins

    def __init__(self, data, *args):
        """
        assign object and property to instance.
        :param data:
        """
        _log.debug(" ".join(map(str, ('_NotionObject', self))))

        # value assignment event
        for k, v in data.items():
            # setattr(self, k, _get_proper_object(k, v, self))
            setattr(self, k, v)
        _log.debug(f"_NotionObject [DONE], '{self}'")


class _NotionBasicObject(_NotionObject):
    """
    '_NotionBasicObject' for Database, Page and Block.
    """
    _instances = {}

    def __new__(cls, request, data, key: str=None):
        """
        construct '_NotionBasicObject' class.

        check 'key' value and if instance is exist, reuse instance with renewed namespace.
        :param request:
        :param data:
        :param key:
        """
        _log.debug(" ".join(map(str, ('_NotionBasicObject:', cls))))
        # instance = super(_NotionBasicObject, cls).__new__(cls, data)
        instance = super(_NotionBasicObject, cls).__new__(cls, data)

        if key:
            org_namespace = dict(_NotionBasicObject._instances[key].__dict__)

            # instance.__init__(data)

            _NotionBasicObject._instances[key].__dict__ = instance.__dict__
            for k in set(org_namespace) - set(instance.__dict__):
                instance.__dict__[k] = org_namespace[k]

        else:
            key = data['id']

            _NotionBasicObject._instances[key] = instance

        return instance

    def __init__(self, request, data):
        _log.debug(" ".join(map(str, ('_NotionBasicObject:', self))))
        super().__init__(data)

    def _update(self, property_name, contents):
        url = self._api_url + self.id
        request, data = self._request.patch(url, {property_name: contents})
        # update property of object using 'id' value.
        type(self)(request, data, key=data['id'])


# def _set_object(ins: _NotionObject(), attr_name: str, value: object):
#     """
#     check
#     :param ins: instance of '_NotionObject'
#     :param attr_name: attribute name
#     :param value: value to be assigned as 'attr_name'
#     :return: None
#     """
#     # _get_proper_object
#     # setattr(self, k, _get_proper_object(k, v, self))

class Page:
    pass


class PropertiesProperty(_DictionaryObject):
    """
    'PropertiesProperty' for 'Database' and 'Page'.
    """
    def __new__(cls, object_type:str):

        super_cls = super(PropertiesProperty, cls)
        notion_ins = super_cls.__new__(cls)

        _log.debug("PropertiesProperty: " + str(cls))

        return notion_ins

    def __init__(self, object_type: str):
        """
        :param object_type: 'database' or 'page'.
        """
        assert object_type in ['database', 'page']
        self._object_type = object_type
        super().__init__('properties', self)

    def __set__(self, owner, value: dict):
        _log.debug(f'{self}, {owner}')
        for k, v in value.items():
            if self._object_type == 'database':
                property_cls: _PropertyObject = database_properties_mapper.get(v['type'], _PropertyObject)
                property_ins = property_cls(owner, v, object_type=self._object_type)
                self.__setitem__(k, property_ins)

            elif self._object_type == 'page':
                property_cls: _PropertyObject = page_properties_mapper.get(v['type'], _PropertyObject)
                property_ins = property_cls(owner, v, object_type=self._object_type)
                self.__setitem__(k, property_ins)
            else:
                raise NotImplemented(f"'{self._object_type}' object is not implemented")


class _PropertyObject(_NotionObject):
    """
    Basic Object for Data and Page Properties.
    """
    # to find which object is proper, uses '_type_defined' while assigning event.
    _type_defined = ''

    def __new__(cls, obj, data, object_type):
        _log.debug(" ".join(map(str, ('_PropertyObject:', cls._type_defined))))

        ins = super(_PropertyObject, cls)
        ins.__init__(cls, data)

        return ins

    def __init__(self, obj, data, object_type):

        self._object: _NotionObject = obj
        self._object_type = object_type
        _log.debug(" ".join(map(str, ('_PropertyObject:', self._type_defined))))

        # Used for Page.

        # for attr in data:
        #     setattr(self, attr, data[attr])

    def __repr__(self):
        if self._object_type == 'database':
            return f"<'{self.__class__.__name__}': '{self.name}'>"
        elif self._object_type == 'page':
            return f"<'{self.__class__.__name__}: {self._key}'>"

    def _update(self, property_name, data):
        self._object._update('properties', {property_name: data})

    def get_value(self):
        value = getattr(self, self._type_defined)
        if isinstance(value, dict):

            return value['name'].replace(u'\xa0', u'')
        elif isinstance(value, list):
            return [e['name'].replace(u'\xa0', u'') for e in value]
        else:
            return value


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


class DbPropertyEmail(_PropertyObject):
    _type_defined = 'email'



class Database(_NotionBasicObject):

    _api_url = 'v1/databases/'

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
        _log.debug(" ".join(map(str, (type(self).__init__))))
        type(self)(request, data, key=data['id'])


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


