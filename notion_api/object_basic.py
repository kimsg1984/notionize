

from functools import wraps as _wraps
from typing import MutableSequence as _MutableSequence, MutableMapping as _MutableMapping
from notion_api.properties import ImmutableProperty, NotionApiPropertyException, NotionApiPropertyUnassignedException

_log = __import__('logging').getLogger(__name__)


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

    # Implement MutableMapping method

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


