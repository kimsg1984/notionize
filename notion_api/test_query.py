import logging

# log_format = '%(asctime)s [%(filename)s:%(lineno)s|%(levelname)s] %(funcName)s(): %(message)s'

# logging.basicConfig(format=log_format, level=logging.DEBUG)
log_format = '%(lineno)s|%(levelname)s] %(funcName)s(): %(message)s'
logging.basicConfig(format=log_format, level=logging.INFO)
# logging.basicConfig(format=log_format, level=logging.WARN)

log = logging.getLogger(__name__)
import traceback

from unittest import TestCase
from query import sorts
import query
from query import filter
# from query import query_by_expression
from query import filter_text
import notion_api.notion
import pandas as pd
from pprint import pprint

from typing import List
from typing import Dict


notion = notion_api.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')
test_table = notion.get_database('44d6b8fda2734f04968a771a79f97fb6')

testcase_sample = {
    'string': ['TitleFixed', 'TitleFixed1', 'itleFixed1', 'some text', 'kimsg1984@gmail.com', '01065033680',
               'https://notion.so', 'option1', 'moption2'],
    'boolean (only true)': [None],  # implimented no parameter
    'number': [100, 101, 102],
    'boolean': [True, False],
    'string(enum)': '',
    'object(number filter condition)': '',
    'string(UUIDv4)': '',
    'object(date filtercondition)': '',
    'object(checkbox filter condition)': '',
    'object(text filter condition)': '',
    'object': '',
    'string (ISO 8601 date)': ['2022-03-23', '2022-03-24', '2022-03-25', '2022-03-26',
                               '2022-03-25T12:00', '2022-03-25T12:00:00+09:00', '2022-03-25T15:00:00'],
    'object (empty)': [{}, ],
}


def query_test(test_type: str) -> None:
    # done
    filter_table = notion.get_database('e8108c53c9cf42259878954a289842fe')
    test_table = notion.get_database('44d6b8fda2734f04968a771a79f97fb6')  # test1

    # columns = ('Done', 'property_name', 'object_type', 'value_type', 'property_type')
    # result = filter_table.get_as_tuples(filter_table.query(), columns)
    result: dict = filter_table.get_as_dictionaries(filter_table._filter_and_sort())
    # df = pd.DataFrame(result[1:], columns=columns)
    # pprint(result)

    # object_type = ['text', 'timestamp' 'formula' 'relation' 'files' 'rollup' 'multi_select' 'date'
    #                        'people' 'select' 'checkbox' 'number']

    test_properties = {v._type_defined: k for k, v in test_table.properties.items()}
    print(test_properties.keys())
    a = ['email', 'last_edited_time', 'rich_text', 'created_by', 'url', 'multi_select', 'date', 'people', 'select',
         'number', 'relation', 'last_edited_by', 'checkbox', 'formula', 'created_time', 'phone_number', 'files',
         'rollup', 'title']


    test_rows = [r for r in result if (r['object_type'] == test_type) and (r['Done'] == False)]

    # print(result)

    for r in test_rows:
        done = r['Done']
        property_name = r['property_name']
        object_type = r['object_type']
        value_type = r['value_type']
        property_type = r['property_type']


        for property in property_type:
            test_column = test_properties[property]
            print(f'{object_type}: {property_name}({value_type}), {property}({test_column})')
            for test_value in testcase_sample[value_type]:

                filter_function = getattr(query, f'filter_{object_type}')

                if object_type in ['text', 'date', 'people', 'timestamp']:
                    if object_type == 'date':
                        condition = filter_function(property, test_column, timezone='+09:00')
                    else:
                        condition = filter_function(property, test_column)
                else:
                    condition = filter_function(test_column)

                method = getattr(condition, property_name)
                # print(f'method: {method}')
                if not test_value:
                    method()
                else:
                    method(test_value)
                # print('     ', test_value)
                db_filter = filter()
                db_filter.add(condition)
                result = test_table.get_as_dictionaries(test_table._filter_and_sort(notion_filter=db_filter))
                for r in result:
                    # print('     value:', test_value, f'{test_column}:', r)
                    print('     value:', test_value, f'{test_column}:', r[test_column])
                break
            break


class Testfilter_text(TestCase):
    def dtest_property(self) -> None:
        # print(d3)
        filter_table = notion.get_database('e8108c53c9cf42259878954a289842fe')
        test_table = notion.get_database('44d6b8fda2734f04968a771a79f97fb6')  # test1
        columns = ('property_name', 'object_type', 'value_type', 'property_type')
        result = filter_table.get_as_tuples(filter_table._filter_and_sort(), columns)
        df = pd.DataFrame(result[1:], columns=columns)
        # pprint(result)

        object_type = ['text', 'timestamp' 'formula' 'relation' 'files' 'rollup' 'multi_select' 'date'
                               'people' 'select' 'checkbox' 'number']

        object_type_test = ['text']
        test_properties = {v._type_defined: k for k, v in test_table.properties.items()}
        # print(repr(test_properties))
        for test_type in object_type_test:
            test_rows = [r for r in result[1:] if r[1] == test_type]
            for r in test_rows:
                property_name, object_type, value_type, property_type = r

                for property in property_type:
                    test_column = test_properties[property]
                    print(f'{object_type}: {property_name}({value_type}), {property}({test_column})')


def query_test_syntax(syntax: str, check_properties: List[str] = [], only_syntax=False) -> None:
    log.info('syntax: ' + syntax)
    if only_syntax:
        log.info(test_table._query_helper.query_by_expression(syntax)._body)

    else:
        for e in test_table.get_as_dictionaries(test_table.query(syntax)):
            if check_properties:
                log.info('    ' + ', '.join(f"{k}: {e[k]}" for k in check_properties))
            else:
                log.info('    ' + str(e))


class Query_test(TestCase):

    def dtest_text(self) -> None:
        query_test('text')

    def dtest_number(self) -> None:
        query_test('number')

    def dtest_checkbox(self) -> None:
        query_test('checkbox')

    def dtest_select(self) -> None:
        query_test('select')

    def dtest_multi_select(self) -> None:
        query_test('multi_select')

    def dtest_date(self) -> None:
        query_test('date')

    def dtest_files(self) -> None:
        query_test('files')

    def dtest_query_existance(self) -> None:
        test_table = notion.get_database('44d6b8fda2734f04968a771a79f97fb6')
        pprint(test_table.get_as_dictionaries(test_table.query('Number')))
        pprint(test_table.get_as_dictionaries(test_table.query('not Number')))

    def dtest_query_equals(self) -> None:
        """
        Title, Number, Checkbox
        """


        test_properties = (
            ('Title', '"TitleFixed1"'),
            ('Number', '2'),
            ('Checkbox', True),
            ('Checkbox', False),
        )

        test_symbols = (
            '==',
            '!=',
            'is',
            'is not',
        )
        syntax = '{} {} {}'
        query_test_syntax("Number == 2", ['Number'])
        for prop, value in test_properties:
            for symbol in test_symbols:
                query_test_syntax(syntax.format(prop, symbol, value), [prop])

    def test_query_invalid(self):
        invalid_syntax = (
            # 'True',
            # 'False',
            # 'not Title',
            # 'Title',
            # 'Title == "t" or Number == 1',
            # 'Title == "t" or Number == 1 or Title == 1',
#             """(Title == 1
# or
# Number == 1)""",

            # "'Title' in Title",
            # "(Number < 2) < 3",
            # 'Number < 4 < 3',
            # "'title1' == Title",
            # "'Title' == 'Title'",
            "Title == None",
        )

        syntax: str
        for syntax in invalid_syntax:
            try:
                query_test_syntax(syntax, only_syntax=True)

            except Exception as e:
                # log.info('[Error]' + str(e))
                log.info(traceback.format_exc())
