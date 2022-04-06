from typing import MutableMapping as _MutableMapping, MutableSequence as _MutableSequence

from notion_api.exception import NotionApiPropertyException, NotionApiPropertyUnassignedException

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
        if name:
            self.public_name = name
            self.private_name = '__property_' + name

        # Dynamic assignment of 'descriptor' does not execute '__set_name__' method, should touch manually.
        if owner and name:
            # _log.debug(f"owner and name, {owner} and {name}")
            self.__set_name__(owner, name)

    def __set_name__(self, owner: object, name: str):
        """

        :param owner: instance of 'parent'
        :param name: property name
        :return:
        """
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
        """

        :param obj:
        :param value:
        :return:
        """

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