"""
database query filter and sorts


:: example ::

from query import filter
from query import filter_text

from query import sorts
from query import sort_by_timestamp


condition_title = filter_text(filter_text.TYPE_TITLE)
condition_title.contains('Some Title')
db_filter = filter()
db_filter.add_condition(condition_title)


filter_text


sort = sorts()
sort.add(sort_by_timestamp(sorts.LAST_EDITED_TIME))
sort.add(sort_by_property('title', sorts.DESCENDING))


result = database.query(filter=db_filter, sorts=sort)


reference:
    https://developers.notion.com/reference/post-database-query-filter
    https://docs.python.org/3.6/library/ast.html
    https://greentreesnakes.readthedocs.io/en/latest/nodes.html

"""
from typing import Dict, Union, List
from typing import TypeVar
from typing import List
from typing import Type
from typing import Any
from typing import Type
from typing import Union
from typing import Optional
from typing import Generic
from typing import Tuple
from typing import get_type_hints

import copy
import abc
import ast
import _ast
import time

from notionizer import properties_basic
from notionizer.properties_basic import DbPropertyObject
from notionizer.functions import pdir
from notionizer.exception import NotionApiQueoryException

log = __import__('logging').getLogger(__name__)

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

    def __init__(self, bool_op: str = OR) -> None:
        """
        filter object

        Args:
            bool_op: 'filter.OR' or 'filter.AND' (default: OR)

        example:

            from query import filter
            from query import filter_text

            from query import sorts
            from query import sort_by_timestamp


            condition_title = filter_text(filter_text.TYPE_TITLE)
            condition_title.contains('Some Title')
            db_filter = filter()
            db_filter.add(condition_title)
        """
        self.bool_op = bool_op
        self._body: Dict[str, List[FilterConditionABC]] = {bool_op: []}

    def add(self, condition: 'T_Filter') -> 'filter':
        """

        Args:
            condition:

        Returns:

        """

        assert issubclass(type(condition), FilterConditionABC), 'type: ' + str(type(condition))
        compound_obj: List[Any] = self._body[self.__bool_op]
        compound_obj.append(dict(condition.get_body()))
        return self

    def clear(self) -> 'filter':
        """
        clear conditions to reuse object.

        Returns:

        """
        self._body = {self.__bool_op: []}
        return self

    def get_body(self) -> Dict[str, List['FilterConditionABC']]:
        # log.info(self._body)
        return copy.deepcopy(self._body)

    @property
    def bool_op(self) -> str:
        return self.__bool_op

    @bool_op.setter
    def bool_op(self, compound_type: str) -> None:
        assert compound_type in ['or', 'and']
        self.__bool_op = compound_type


class ChangeMroMeta(abc.ABCMeta):
    def __new__(cls, cls_name, cls_bases, cls_dict):
        out_cls = super(ChangeMroMeta, cls).__new__(cls, cls_name, cls_bases, cls_dict)
        out_cls._mro_fixed = tuple()
        out_cls._set_mro = classmethod(cls._set_mro)
        return out_cls

    @staticmethod
    def _set_mro(cls: object, mro: Tuple[object]) -> None:
        default_mro = super(ChangeMroMeta, cls).mro()
        new_mro = list()
        new_mro.append(default_mro[0])  # assign class itself
        for m in mro:
            if m is not default_mro[0]:
                new_mro.append(m)
        for d in default_mro:
            if d not in new_mro:
                new_mro.append(d)

        cls._mro_fixed = tuple(new_mro)
        cls.__bases__ = cls.__bases__ + tuple()

    def mro(cls):

        if hasattr(cls, '_mro_fixed') and cls._mro_fixed:
            mro = tuple(cls._mro_fixed)
        else:
            # default
            mro = super(ChangeMroMeta, cls).mro()
        return mro

class FilterConditionABC(metaclass=ChangeMroMeta):

    def __init__(self, property_name: str, property_type: Optional[str] = '', **kwargs: Dict[str, Any]):
        self._body: Dict[str, Any] = {
            'property': property_name,
            str(property_type): dict()
        }
        self._property_type: str = str(property_type)

    def get_body(self) -> Dict[str, Any]:
        return copy.deepcopy(self._body)

"""
filters
"""


class SortObject:
    _body: Dict[str, Any] = {}

    def get_body(self) -> Dict[str, Any]:
        return copy.deepcopy(self._body)


class FilterConditionEmpty(FilterConditionABC):
    data_type = ''

    def is_empty(self) -> 'FilterConditionEmpty':
        self._body[self._property_type]['is_empty'] = True
        return self

    def is_not_empty(self) -> 'FilterConditionEmpty':
        self._body[self._property_type]['is_not_empty'] = True
        return self


class FilterConditionEquals(FilterConditionABC):
    @abc.abstractmethod
    def equals(self, value: Any) -> Any:
        pass

    @abc.abstractmethod
    def does_not_equal(self, value: Any) -> Any:
        pass


class FilterConditionContains(FilterConditionABC):
    @abc.abstractmethod
    def contains(self, value: Any) -> Any:
        pass

    @abc.abstractmethod
    def does_not_contain(self, value: Any) -> Any:
        pass


class filter_text(FilterConditionEquals,
                  FilterConditionContains,
                  FilterConditionEmpty):
    data_type = 'text'
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

    def __init__(self, property_type: str, property_name: Optional[str] = 'title'):
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

        FilterConditionABC.__init__(self, str(property_name), property_type)

    def equals(self, string: str) -> 'filter_text':
        """
        Args:
            string: case sensitive
        Returns:
        """
        self._body[self._property_type]['equals'] = string
        return self

    def does_not_equal(self, string: str) -> 'filter_text':
        """
        Args:
            string: case sensitive

        Returns:
        """
        self._body[self._property_type]['does_not_equal'] = string
        return self

    def contains(self, string: str) -> 'filter_text':
        """

        Args:
            string: case sensitive

        Returns:

        """
        self._body[self._property_type]['contains'] = string
        return self

    def does_not_contain(self, string: str) -> 'filter_text':
        """

        Args:
            string: case sensitive

        Returns:

        """
        self._body[self._property_type]['does_not_contain'] = string
        return self

    def starts_with(self, string: str) -> 'filter_text':
        """

        Args:
            string: case sensitive

        Returns:

        """
        self._body[self._property_type]['starts_with'] = string
        return self

    def ends_with(self, string: str) -> 'filter_text':
        """
        Args:
            string: case sensitive

        Returns:
        """
        self._body[self._property_type]['ends_with'] = string
        return self


class filter_number(FilterConditionEquals, FilterConditionEmpty):
    data_type = 'number'

    def __init__(self, property_name: str):
        """
        initialize
        Args:
            property_name:
        """
        FilterConditionABC.__init__(self, property_name, property_type='number')

    def equals(self, number: int) -> 'filter_number':
        """

        Args:
            number:

        Returns:

        """
        self._body[self._property_type]['equals'] = number
        return self

    def does_not_equal(self, number: int) -> 'filter_number':
        """

        Args:
            number:

        Returns:

        """
        self._body[self._property_type]['does_not_equal'] = number
        return self

    def greater_than(self, number: int) -> 'filter_number':
        """

        Args:
            number:

        Returns:

        """
        self._body[self._property_type]['greater_than'] = number
        return self

    def less_than(self, number: int) -> 'filter_number':
        """

        Args:
            number:

        Returns:

        """
        self._body[self._property_type]['less_than'] = number
        return self

    def greater_than_or_equal_to(self, number: int) -> 'filter_number':
        """

        Args:
            number:

        Returns:

        """
        self._body[self._property_type]['greater_than_or_equal_to'] = number
        return self

    def less_than_or_equal_to(self, number: int) -> 'filter_number':
        """

        Args:
            number:

        Returns:

        """
        self._body[self._property_type]['less_than_or_equal_to'] = number
        return self


class filter_checkbox(FilterConditionEquals):
    data_type = 'boolean'

    def __init__(self, property_name: str):
        """
        initialize
        Args:
            property_name:
        """

        FilterConditionABC.__init__(self, property_name, property_type='checkbox')

    def equals(self, boolean: bool) -> 'filter_checkbox':
        """

        Args:
            boolean: bool

        Returns:

        """
        self._body[self._property_type]['equals'] = boolean
        return self

    def does_not_equal(self, boolean: bool) -> 'filter_checkbox':
        """

        Args:
            boolean: bool

        Returns:

        """
        self._body[self._property_type]['does_not_equal'] = boolean
        return self


class filter_select(FilterConditionEquals, FilterConditionEmpty):
    data_type = 'select'

    def __init__(self, property_name: str):
        """
        initialize
        Args:
            property_name:
        """

        super().__init__(property_name, property_type='select')

    def equals(self, option: str) -> 'filter_select':
        """

        Args:
            option: str

        Returns:

        """
        self._body[self._property_type]['equals'] = option
        return self

    def does_not_equal(self, option: str) -> 'filter_select':
        """

        Args:
            option: str

        Returns:

        """
        self._body[self._property_type]['does_not_equal'] = option
        return self


class filter_multi_select(FilterConditionContains, FilterConditionEmpty):
    data_type = 'multi_select'

    def __init__(self, property_name: str):
        """
        initialize
        Args:
            property_name:
        """

        super().__init__(property_name, property_type='multi_select')

    def contains(self, option: str) -> 'filter_multi_select':
        """

        Args:
            option: case sensitive

        Returns:

        """
        self._body[self._property_type]['contains'] = option
        return self

    def does_not_contain(self, option: str) -> 'filter_multi_select':
        """

        Args:
            option: case sensitive

        Returns:

        """
        self._body[self._property_type]['does_not_contain'] = option
        return self


class filter_date(FilterConditionEmpty):
    data_type = 'date'

    def __init__(self, property_type: str, property_name: str, timezone: Optional[str] = ''):
        """

        date filter requires 'timezone'. You should tail after 'datetime' like "2021-10-15T12:00:00+09:00" to set the
        specific 'timezone' value. Module set the 'timezone' dynamically. So user doesn't need to set.  But if user want
        to set manually, use 'timezone' parameter or after generating 'filter_date' instance, assign value on 'timezone'
        property.

        :param property_type: 'date', 'created_time', 'last_edited_time'
        :param property_name: $property_name
        :param timezone: Optional[str]. If is not set, module assign it from 'time.timezone' value.
            ex) '09:00', '+03:00', '-02:00'

        [USAGE]
            filter_dt = filter_date(filter_date.TYPE_DATE, 'PropertyName')
            filter_dt.equals("2021-05-10+09:00")

            or

            filter_dt = filter_date(filter_date.TYPE_DATE, 'PropertyName')
            filter_dt.timezone = '+09:00'
            filter_dt.equals("2021-05-10")
        """

        TYPE_DATE = 'date'
        TYPE_CREATED_TIME = 'created_time'
        TYPE_LAST_EDITED_TIME = 'last_edited_time'

        assert property_type in [TYPE_DATE, TYPE_CREATED_TIME, TYPE_LAST_EDITED_TIME], \
            f"'property_type' allows only 'date', 'created_time', and 'last_edited_time'"

        if not timezone:
            timezone = ''
            timezone_int = -int(time.timezone / 60 / 60)
            if timezone_int == 0:
                timezone = '+00:00'
            elif 0 < timezone_int:
                timezone += '+'
                timezone += str(timezone_int).zfill(2) + ':00'
            elif timezone_int < 0:
                timezone += str(timezone_int).zfill(3) + ':00'

        self.timezone = timezone

        """
        'created_time' and 'last_edited_time' is 'Timestamp filter object' which has 'timestamp' property instead
        'property' property.
        {
            "filter": {
                "timestamp": "created_time",
                "created_time": {
                  "past_week": {}
                }
             }
        }
        """
        if property_type in [TYPE_CREATED_TIME, TYPE_LAST_EDITED_TIME]:
            self._body: Dict[str, Any] = {
                'timestamp': property_type,
                property_type: dict()
            }
            self._property_type: str = str(property_type)

        # 'date' property
        else:
            FilterConditionABC.__init__(self, property_name, property_type=property_type)

    @property
    def timezone(self) -> str:
        return self.__time_zone

    @timezone.setter
    def timezone(self, timezone: str) -> None:
        if timezone:
            if timezone[0] in ['+', '-']:
                self.__time_zone = timezone
            else:
                self.__time_zone = '+' + timezone

        # set emtpy timezone
        else:
            self.__time_zone = ''

    def equals(self, datetime: str) -> 'filter_date':
        """
        Args:
            datetime: string(ISO 8601 date.  "2021-05-10"  or "2021-05-10T12:00:00" or "2021-10-15T12:00:00-07:00")
        Returns:

        Usage:
            filter_dt.equals("2021-05-10")
            filter_dt.equals("2021-05-10T12:00:00")
            filter_dt.equals("2021-10-15T12:00:00-07:00")
            filter_dt = filter_date(filter_date.TYPE_TEXT, 'date_column_name', time_zone='+09:00')

        """

        if self.__time_zone and 11 < len(datetime) and datetime[-6] not in ['+', '-']:
            datetime += self.__time_zone

        self._body[self._property_type]['equals'] = datetime
        return self

    def before(self, datetime: str) -> 'filter_date':
        """
        Args:
            datetime: string(ISO 8601 date.  "2021-05-10"  or "2021-05-10T12:00:00" or "2021-10-15T12:00:00-07:00")
        Returns:
        """
        if self.__time_zone and len(datetime) < 10 and datetime[-6] not in ['+', '-']:
            datetime += self.__time_zone
        self._body[self._property_type]['before'] = datetime
        return self

    def after(self, datetime: str) -> 'filter_date':
        """
        Args:
            datetime: string(ISO 8601 date.  "2021-05-10"  or "2021-05-10T12:00:00" or "2021-10-15T12:00:00-07:00")
        Returns:
        """
        if self.__time_zone and len(datetime) < 10 and datetime[-6] not in ['+', '-']:
            datetime += self.__time_zone
        self._body[self._property_type]['after'] = datetime
        return self

    def on_or_before(self, datetime: str) -> 'filter_date':
        """
        Args:
            datetime: string(ISO 8601 date.  "2021-05-10"  or "2021-05-10T12:00:00" or "2021-10-15T12:00:00-07:00")
        Returns:
        """
        if self.__time_zone and len(datetime) < 10 and datetime[-6] not in ['+', '-']:
            datetime += self.__time_zone
        self._body[self._property_type]['on_or_before'] = datetime
        return self

    def on_or_after(self, datetime: str) -> 'filter_date':
        """
        Args:
            datetime: string(ISO 8601 date.  "2021-05-10"  or "2021-05-10T12:00:00" or "2021-10-15T12:00:00-07:00")
        Returns:
        """
        if self.__time_zone and len(datetime) < 10 and datetime[-6] not in ['+', '-']:
            datetime += self.__time_zone
        self._body[self._property_type]['on_or_after'] = datetime
        return self

    def past_week(self) -> 'filter_date':
        self._body[self._property_type]['past_week'] = {}
        return self

    def past_month(self) -> 'filter_date':
        self._body[self._property_type]['past_month'] = {}
        return self

    def past_year(self) -> 'filter_date':
        self._body[self._property_type]['past_year'] = {}
        return self

    def next_week(self) -> 'filter_date':
        self._body[self._property_type]['next_week'] = {}
        return self

    def next_month(self) -> 'filter_date':
        self._body[self._property_type]['next_month'] = {}
        return self

    def next_year(self) -> 'filter_date':
        self._body[self._property_type]['next_year'] = {}
        return self


class filter_files(FilterConditionEmpty):
    data_type = 'files'

    def __init__(self, property_name: str):
        """
        initialize
        Args:
            property_name:
        """

        super().__init__(property_name, property_type='files')


class filter_formula(filter_text, filter_checkbox, filter_number, filter_date, metaclass=ChangeMroMeta):  # type: ignore
    data_type = 'formula'

    def __init__(self, property_type: str, property_name: str, timezone: Optional[str] = ''):
        """
        formula filter

        :param property_type: 'string', 'checkbox', 'number', 'date'.
        :param property_name: $property_name
        :param timezone: '09:00', '+03:00', '-02:00' (only for 'date' filter).
        """

        TYPE_STRING = 'string'
        TYPE_CHECKBOX = 'checkbox'
        TYPE_NUMBER = 'number'
        TYPE_DATE = 'date'

        assert property_type in [TYPE_STRING, TYPE_CHECKBOX, TYPE_NUMBER, TYPE_DATE], \
            f"property_type '{property_type}' is not allowed in 'filter_formula'. Please read the docstring."

        if property_type == TYPE_DATE:
            filter_date.__init__(self, property_type, property_name, timezone)
            self._set_mro((filter_date, ))
        elif property_type == TYPE_CHECKBOX:
            filter_checkbox.__init__(self, property_name)
            self._set_mro((filter_checkbox, ))
        elif property_type == TYPE_NUMBER:
            filter_number.__init__(self, property_name)
            self._set_mro((filter_number, ))
        elif property_type == TYPE_STRING:
            filter_text.__init__(self, property_type, property_name)
            self._set_mro((filter_text, ))

    def get_body(self) -> Dict[str, Any]:
        # self._body = [{'property': 'Formula_checkbox', 'checkbox': {'equals': True}}]
        body: Dict[str, Any] = {'property': self._body['property']}
        body['formula'] = {self._property_type: copy.deepcopy(self._body[self._property_type])}
        # log.info(f"formula body: {self._body}")
        return body


class filter_people(FilterConditionEmpty, FilterConditionContains):
    """
    filter for 'people'.
    """

    data_type = 'people'

    TYPE_PEOPLE = 'people'
    TYPE_CREATED_BY = 'created_by'
    TYPE_LAST_EDITED_BY = 'last_edited_by'

    def __init__(self, property_type: str, property_name: str):
        """
        initialize 'filter_people' instance
        Args:
            property_name:
        """

        super().__init__(property_name, property_type=property_type)

    def contains(self, user_id: str) -> 'filter_people':
        """

        :return: filter_people
        """

        self._body[self._property_type]['contains'] = user_id
        return self

    def does_not_contain(self, user_id: str) -> 'filter_people':
        """

        :return: filter_people
        """

        self._body[self._property_type]['does_not_contain'] = user_id
        return self

    def is_empty(self) -> 'filter_people':
        """

        :return: filter_people
        """
        self._body[self._property_type]['is_empty'] = True

        return self

    def is_not_empty(self) -> 'filter_people':
        """

        :return: filter_people
        """
        self._body[self._property_type]['is_not_empty'] = True
        return self


class filter_relation(FilterConditionEmpty, FilterConditionContains):
    """
    filter for 'relation'.
    """

    data_type = 'relation'

    def __init__(self, property_name: str):
        """
        initialize 'filter_people' instance
        Args:
            property_name:
        """
        super().__init__(property_name, property_type='relation')

    def contains(self, page_id: str) -> 'filter_relation':
        """

        :return: filter_relation
        """

        self._body[self._property_type]['contains'] = page_id
        return self

    def does_not_contain(self, page_id: str) -> 'filter_relation':
        """

        :return: filter_relation
        """

        self._body[self._property_type]['does_not_contain'] = page_id
        return self

    def is_empty(self) -> 'filter_relation':
        """

        :return: filter_relation
        """
        self._body[self._property_type]['is_empty'] = True

        return self

    def is_not_empty(self) -> 'filter_relation':
        """

        :return: filter_relation
        """
        self._body[self._property_type]['is_not_empty'] = True
        return self


class filter_rollup(FilterConditionABC):
    """
    filter for 'rollup'.
    """

    data_type = 'rollup'

    """
    {
        "property": "Rollup_text",
        "rollup": { "any": { "rich_text": { "contains": "text" }}} 
    }
    
    """
    def __init__(self, property_name: str):
        """
        initialize 'filter_people' instance
        Args:
            property_name:
        """
        super().__init__(property_name, property_type='rollup')

    def any(self, filter_ins: FilterConditionABC) -> 'filter_rollup':
        """
        'filter_rollup' instance requires another 'filter instance', the title of which doesn't matter.

        :param filter_ins: any of 'filter' instance
        :return:
        """

        ins_body: Dict[str, Any] = filter_ins.get_body()
        ins_type: str = filter_ins._property_type
        self._body[self._property_type]['any'] = {ins_type: ins_body[ins_type]}
        return self

    def every(self, filter_ins: FilterConditionABC) -> 'filter_rollup':
        """
        'filter_rollup' instance requires another 'filter instance', the title of which doesn't matter.

        :param filter_ins: any of 'filter' instance
        :return:
        """
        ins_body: Dict[str, Any] = filter_ins.get_body()
        ins_type: str = filter_ins._property_type
        self._body[self._property_type]['every'] = {ins_type: ins_body[ins_type]}
        return self

    def none(self, filter_ins: FilterConditionABC) -> 'filter_rollup':
        """
        'filter_rollup' instance requires another 'filter instance', the title of which doesn't matter.

        :param filter_ins: any of 'filter' instance
        :return:
        """
        ins_body: Dict[str, Any] = filter_ins.get_body()
        ins_type: str = filter_ins._property_type
        self._body[self._property_type]['none'] = {ins_type: ins_body[ins_type]}
        return self

    def number(self, filter_ins: filter_number) -> 'filter_rollup':
        """
        'filter_rollup' instance requires another 'filter instance', the title of which doesn't matter.

        :param filter_ins: any of 'filter' instance
        :return:
        """
        ins_body: Dict[str, Any] = filter_ins.get_body()
        ins_type: str = filter_ins._property_type
        self._body[self._property_type]['number'] = {ins_type: ins_body[ins_type]}
        return self

    def date(self, filter_ins: filter_date) -> 'filter_rollup':
        """
        'filter_rollup' instance requires another 'filter instance', the title of which doesn't matter.

        :param filter_ins: any of 'filter' instance
        :return:
        """
        ins_body: Dict[str, Any] = filter_ins.get_body()
        ins_type: str = filter_ins._property_type
        self._body[self._property_type]['date'] = {ins_type: ins_body[ins_type]}
        return self


"""
SORTS
"""


class sorts:

    ASCENDING = 'ascending'
    DESCENDING = 'descending'
    CREATED_TIME = 'created_time'
    LAST_EDITED_TIME = 'last_edited_time'

    def __init__(self) -> None:
        """

        Args:
            compound: 'filter.OR' or 'filter.AND'
        """
        self._body: List[Any] = []

    def add(self, sort_obj: Type[SortObject]) -> 'sorts':
        assert issubclass(sort_obj, SortObject)
        self._body.append(dict(sort_obj._body))

        return self


class sort_by_timestamp(SortObject):

    def __init__(self, time_property: str, direction: Optional[str] = sorts.ASCENDING):
        assert time_property in [sorts.CREATED_TIME, sorts.LAST_EDITED_TIME]
        assert direction in [sorts.ASCENDING, sorts.DESCENDING]

        self._body = {'timestamp': time_property, 'direction': direction}


class sort_by_property(SortObject):

    def __init__(self, property_name: str, direction: Optional[str] = sorts.ASCENDING):
        assert direction in [sorts.ASCENDING, sorts.DESCENDING]

        self._body = {'property': property_name, 'direction': direction}


"""
EXPRESSION PARSING
"""

T_Union = Union[_ast.AST,
                _ast.Expr,
                _ast.Module,
                _ast.BoolOp,
                _ast.Or,
                _ast.Compare,
                _ast.Eq,
                _ast.Constant,
                _ast.Name,
                _ast.Load,
                _ast.Num,  # type: ignore
                _ast.Str,  # type: ignore
                _ast.UnaryOp,
                ]

T_Node = Union[T_Union, List[T_Union]]


op_map = {
    'AST': '',
    'Expr': '',
    'Module': '',
    'BoolOp': '',
    'Or': '',
    'Compare': '',
    'Eq': '',
    'Constant': '',
    'Name': '',
    'Load': '',

    # Replaced by 'Constant' since python 3.8
    'Num': '',
    'Str': '',
    'NameConstant': '',

    'Assign': '',
    ###
    'Add': '',
    'And': '',
    'AnnAssign': '',
    'Assert': '',
    'AsyncFor': '',
    'AsyncFunctionDef': '',
    'AsyncWith': '',
    'Attribute': '',
    'AugAssign': '',
    'AugLoad': '',
    'AugStore': '',
    'Await': '',
    'BinOp': '',
    'BitAnd': '',
    'BitOr': '',
    'BitXor': '',
    'Break': '',
    'Call': '',
    'ClassDef': '',
    'Not': '',
    'NotEq': '',
    'NotIn': '',
    'Gt': '',
    'GtE': '',

    'Continue': '',
    'Del': '',
    'Delete': '',
    'Dict': '',
    'DictComp': '',
    'Div': '',
    'ExceptHandler': '',
    'Expression': '',
    'ExtSlice': '',
    'FloorDiv': '',
    'For': '',
    'FormattedValue': '',
    'FunctionDef': '',
    'FunctionType': '',
    'GeneratorExp': '',
    'Global': '',
    'If': '',
    'IfExp': '',
    'Import': '',
    'ImportFrom': '',
    'In': '',
    'Index': '',
    'Interactive': '',
    'Invert': '',
    'Is': '',
    'IsNot': '',
    'JoinedStr': '',
    'LShift': '',
    'Lambda': '',
    'List': '',
    'ListComp': '',
    'Lt': '',
    'LtE': '',
    'MatMult': '',
    'Mod': '',
    'Mult': '',
    'NamedExpr': '',
    'Nonlocal': '',
    'Param': '',
    'Pass': '',
    'Pow': '',
    'PyCF_ALLOW_TOP_LEVEL_AWAIT': '',
    'PyCF_ONLY_AST': '',
    'PyCF_TYPE_COMMENTS': '',
    'RShift': '',
    'Raise': '',
    'Return': '',
    'Set': '',
    'SetComp': '',
    'Slice': '',
    'Starred': '',
    'Store': '',
    'Sub': '',
    'Subscript': '',
    'Suite': '',
    'Try': '',
    'Tuple': '',
    'TypeIgnore': '',
    'UAdd': '',
    'USub': '',
    'UnaryOp': '',
    'While': '',
    'With': '',
    'Yield': '',
    'YieldFrom': '',
    'alias': '',
    'arg': '',
    'arguments': '',
    'boolop': '',
    'cmpop': '',
    'comprehension': '',
    'excepthandler': '',
    'expr': '',
    'expr_context': '',
    'keyword': '',
    'mod': '',
    'operator': '',
    'slice': '',
    'stmt': '',
    'type_ignore': '',
    'unaryop': '',
    'withitem': '',
}

ast_types_dict = {getattr(_ast, e): e for e in dir(_ast) if e in op_map}


def get_ast_attr(node: _ast.AST) -> Dict[str, _ast.AST]:
    # print(dir(node))
    return {e: getattr(node, e) for e in dir(node) if
            type(getattr(node, e)) in ast_types_dict or type(getattr(node, e)) == list}


def check_ast_type(node: T_Node, node_type: str) -> bool:
    if type(node) not in ast_types_dict:
        return False
    return ast_types_dict[type(node)] == node_type


def display_ast_tree(node: T_Node, indent: int = 0, key: str = '') -> None:
    indent_str = '   ' * indent
    content = f"{indent_str}{node}{'('+key+')' if key else ''}"
    if hasattr(node, 's'):
        content += f" s:{node.s}"  # type: ignore

    if hasattr(node, 'id'):
        content += f" id:{node.id}"  # type: ignore

    if hasattr(node, 'n'):
        content += f" n:{node.n}"  # type: ignore

    if hasattr(node, 'value'):
        content += f" value:{node.value}"  # type: ignore

    log.info(content)

    if isinstance(node, list):
        for e in node:
            if type(e) in ast_types_dict:
                display_ast_tree(e, indent, key='list_el')
            else:
                log.debug(f"e:{e}")

    else:
        # log.info(content)
        for k, v in get_ast_attr(node).items():
            display_ast_tree(v, indent + 1, k)


T_Filter = TypeVar('T_Filter', FilterConditionEmpty, FilterConditionEquals, FilterConditionContains, FilterConditionABC)
T_Sorts = TypeVar('T_Sorts', SortObject, sorts)


class Query:
    """
    'Query' object which contains 'expression parser' and 'filter object constructor'.

    """

    def __init__(self, db_properties: Any):
        """

        :param db_properties: PropertiesProperty
        """
        self.properties = db_properties
        self._error_with_expr = ''
        self.expression = ''

    def parse_unaryop(self, expr: _ast.UnaryOp) -> filter:
        """
        Unary operator allows 'Not' only. It's used for 'is_empty' case.
        :param expr: _ast.UnaryOp
        :return: filter
        """
        assert check_ast_type(expr.op,
                          'Not'), f"{self.get_error_comment(expr)} Invalid UnaryOp: {ast_types_dict[type(expr.op)]}"
        assert check_ast_type(expr.operand,
                          'Name'), f"{self.get_error_comment(expr)} after 'not' only 'property name' allow"
        return self.is_empty(expr.operand)  # type: ignore

    def call_by_method_name(self, filter_ins: T_Filter, method_name: str, value: Optional[object] = None) -> T_Filter:
        """
        call the 'method' by 'name' with value. Before call the method, check the 'method' in the filter.
        After calling, return 'filter instance'.
        :param filter_ins:
        :param method_name: str
        :param value: object, optional
        :return: filter instance
        """
        # assert
        # 메소드 네임만 받으면, 애러시 어느 부분에서 발생했는지 알 수가 없다. 메소드 네임과 에러를 함께 넣을거면,
        # It would be better to check the symbol here and assign proper method.
        # TODO: call by name only? or check the symbol.

    def call_by_symbol(self, filter_ins: T_Filter, symbol: T_Node) -> T_Filter:
        """
        call by operator symbol.

        :param filter_ins:
        :param symbol:
        :return:
        """

    def parse_compare(self, compare_node: _ast.Compare) -> FilterConditionABC:
        """

        cmpop = Eq | NotEq | Lt | LtE | Gt | GtE | Is | IsNot | In | NotIn

        :param compare_node:
        :return: filter_ins
        """
        def get_elements(compare_node: _ast.Compare) -> Tuple[T_Node, ast.Name, T_Node]:
            """

            :param compare_node:
            :return: comparator, left, op
            """
            assert len(compare_node.comparators) == 1, \
                f"{self.get_error_comment(compare_node)} Not allow comparing sequence(like: Number < 4 < 3)"
            comparator: T_Node = compare_node.comparators[0]
            left: _ast.Name = compare_node.left  # type: ignore

            check_left: bool = check_ast_type(left, 'Name')
            check_comparator: bool = check_ast_type(comparator, 'Name')
            # One of 'comparator' and 'left' should be '_ast.Name', which means compare with 'Property'.
            assert (check_left or check_comparator) and (sum((check_left, check_comparator)) == 1),  \
                f"{self.get_error_comment(compare_node.left)} " \
                f"One of 'comparator' and 'left' should be 'variable name' and  'primitive value('string' or 'number')'."
            # check if left is '_ast.Name' and swap.
            if check_comparator:
                comparator, left = left, comparator

            # 'ops' has only one value since 'comparators' has single value.
            op = compare_node.ops[0]
            return comparator, left, op

        def test() -> None:
            pass

        comparator, left, op = get_elements(compare_node)

        prop_name = left.id
        prop_obj: properties_basic.DbPropertyObject
        filter_ins: FilterConditionABC
        prop_obj, filter_ins = self.get_property_and_filter(left)

        error_comment = f"{self.get_error_comment(comparator)} " \
                        f"Type of '{prop_name}' property is '{prop_obj._type_defined}'. It does not match with " \
                        f"'{{}}'."

        #  'Num', 'Str', 'NameConstant' replaced by 'Constant' since python 3.8
        # TODO: 필터 타입에 따라 요구되는 '데이터 타입'을 비교해야 함. 비교 대상(comparator)을 기준으로 '필터 타입'을 확인할 수 없음.
        # if check_type(comparator, 'Num'):
        #     assert type(filter_ins) == filter_number, error_comment.format(filter_number.data_type)
        #     value = comparator.n  # type: ignore
        # elif check_type(comparator, 'Str'):
        #     assert type(filter_ins) == filter_text, error_comment.format(filter_text.data_type)
        #     value = comparator.s  # type: ignore
        # # True, False
        # elif check_type(comparator, 'NameConstant'):
        #     assert comparator.value is not None, f"{self.get_error_comment(comparator)} None is invalid value."  # type: ignore
        #     assert type(filter_ins) == filter_checkbox, error_comment.format(filter_checkbox.data_type)
        #     value = comparator.value  # type: ignore


        # else:
        #     raise NotionApiQueoryException(f'{self.get_error_comment(comparator)} '
        #                                    f'Invalid Compare comparator: {comparator}')

        # TODO: Lt | LtE | Gt | GtE |
        # if isinstance(op, (_ast.Eq, _ast.Is)):
        #     filter_ins.equals(value)  # type: ignore
        # elif isinstance(op, (_ast.NotEq, _ast.IsNot)):
        #     filter_ins.does_not_equal(value)  # type: ignore
        # # contain
        # elif isinstance(op, _ast.In):
        #     filter_ins.contains(value)  # type: ignore
        # elif isinstance(op, _ast.NotIn):
        #     filter_ins.does_not_contain(value)  # type: ignore
        # elif isinstance(op, _ast.Lt):
        #     filter_ins.less_than(value)  # type: ignore
        #
        # else:
        #     raise NotionApiQueoryException(f'{self.get_error_comment(compare_node)} Invalid Compare OPS: {type(op)}')

        return filter_ins

    def parse_module(self, expression: str) -> Union[None, filter]:
        """
        search object and call proper function
        """

        node: _ast.Module = ast.parse(expression)
        display_ast_tree(node)
        assert check_ast_type(node, 'Module'), f"{self.get_error_comment(node)} Invalid expression"
        assert len(node.body) == 1, f"{self.get_error_comment(node)} Invalid expression"

        expr: _ast.Expr = node.body[0]  # type: ignore

        return self.parse_expression(expr)

    def parse_expression(self, expr: _ast.Expr) -> filter:
        """
        parse Base Expression allows 'Name', 'UnaryOp', 'Compare', 'BoolOp'.
        'BoolOp' is the only composition.

        :param expr: 'Name', 'UnaryOp', 'Compare', 'BoolOp'
        :return: filter
        """
        assert not check_ast_type(expr, 'Assign'), f"{self.get_error_comment(expr)} '=' should be '=='"
        assert check_ast_type(expr, 'Expr'), f"{self.get_error_comment(expr)} only 'expression' allow."
        db_filter = filter()

        # 'Name' which only exists calls 'is_not_empty'
        element: T_Node = expr.value
        if check_ast_type(element, 'Name'):
            ast_name: _ast.Name = expr.value  # type: ignore
            filter_ins = self.is_not_empty(ast_name)
            db_filter.add(filter_ins)

        # 'not' keyword calls 'is_empty'
        elif check_ast_type(element, 'UnaryOp'):
            db_filter.add(self.parse_unaryop(element))  # type: ignore

        # compare
        elif check_ast_type(element, 'Compare'):
            filter_ins = self.parse_compare(element)  # type: ignore
            db_filter.add(filter_ins)

        # BoolOp composition
        elif check_ast_type(element, 'BoolOp'):
            bool_op = 'or'
            if check_ast_type(element.op, 'And'):  # type: ignore
                bool_op = 'and'

            db_filter.bool_op = bool_op
            for compare_obj in element.values:  # type: ignore
                db_filter.add(self.parse_expression(compare_obj))  # type: ignore

        else:
            raise NotionApiQueoryException(f"{self.get_error_comment(element)} Invalid Expression.")

        return db_filter

    def get_error_comment(self, expr: T_Node) -> str:
        """
        pickup error line and point elemnt.
        :return: str
        """
        expr_splited: List[str] = self.expression.split('\n')
        error_line: str = expr_splited[expr.lineno-1]  # type: ignore
        indent = ' ' * 4
        comment = f"\n{indent}{error_line}\n{indent}{' ' * expr.col_offset + '^'}\n{indent}  "  # type: ignore
        return comment

    def get_property_and_filter(self, expr: _ast.Name) -> Tuple[properties_basic.DbPropertyObject, FilterConditionABC]:
        """
        :param expr: instance of '_ast.Name'
        :return: filter_ins
        """
        prop_name: str = expr.id
        assert prop_name in self.properties, f"{self.get_error_comment(expr)} Wrong property name."
        prop_obj: properties_basic.DbPropertyObject = self.properties[prop_name]
        prop_type = prop_obj._type_defined
        if prop_type == 'title':
            prop_type = 'text'
        filter_name: str = f'filter_{prop_type}'
        assert filter_name in globals()
        filter_cls: Type[T_Filter] = globals()[filter_name]  # type: ignore
        return prop_obj, filter_cls(prop_name)  # type: ignore

    def is_not_empty(self, expr: _ast.Name) -> FilterConditionEmpty:
        prop_obj, filter_ins = self.get_property_and_filter(expr)
        assert hasattr(filter_ins, 'is_not_empty')
        filter_ins.is_not_empty()  # type: ignore
        return filter_ins  # type: ignore

    def is_empty(self, expr: _ast.Name) -> FilterConditionEmpty:
        prop_obj: properties_basic.DbPropertyObject
        filter_ins: FilterConditionABC
        prop_obj, filter_ins = self.get_property_and_filter(expr)

        assert 'is_empty' in dir(filter_ins)
        filter_ins.is_empty()  # type: ignore
        return filter_ins  # type: ignore

    def query_by_expression(self, expression: str) -> filter:
        """
        create 'filter' and 'sorts' object with 'python expression'

        :param expression: str
        :return: (filter, sorts)
        """
        self.expression = f"{expression}"

        self._error_with_expr = f"'{expression}' is invalid expression."

        result: filter = self.parse_module(expression)  # type: ignore
        log.info(f"{expression}: {result.get_body()}")
        # assert result._body['or'], f"{result._body['or']}"
        return result



