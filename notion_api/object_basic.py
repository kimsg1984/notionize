from functools import wraps as _wraps
from typing import MutableMapping as _MutableMapping, MutableSequence as _MutableSequence

from notion_api.properties import ImmutableProperty, NotionApiPropertyException, NotionApiPropertyUnassignedException

_log = __import__('logging').getLogger(__name__)



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


_notion_object_class = {}


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