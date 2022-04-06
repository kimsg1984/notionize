
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from notion_api.object_basic import _NotionObject, _ListObject, _from_rich_text_array_to_plain_text


_log = __import__('logging').getLogger(__name__)


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


