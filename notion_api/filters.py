"""
database query filter and sorts


:: example ::

from filter import filter
from filter import filter_text

from filter import sorts
from filter import sort_by_timestamp


condition_title = filter_text(filter_text.TYPE_TITLE)
condition_title.contains('Some Title')
db_filter = filter()
db_filter.add_condition(condition_title)


filter_text


sort = sorts()
sort.add(sort_by_timestamp(sorts.LAST_EDITED_TIME))
sort.add(sort_by_property('title', sorts.DESCENDING))


result = database.query(filter=db_filter, sorts=sort)



"""

import abc


"""
    filter: {
      or: [
        {
          property: 'In stock',
          checkbox: {
            equals: true,
          },
        },
        {
          property: 'Cost of next trip',
          number: {
            greater_than_or_equal_to: 2,
          },
        },
      ],
    },
"""


class filter:
    """
    filter collector. All filter object should be collected here.
    """

    OR = 'or'
    AND = 'and'

    def __init__(self, compound: object = OR) -> object:
        """

        Args:
            compound: 'filter.OR' or 'filter.AND' (default: OR)
        """
        self.compound = compound
        self._body = {compound: []}

    def add(self, condition):
        """

        Args:
            condition:

        Returns:

        """

        assert issubclass(type(condition), _FilterConditionABC), 'type: ' + str(type(condition))
        self._body[self.compound].append(dict(condition._body))

        return self

    def clear(self):
        """
        clear conditions to reuse object.

        Returns:

        """
        self._body = {self.compound: []}
        return self


class sorts:

    ASCENDING = 'ascending'
    DESCENDING = 'descending'
    CREATED_TIME = 'created_time'
    LAST_EDITED_TIME = 'last_edited_time'

    def __init__(self):
        """

        Args:
            compound: 'filter.OR' or 'filter.AND'
        """
        self._body = []

    def add(self, sort_obj):
        assert issubclass(sort_obj, _SortObject)
        self._body.append(dict(sort_obj.body))

        return self


class _SortObject:
    pass


class sort_by_timestamp(_SortObject):

    def __init__(self, time_property, direction=sorts.ASCENDING):
        assert time_property in [sorts.CREATED_TIME, sorts.LAST_EDITED_TIME]
        assert direction in [sorts.ASCENDING, sorts.DESCENDING]

        self._body = {'timestamp': time_property, 'direction': direction}


class sort_by_property(_SortObject):

    def __init__(self, property_name, direction=sorts.ASCENDING):
        assert direction in [sorts.ASCENDING, sorts.DESCENDING]

        self._body = {'property': property_name, 'direction': direction}


# filters

class _FilterConditionABC(metaclass=abc.ABCMeta):

    def __init__(self, property_type, property_name):
        self._body = {
            'property': property_name,
            property_type: dict()
        }
        self._property_type = property_type

    def is_empty(self):
        self._body[self._property_type]['is_empty'] = True
        return self

    def is_not_empty(self):
        self._body[self._property_type]['is_not_empty'] = True
        return self


class _FilterConditionEquals(_FilterConditionABC):
    @abc.abstractmethod
    def equals(self, value):
        pass

    def does_not_equal(self, value):
        pass


class _FilterConditionContains(_FilterConditionABC):
    @abc.abstractmethod
    def contains(self, value):
        pass

    def does_not_contain(self, value):
        pass


class filter_text(_FilterConditionEquals,
                  _FilterConditionContains):
    """
    Text Filter Condition

    Args:
        property_type: filter_text.TYPE_$TYPE
                (TITLE, TEXT, RICHTEXT, URL, EMAL, PHONE_NUMBER)
        property_name: $property_name ('TYPE_TITLE' doesn't need 'property_name')


    ftext = filter_text(filter_text.TYPE_TITLE)
    ftext.contains('apple')

    """

    TYPE_TITLE = 'title'
    TYPE_TEXT = 'text'
    TYPE_RICHTEXT = 'rich_text'
    TYPE_URL = 'url'
    TYPE_EMAIL = 'email'
    TYPE_PHONE_NUMBER = 'phone_number'

    def __init__(self, property_type, property_name='title'):
        """
        Text Filter Condition

        Args:
            property_type: filter_text.TYPE_$TYPE
                (TITLE, TEXT, RICHTEXT, URL, EMAL,
                 PHONE_NUMBER)
            property_name: $property_name
                ('TYPE_TITLE' doesn't need 'property_name')


        ftext = filter_text(filter_text.TYPE_TITLE)
        ftext.contains('apple')
        ftext2 = filter_text(filter_text.TYPE_TEXT, 'Column1')
        """

        super().__init__(property_type, property_name)

    def equals(self, string: str):
        """

        Args:
            string: case sensitive
        Returns:

        """
        self._body[self._property_type]['equals'] = string
        return self

    def does_not_equal(self, string: str):
        """

        Args:
            string: case sensitive

        Returns:

        """
        self._body[self._property_type]['does_not_equal'] = string
        return self

    def contains(self, string: str):
        """

        Args:
            string: case sensitive

        Returns:

        """
        self._body[self._property_type]['contains'] = string
        return self

    def does_not_contain(self, string: str):
        """

        Args:
            string: case sensitive

        Returns:

        """
        self._body[self._property_type]['does_not_contain'] = string
        return self

    def starts_with(self, string: str):
        """

        Args:
            string: case sensitive

        Returns:

        """
        self._body[self._property_type]['starts_with'] = string
        return self

    def ends_with(self, string: str):
        """

        Args:
            string: case sensitive

        Returns:

        """
        self._body[self._property_type]['ends_with'] = string
        return self


class filter_number(_FilterConditionEquals):

    def __init__(self, property_name: str):
        """
        initialize
        Args:
            property_name:
        """

        super().__init__('number', property_name)

    def equals(self, number: int):
        """

        Args:
            number:

        Returns:

        """
        self._body[self._property_type]['equals'] = number
        return self

    def does_not_equal(self, number: int):
        """

        Args:
            number:

        Returns:

        """
        self._body[self._property_type]['does_not_equal'] = number
        return self

    def greater_than(self, number: int):
        """

        Args:
            number:

        Returns:

        """
        self._body[self._property_type]['greater_than'] = number
        return self

    def less_than(self, number: int):
        """

        Args:
            number:

        Returns:

        """
        self._body[self._property_type]['less_than'] = number
        return self

    def greater_than_or_equal_to(self, number: int):
        """

        Args:
            number:

        Returns:

        """
        self._body[self._property_type]['greater_than_or_equal_to'] = number
        return self

    def less_than_or_equal_to(self, number: int):
        """

        Args:
            number:

        Returns:

        """
        self._body[self._property_type]['less_than_or_equal_to'] = number
        return self


class filter_checkbox(_FilterConditionEquals):

    def __init__(self, property_name: str):
        """
        initialize
        Args:
            property_name:
        """

        super().__init__('checkbox', property_name)

    def equals(self, boolean: bool):
        """

        Args:
            boolean: bool

        Returns:

        """
        self._body[self._property_type]['equals'] = boolean
        return self

    def does_not_equal(self, boolean: bool):
        """

        Args:
            boolean: bool

        Returns:

        """
        self._body[self._property_type]['does_not_equal'] = boolean
        return self

