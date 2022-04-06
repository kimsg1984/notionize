from notion_api.functions import _from_rich_text_array_to_plain_text, _from_plain_text_to_rich_text_array

# from notion_api.objects import _log
from notion_api.object_adt import MutableProperty, _ListObject
from notion_api.object_basic import _NotionObject

_log = __import__('logging').getLogger(__name__)


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

    def __init__(self, parent: 'PropertiesProperty', data, parent_type, force_new=False):
        self._parent: 'PropertiesProperty' = parent
        self._parent_type = parent_type
        super().__init__(data)

    def __repr__(self):
        return f"<'{self.__class__.__name__}: {self.name}' at {hex(id(self))}>"


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