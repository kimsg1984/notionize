from notion_api.properties_basic import _DbPropertyObject
from notion_api.functions import _from_plain_text_to_rich_text_array

class DbPropertyLastEditedTime(_DbPropertyObject):
    """
    'DbPropertyLastEditedTime'
    """
    _type_defined = 'last_edited_time'
    _mutable = False


class DbPropertyCreatedBy(_DbPropertyObject):
    """
    'DbPropertyCreatedBy'
    """
    _type_defined = 'created_by'
    _mutable = False


class DbPropertyCreatedTime(_DbPropertyObject):
    """
    'DbPropertyCreatedTime'
    """
    _type_defined = 'created_time'
    _mutable = False


class DbPropertyLastEditedBy(_DbPropertyObject):
    """
    'DbPropertyLastEditedBy'
    """
    _type_defined = 'last_edited_by'
    _mutable = False


class DbPropertyRollup(_DbPropertyObject):
    """
    'DbPropertyRollup'
    """
    _type_defined = 'rollup'
    _mutable = False


class DbPropertyPeople(_DbPropertyObject):
    """
    'DbPropertyPeople'
    """
    _type_defined = 'people'
    _mutable = True
    _input_validation = (list, )


class DbPropertyCheckbox(_DbPropertyObject):
    """
    'DbPropertyCheckbox'
    """
    _type_defined = 'checkbox'
    _mutable = True
    _input_validation = (bool, )


class DbPropertyRelation(_DbPropertyObject):
    """
    'DbPropertyRelation'
    """
    _type_defined = 'relation'
    _mutable = False


class DbPropertyFormula(_DbPropertyObject):
    """
    'DbPropertyFormula'
    """
    _type_defined = 'formula'
    _mutable = False


class DbPropertyUrl(_DbPropertyObject):
    """
    'DbPropertyUrl'
    """
    _type_defined = 'url'
    _mutable = True
    _input_validation = (str, )


class DbPropertyEmail(_DbPropertyObject):
    """
    'DbPropertyEmail'
    """
    _type_defined = 'email'
    _mutable = True
    _input_validation = (str, )


class DbPropertyPhoneNumber(_DbPropertyObject):
    """
    'DbPropertyPhoneNumber'
    """
    _type_defined = 'phone_number'
    _mutable = True
    _input_validation = (str, )


class DbPropertyFiles(_DbPropertyObject):
    """
    'DbPropertyFiles'
    """
    _type_defined = 'files'
    _mutable = True
    _input_validation = (list, )


class DbPropertyDate(_DbPropertyObject):
    """
    'DbPropertyDate'
    """
    _type_defined = 'date'
    _mutable = True
    _input_validation = (dict, )


class DbPropertyMultiSelect(_DbPropertyObject):
    """
    'DbPropertyMultiSelect'
    """
    _type_defined = 'multi_select'
    _mutable = True
    _input_validation = (list, )


class DbPropertySelect(_DbPropertyObject):
    """
    'DbPropertySelect'
    """
    _type_defined = 'select'
    _mutable = True
    _input_validation = (dict, )


class DbPropertyText(_DbPropertyObject):
    """
    'DbPropertyText'
    """
    _type_defined = 'text'
    _mutable = True
    _input_validation = (str, list)


class DbPropertyTitle(_DbPropertyObject):
    """
    'DbPropertyTitle'
    """
    _type_defined = 'title'
    _mutable = True
    _input_validation = (str, list)

    def _convert_to_update(self, value: str):
        """
        convert value to 'rich_text' update from.

        to make some more specific, 'inheritance' should overide this method.

        ex) some_number_property._convert_to_update(123):
            return {'number': 123}

        :param value: nay of type
        :return: dictionary
        """
        return {'title': _from_plain_text_to_rich_text_array(value)}


class DbPropertyNumber(_DbPropertyObject):
    """
    'DbPropertyNumber'
    """
    _type_defined = 'number'
    _mutable = True
    _input_validation = (int, )


