from notion_api.functions import _from_rich_text_array_to_plain_text
from notion_api.object_adt import MutableProperty
from notion_api.properties_basic import _PagePropertyObject


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