from notion_api.functions import from_rich_text_array_to_plain_text, from_plain_text_to_rich_text_array, pdir

from notion_api.object_adt import MutableProperty, ListObject
from notion_api.object_basic import NotionObject

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
        return from_rich_text_array_to_plain_text(getattr(obj, self.private_name))

    def __set__(self, obj, value):
        if type(value) == str:
            value = from_plain_text_to_rich_text_array(value)

        super().__set__(obj, value)


class _PropertyObject(NotionObject):
    """
    Basic Object for Data and Page Properties.
    """
    # to find which object is proper, uses '_type_defined' while assigning event.
    _type_defined = ''

    def __new__(cls, obj, data, parent_type, name:str, force_new=False):
        new_cls = super(_PropertyObject, cls)
        ins = new_cls.__new__(cls, data, force_new=force_new)

        return ins

    def __init__(self, parent: 'PropertiesProperty', data, parent_type, name: str, force_new=False):
        self._parent: 'PropertiesProperty' = parent
        self._parent_type = parent_type

        # page properties don't have 'name' property. This method assign '_name' property manually.
        self._name = name
        super().__init__(data)


class PagePropertyObject(_PropertyObject):
    """
    Basic Object for Data and Page Properties.
    """

    # to figure out which object is 'proper', uses '_type_defined' while assigning event.
    _type_defined = ''

    def __repr__(self):
        # return f"<'{self.__class__.__name__}:' at {hex(id(self))}>"
        return f"<'{self.__class__.__name__}: {self._name}' at {hex(id(self))}>"

    def _update(self, property_name, data):
        self._parent._update(self.name, {property_name: data})

    def get_value(self):

        value = getattr(self, self.type)

        if hasattr(value, 'keys'):
            if 'name' in value:
                return value['name'].replace(u'\xa0', u' ')
            else:
                _log.info(f"{self}, {self.type}, {value.keys()}")
                return value

        elif isinstance(value, (list, ListObject)):
            return tuple([e['name'].replace(u'\xa0', u' ') for e in value])
        else:
            return value


class DbPropertyObject(_PropertyObject):
    """
    Basic Object for Data and Page Properties.
    """
    # to find which object is proper, uses '_type_defined' while assigning event.
    _type_defined = ''
    _mutable = False

    name = MutableProperty()
    type = MutableProperty()
    _input_validation = tuple()

    def _update(self, property_name, data):
        if property_name == 'type':
            property_type = data
            self._parent._update(self.name, {property_name: property_type, property_type: {}})
        else:
            self._parent._update(self.name, {property_name: data})

    def _convert_to_update(self, value: any):
        """
        convert value to update object form.

        to make some more specific, 'inheritance' should overide this method.

        ex) some_number_property._convert_to_update(123):
            return {'number': 123}

        :param value: nay of type
        :return: dictionary
        """
        return {self._type_defined: value}

    def __repr__(self):
        return f"<'{self.__class__.__name__}: {self.name}' at {hex(id(self))}>"