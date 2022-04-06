from notion_api.object_adt import _DictionaryObject, _ListObject, ImmutableProperty
from notion_api.exception import NotionApiPropertyException

_log = __import__('logging').getLogger(__name__)


def _pdir(obj, level='public'):
    attr_list = dir(obj)
    if level == 'hide':
        attr_list = [a for a in attr_list if a[:2] != '__']
    elif level == 'public':
        attr_list = [a for a in attr_list if a[0] != '_']
    return attr_list


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
        obj = RichTextProperty(cls, key, mutable=True)
        # _log.debug(f"rich_text, {cls}, {key}: {value}")
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
        _log.debug(f"{cls}")
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


class ObjectProperty(ImmutableProperty):
    """
    ObjectProperty which inherits 'ImmutableProperty'.
    """

    def __set__(self, owner, value: dict):
        obj = _DictionaryObject(self.public_name, owner, value)
        super().__set__(owner, obj)


class ArrayProperty(ImmutableProperty):
    """
    ArrayProperty which inherits 'ImmutableProperty'.
    """

    def __init__(self, owner=None, name='', mutable=False):
        self.mutable = mutable
        super().__init__(owner=owner, name=name)

    def __set__(self, owner, value: dict):
        # def __init__(self, name, owner, data: list=None, mutable=False):

        obj = _ListObject(self.public_name, owner, value, mutable=self.mutable)

        super().__set__(owner, obj)


class RichTextProperty(ArrayProperty):
    pass






