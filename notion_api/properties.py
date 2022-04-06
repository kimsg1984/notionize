from notion_api.objects import RichTextProperty, ObjectProperty, ArrayProperty

_log = __import__('logging').getLogger(__name__)


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


