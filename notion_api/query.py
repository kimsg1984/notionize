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


referance: https://developers.notion.com/reference/post-database-query-filter

"""
from typing import Dict
from typing import TypeVar
from typing import List
from typing import Any
from typing import Type
from typing import Union
from typing import Optional
from typing import Generic
from typing import Tuple

import abc
import ast
import _ast

from notion_api import properties_basic
from notion_api import properties_db
from notion_api.functions import pdir
from notion_api.exception import NotionApiQueoryException

# import typing
# typing.Optional

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
        self.__bool_op = bool_op
        self._body: Dict[str, List[FilterConditionABC]] = {bool_op: []}

    def add(self, condition: 'T_Filter') -> 'filter':
        """

        Args:
            condition:

        Returns:

        """

        assert issubclass(type(condition), FilterConditionABC), 'type: ' + str(type(condition))
        compound_obj: List[Any] = self._body[self.__bool_op]
        compound_obj.append(dict(condition._body))
        return self

    def clear(self) -> 'filter':
        """
        clear conditions to reuse object.

        Returns:

        """
        self._body = {self.__bool_op: []}
        return self

    @property
    def bool_op(self) -> str:
        return self.__bool_op

    @bool_op.setter
    def bool_op(self, compound_type: str) -> None:
        assert compound_type in ['or', 'and']
        self.__bool_op = compound_type


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
        assert issubclass(sort_obj, SortObject)
        self._body.append(dict(sort_obj.body))

        return self


class SortObject:
    pass


class sort_by_timestamp(SortObject):

    def __init__(self, time_property, direction=sorts.ASCENDING):
        assert time_property in [sorts.CREATED_TIME, sorts.LAST_EDITED_TIME]
        assert direction in [sorts.ASCENDING, sorts.DESCENDING]

        self._body = {'timestamp': time_property, 'direction': direction}


class sort_by_property(SortObject):

    def __init__(self, property_name, direction=sorts.ASCENDING):
        assert direction in [sorts.ASCENDING, sorts.DESCENDING]

        self._body = {'property': property_name, 'direction': direction}


# filters

class FilterConditionABC(metaclass=abc.ABCMeta):

    def __init__(self, property_name: str, property_type: str = '', **kwargs: Dict[str, Any]):

        self._body: Dict[str, Any] = {
            'property': property_name,
            property_type: dict()
        }
        self._property_type: str = property_type


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
    def equals(self, value):
        pass

    @abc.abstractmethod
    def does_not_equal(self, value):
        pass


class FilterConditionContains(FilterConditionABC):
    @abc.abstractmethod
    def contains(self, value):
        pass

    @abc.abstractmethod
    def does_not_contain(self, value):
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


class filter_number(FilterConditionEquals, FilterConditionEmpty):
    data_type = 'number'

    def __init__(self, property_name: str):
        """
        initialize
        Args:
            property_name:
        """

        super().__init__(property_name, property_type='number')

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


class filter_checkbox(FilterConditionEquals):
    data_type = 'boolean'
    def __init__(self, property_name: str):
        """
        initialize
        Args:
            property_name:
        """

        super().__init__(property_name, property_type='checkbox')

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


class filter_select(FilterConditionEquals, FilterConditionEmpty):
    data_type = 'select'
    def __init__(self, property_name: str):
        """
        initialize
        Args:
            property_name:
        """

        super().__init__(property_name, property_type='select')

    def equals(self, option: str):
        """

        Args:
            option: str

        Returns:

        """
        self._body[self._property_type]['equals'] = option
        return self

    def does_not_equal(self, option: str):
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

    def contains(self, option: str):
        """

        Args:
            option: case sensitive

        Returns:

        """
        self._body[self._property_type]['contains'] = option
        return self

    def does_not_contain(self, option: str):
        """

        Args:
            option: case sensitive

        Returns:

        """
        self._body[self._property_type]['does_not_contain'] = option
        return self


class filter_date(FilterConditionEmpty):
    data_type = 'date'
    def __init__(self, property_type: str, property_name: str, timezone: str=''):
        """

        date filter requires 'timezone'. You should tail after 'datetime' like "2021-10-15T12:00:00+09:00" or
        use the 'timezone' parameter. If 'timezone' set, filter checks your 'datetime' argument with 'timezone' or
        not and tail it.

        :param property_type: 'date', 'created_time', 'last_edited_time'
        :param property_name: $property_name
        :param timezone: '09:00', '+03:00', '-02:00'
        """

        TYPE_DATE = 'date'
        TYPE_CREATED_TIME = 'created_time'
        TYPE_LAST_EDITED_TIME = 'last_edited_time'

        self.time_zone = ''
        if timezone:
            if timezone[0] in ['+', '-']:
                self.time_zone = timezone

            else:
                self.time_zone = '+' + timezone
        super().__init__(property_name, property_type=property_type)

#     def equals(self, datetime: str):
#         """
#         Args:
#             datetime: string(ISO 8601 date)
#         Returns:
# -
#         Usage:
#         filter_dt.equals("2021-05-10")
#         filter_dt.equals("2021-05-10T12:00:00")
#         filter_dt.equals("2021-10-15T12:00:00-07:00")
#         filter_dt = filter_date(filter_date.TYPE_TEXT, 'date_column_name', time_zone='+09:00')
#         """
#
#         if self.time_zone and len(datetime) < 10 and datetime[-6] not in ['+', '-']:
#             datetime += self.time_zone
#         self._body[self._property_type]['equals'] = datetime
#         return self

    def equals(self, datetime: str):
        """
        Args:
            datetime: string(ISO 8601 date.  "2021-05-10"  or "2021-05-10T12:00:00" or "2021-10-15T12:00:00-07:00")
        Returns:

        """

        if self.time_zone and 11 < len(datetime) and datetime[-6] not in ['+', '-']:
            datetime += self.time_zone

        self._body[self._property_type]['equals'] = datetime
        return self

    def before(self, datetime: str):
        """
        Args:
            datetime: string(ISO 8601 date.  "2021-05-10"  or "2021-05-10T12:00:00" or "2021-10-15T12:00:00-07:00")
        Returns:
        """
        if self.time_zone and len(datetime) < 10 and datetime[-6] not in ['+', '-']:
            datetime += self.time_zone
        self._body[self._property_type]['before'] = datetime

    def after(self, datetime: str):
        """
        Args:
            datetime: string(ISO 8601 date.  "2021-05-10"  or "2021-05-10T12:00:00" or "2021-10-15T12:00:00-07:00")
        Returns:
        """
        if self.time_zone and len(datetime) < 10 and datetime[-6] not in ['+', '-']:
            datetime += self.time_zone
        self._body[self._property_type]['after'] = datetime\

    def on_or_before(self, datetime: str):
        """
        Args:
            datetime: string(ISO 8601 date.  "2021-05-10"  or "2021-05-10T12:00:00" or "2021-10-15T12:00:00-07:00")
        Returns:
        """
        if self.time_zone and len(datetime) < 10 and datetime[-6] not in ['+', '-']:
            datetime += self.time_zone
        self._body[self._property_type]['on_or_before'] = datetime

    def on_or_after(self, datetime: str):
        """
        Args:
            datetime: string(ISO 8601 date.  "2021-05-10"  or "2021-05-10T12:00:00" or "2021-10-15T12:00:00-07:00")
        Returns:
        """
        if self.time_zone and len(datetime) < 10 and datetime[-6] not in ['+', '-']:
            datetime += self.time_zone
        self._body[self._property_type]['on_or_after'] = datetime

    def past_week(self):
        self._body[self._property_type]['past_week'] = {}

    def past_month(self):
        self._body[self._property_type]['past_month'] = {}

    def past_year(self):
        self._body[self._property_type]['past_year'] = {}

    def next_week(self):
        self._body[self._property_type]['next_week'] = {}

    def next_month(self):
        self._body[self._property_type]['next_month'] = {}

    def next_year(self):
        self._body[self._property_type]['next_year'] = {}


class filter_files(FilterConditionEmpty):
    data_type = 'files'
    def __init__(self, property_name: str):
        """
        initialize
        Args:
            property_name:
        """

        super().__init__(property_name, property_type='files')


    """
    create 'filter' and 'sorts' object with 'python expression'

    :param query_statement: str
    :return: (filter, sorts)
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

    # after python 3.8, these are removed.
    'Num': '',
    'Str': '',

    # after python 3.8, 'NameConstant' should be 'Constant'.
    'NameConstant': '',

    'Assign': '',

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


def check_type(node: T_Node, node_type: str) -> bool:
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


class GenericFilter(Generic[T_Filter]):
    pass


class Query:
    """
    'Query' object which contains 'expression parser' and 'filter object constructor'.

    """

    def __init__(self, db_properties):
        self.properties = db_properties
        self._error_with_expr = ''
        self.expression = ''

    def parse_unaryop(self, expr: _ast.UnaryOp) -> filter:
        assert check_type(expr.op,
                          'Not'), f"{self.get_error_comment(expr)} Invalid UnaryOp: {ast_types_dict[type(expr.op)]}"
        assert check_type(expr.operand,
                          'Name'), f"{self.get_error_comment(expr)} after 'not' only 'property_name' allow"
        return self.is_empty(expr.operand)  # type: ignore

    def search_base_expr(self, expr: _ast.Expr) -> filter:
        """
        parse Base Expression.
        :param ast_module:
        :return:
        """
        assert not check_type(expr, 'Assign'), f"{self.get_error_comment(expr)} '=' should be '=='"
        assert check_type(expr, 'Expr'), f"{self.get_error_comment(expr)} only 'expression' allow."
        db_filter = filter()

        # exists calls 'is_not_empty'
        element: T_Node = expr.value
        if check_type(element, 'Name'):
            ast_name: _ast.Name = expr.value  # type: ignore
            filter_ins = self.is_not_empty(ast_name)
            db_filter.add(filter_ins)

        # 'not' keywoard calls 'is_empty'
        elif check_type(element, 'UnaryOp'):
            db_filter.add(self.parse_unaryop(element))  # type: ignore

        # compare
        elif check_type(element, 'Compare'):
            filter_ins = self.parse_compare(element)  # type: ignore
            db_filter.add(filter_ins)

        # BoolOp composition
        elif check_type(element, 'BoolOp'):
            bool_op = 'or'
            if check_type(element.op, 'And'):  # type: ignore
                bool_op = 'and'

            db_filter.bool_op = bool_op
            for compare_obj in element.values:  # type: ignore
                db_filter.add(self.parse_compare(compare_obj))  # type: ignore

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

    def parse_compare(self, compare_node: _ast.Compare) -> FilterConditionABC:
        """
        Property should be 'left', value should be 'right'.
        :param compare_node:
        :return: filter_ins
        """
        assert len(compare_node.comparators) == 1, \
            f"{self.get_error_comment(compare_node)} Not allow comparing sequence(like: Number < 4 < 3)"
        comparator: T_Node = compare_node.comparators[0]
        assert check_type(compare_node.left, 'Name'),  \
            f"{self.get_error_comment(compare_node.left)} Invalid expression"
        left: _ast.Name = compare_node.left  # type: ignore
        assert len(compare_node.ops) == 1, f"{self.get_error_comment(comparator)} Only one OPS allow."
        ops = compare_node.ops[0]

        prop_name = left.id
        prop_obj: properties_basic.DbPropertyObject
        filter_ins: FilterConditionABC
        prop_obj, filter_ins = self.get_property_and_filter(left)

        error_comment = f"{self.get_error_comment(comparator)} " \
                        f"Type of '{prop_name}' property is '{prop_obj._type_defined}'. It does not match with " \
                        f"'{{}}'."

        if check_type(comparator, 'Num'):
            assert type(filter_ins) == filter_number, error_comment.format(filter_number.data_type)
            value = comparator.n  # type: ignore

        elif check_type(comparator, 'Str'):
            assert type(filter_ins) == filter_text, error_comment.format(filter_text.data_type)
            value = comparator.s  # type: ignore

        elif check_type(comparator, 'NameConstant'):
            assert type(filter_ins) == filter_checkbox, error_comment.format(filter_checkbox.data_type)
            value = comparator.value  # type: ignore
        else:
            raise NotionApiQueoryException(f'{self.get_error_comment(comparator)} '
                                           f'Invalid Compare comparator: {comparator}')


        if isinstance(ops, (_ast.Eq, _ast.Is)):
            filter_ins.equals(value)  # type: ignore
        elif isinstance(ops, (_ast.NotEq, _ast.IsNot)):
            filter_ins.does_not_equal(value)  # type: ignore
        else:
            raise NotionApiQueoryException(f'{self.get_error_comment(compare_node)} Invalid Compare OPS: {type(ops)}')

        # TODO: list type

        assert len(compare_node.ops) == 1
        op = compare_node.ops[0]
        
        return filter_ins

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
        prop_obj: properties_basic.DbPropertyObject
        filter_ins: FilterConditionABC
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

    def parse_expression(self, expression: str) -> Union[None, filter]:
        """
        search object and call proper function
        """

        node: _ast.Module = ast.parse(expression)
        display_ast_tree(node)
        assert check_type(node, 'Module'), f"{self.get_error_comment(node)} Invalid expression"
        assert len(node.body) == 1, f"{self.get_error_comment(node)} Invalid expression"

        expr: _ast.Expr = node.body[0]  # type: ignore

        return self.search_base_expr(expr)

    def query_by_expression(self, expression: str) -> filter:
        """
        create 'filter' and 'sorts' object with 'python expression'

        :param expression: str
        :return: (filter, sorts)
        """
        self.expression = f"{expression}"

        self._error_with_expr = f"'{expression}' is invalid expression."

        result: filter = self.parse_expression(expression)  # type: ignore
        log.info(f"{expression}: {result._body}")
        # assert result._body['or'], f"{result._body['or']}"
        return result



