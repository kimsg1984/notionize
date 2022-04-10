from notion_api.functions import from_rich_text_array_to_plain_text
from notion_api.functions import parse_date_object
from notion_api.object_adt import MutableProperty
from notion_api.properties_basic import PagePropertyObject


def parse_value_object(obj):
    """
    parse value of 'formula' and 'rollup'. 

    """
    obj_type = obj['type']
    value = obj[obj_type]
            
    if obj_type == 'date':
        return parse_date_object(value)

    elif obj_type == 'array':
        return [parse_value_object(e) for e in value]
    
    # 'number', 'string', 'boolean'
    else:
        return value


class PagePropertyPhoneNumber(PagePropertyObject):
    """
    'PagePropertyPhoneNumber'
    """
    _type_defined = 'phone_number'
    phone_number = MutableProperty()


class PagePropertySelect(PagePropertyObject):
    """
    'PagePropertySelect'
    """
    _type_defined = 'select'


class PagePropertyCreatedTime(PagePropertyObject):
    """
    'PagePropertyCreatedTime'
    """
    _type_defined = 'created_time'


class PagePropertyCreatedBy(PagePropertyObject):
    """
    'PagePropertyCreatedBy'
    """
    _type_defined = 'created_by'


class PagePropertyRollup(PagePropertyObject):
    """
    'PagePropertyRollup'
    """
    _type_defined = 'rollup'

    def get_value(self):
        """
        parse 'rollup object'
        """
        return parse_value_object(self.rollup)


class PagePropertyPeople(PagePropertyObject):
    """
    'PagePropertyPeople'
    """
    _type_defined = 'people'


class PagePropertyMultiSelect(PagePropertyObject):
    """
    'PagePropertyMultiSelect'
    """
    _type_defined = 'multi_select'


class PagePropertyNumber(PagePropertyObject):
    """
    'PagePropertyNumber'
    """
    _type_defined = 'number'
    number = MutableProperty()


class PagePropertyLastEditedBy(PagePropertyObject):
    """
    'PagePropertyLastEditedBy'
    """
    _type_defined = 'last_edited_by'


class PagePropertyCheckbox(PagePropertyObject):
    """
    'PagePropertyCheckbox'
    """
    _type_defined = 'checkbox'
    checkbox = MutableProperty()


class PagePropertyEmail(PagePropertyObject):
    """
    'PagePropertyEmail'
    """
    _type_defined = 'email'
    email = MutableProperty()


class PagePropertyRichText(PagePropertyObject):
    """
    'PagePropertyRichText'
    """
    _type_defined = 'rich_text'

    def get_value(self):
        """
        parse 'rich_text' to plain 'string' and return
        """
        return from_rich_text_array_to_plain_text(self.rich_text)


class PagePropertyUrl(PagePropertyObject):
    """
    'PagePropertyUrl'
    """
    _type_defined = 'url'
    url = MutableProperty()


class PagePropertyLastEditedTime(PagePropertyObject):
    """
    'PagePropertyLastEditedTime'
    """
    _type_defined = 'last_edited_time'


class PagePropertyFormula(PagePropertyObject):
    """
    'PagePropertyFormula'
    """
    _type_defined = 'formula'

    def get_value(self):
        """
        parse 'formula object'
        """
        return parse_value_object(self.formula)


class PagePropertyRelation(PagePropertyObject):
    """
    'PagePropertyRelation'
    """
    _type_defined = 'relation'


class PagePropertyDate(PagePropertyObject):
    """
    'PagePropertyDate'
    """
    _type_defined = 'date'

    def get_value(self):
        """
        parse 'date object'
        """
        return parse_date_object(self.date)


class PagePropertyFiles(PagePropertyObject):
    """
    'PagePropertyFiles'
    """
    _type_defined = 'files'


class PagePropertyTitle(PagePropertyObject):
    """
    'PagePropertyTitle'
    """
    _type_defined = 'title'

    def get_value(self):
        """
        parse 'rich_text' to plain 'string' and return
        """
        return from_rich_text_array_to_plain_text(self.title)


