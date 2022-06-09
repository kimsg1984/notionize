import logging



# log_format = '%(lineno)s|%(levelname)s] %(funcName)s(): %(message)s'
log_format = '%(asctime)s [%(filename)s:%(lineno)s|%(levelname)s] %(funcName)s(): %(message)s'

# logging.basicConfig(format=log_format, level=logging.ERROR)
logging.basicConfig(format=log_format, level=logging.INFO)
# logging.basicConfig(format=log_format, level=logging.DEBUG)
# logging.basicConfig(format=log_format, level=logging.WARN)

log = logging.getLogger(__name__)
import traceback

from unittest import TestCase
from query import sorts
import query
from query import filter
# from query import query_by_expression
from query import filter_text
from query import filter_rollup
import notionized.notion
import pandas as pd
from pprint import pprint

from typing import List
from typing import Dict
from functions import pdir

notion = notionized.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')
test_table = notion.get_database('44d6b8fda2734f04968a771a79f97fb6')

datetime_case = ['2022-03-23', '2022-03-24', '2022-03-25', '2022-03-26',
                               '2022-03-25T12:00', '2022-03-25T12:00:00+09:00', '2022-03-25T15:00:00']
text_case = ['TitleFixed', 'TitleFixed1', 'itleFixed1', 'some text', 'kimsg1984@gmail.com', '01065033680',
               'https://notion.so', 'option1', 'moption2', 'string']

testcase_sample = {
    'string': text_case,
    'boolean (only true)': [None],  # implimented no parameter
    'number': [100, 101, 102, 1, 2],
    'boolean': [True, False],
    'string(enum)': '',
    'object(number filter condition)': '',
    'string(UUIDv4)': [],
    'object(date filtercondition)': '',
    'object(checkbox filter condition)': '',
    'object(text filter condition)': '',
    'object': '',
    'string (ISO 8601 date)': datetime_case,
    'object (empty)': [{}, ],
    'object (number filter condition)': [1, 2],
    'object (checkbox filter condition)': [True, False],
    'object (date filter condition)': datetime_case,
    'object (text filter condition)': ['string', ],
    'string (UUIDv4)': ['1ecee6f3-2456-4778-8fca-f9c77f34f2b9', '10f8df851f894e6089f6889638f2f0a3'],
}


def query_test(test_type: str, test_all=False) -> None:
    # done
    filter_table = notion.get_database('e8108c53c9cf42259878954a289842fe')
    test_table = notion.get_database('44d6b8fda2734f04968a771a79f97fb6')  # test1

    result: dict = filter_table.get_as_dictionaries(filter_table._filter_and_sort())

    test_properties = {v._type_defined: k for k, v in test_table.properties.items()}
    """
    ['email', 'last_edited_time', 'rich_text', 'created_by', 'url', 'multi_select', 'date', 'people', 'select',
         'number', 'relation', 'last_edited_by', 'checkbox', 'formula', 'created_time', 'phone_number', 'files',
         'rollup', 'title']
    """
    # print('test_properties', test_properties.keys())
    # print(*[f"{r['object_type']}: {r['property_name']}" for r in result], sep='\n')


    if test_all:
        test_rows = [r for r in result if (r['object_type'] == test_type)]
    else:
        test_rows = [r for r in result if (r['object_type'] == test_type) and (r['메소드'] is False)]

    print('test_rows', test_rows)

    for r in test_rows:
        test_each_row(r, test_properties, result)


def test_formula(r, formula_type, test_type):
    done = r['메소드']
    property_name = r['property_name']
    object_type = r['object_type']
    value_type = r['value_type']
    property_type = r['property_type']

    for property in property_type:
        "formula: string(object (text filter condition)), formula(Formula_number)"
        test_column = f"Formula_{property}"

        if property == 'title':
            continue
        elif property == 'rich_text':
            test_column = 'Formula_string'
        else:
            continue
        print(f'{object_type}: {property_name}({value_type}), {property}({test_column}), test_value: {test_type}')
        for test_value in testcase_sample[value_type]:
            filter_function = getattr(query, f'filter_formula')
            # print('filter_function: ', filter_function, 'test_value:', test_value)
            condition = filter_function(formula_type, test_column)
            try:
                method = getattr(condition, property_name)
            except Exception as e:
                print('condition:', condition)
                raise e
            # print(f'method: {method}')
            if (not test_value) and (not (type(test_value) == bool)):
                method()
            else:
                method(test_value)
            db_filter = filter()
            db_filter.add(condition)
            result = test_table.get_as_dictionaries(test_table._filter_and_sort(notion_filter=db_filter))
            for r in result:
                print('     value:', test_value, f'{test_column}:', r[test_column])


def test_each_row(r, test_properties, result, formula=False):
    done = r['메소드']
    property_name = r['property_name']
    object_type = r['object_type']
    value_type = r['value_type']
    property_type = r['property_type']

    for property in property_type:
        test_column = test_properties[property]
        print(f'{object_type}: {property_name}({value_type}), {property}({test_column})')
        for test_value in testcase_sample[value_type]:
            if object_type in ['created_time', 'last_edited_time']:
                filter_function = getattr(query, f'filter_date')
            else:
                filter_function = getattr(query, f'filter_{object_type}')

            if object_type in (['text', 'people'] + ['date' 'created_time', 'last_edited_time]']):
                if object_type in ['date', 'created_time', 'last_edited_time']:
                    condition = filter_function(property, test_column, timezone='+09:00')
                else:
                    condition = filter_function(property, test_column)
            elif object_type == 'formula':
                if property_name == 'string':
                    test_rows_sub = [r for r in result if (r['object_type'] == 'text')]
                else:
                    test_rows_sub = [r for r in result if (r['object_type'] == property_name)]
                # print('property_name', property_name, 'test_rows_sub', test_rows_sub)
                for r_sub in test_rows_sub:
                    test_formula(r_sub, property_name, value_type)
                    # break
                continue

            else:
                condition = filter_function(test_column)
            try:
                method = getattr(condition, property_name)
            except Exception as e:
                print('condition:', condition)
                raise e
            # print(f'method: {method}, test_value: {test_value}')
            if (not test_value) and (not (type(test_value) == bool)):
                method()
            else:
                method(test_value)
            db_filter = filter()
            db_filter.add(condition)
            print(db_filter.get_body())
            result = test_table.get_as_dictionaries(test_table._filter_and_sort(notion_filter=db_filter))
            for r in result:
                print('     value:', test_value, f'{test_column}:', r[test_column])


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

    def test_date(self) -> None:
        # query_test('date', test_all=True)
        # query_test('last_edited_time', test_all=True)
        query_test('created_time')

    def dtest_files(self) -> None:
        query_test('files', test_all=True)

    def test_formula(self) -> None:
        query_test('formula')

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

    # waiting
    def wtest_query_invalid(self):
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

    def dtest_people(self):
        query_test('people')

    def dtest_relation(self):
        query_test('relation')

    def dtest_rollup_simple(self):

        db_filter = filter()
        condition_text = filter_text(filter_text.TYPE_RICHTEXT, 'Rollup_text')
        condition_text.contains('text')
        condition_rollup = filter_rollup('Rollup_text')
        condition_rollup.any(condition_text)
        db_filter.add(condition_rollup)

        print(db_filter.get_body())
        result = test_table.get_as_dictionaries(test_table._filter_and_sort(notion_filter=db_filter))
        print(result)

    def dtest_rollup_relation(self):

        table = notion.get_database('c0dbfa46ba0046d294f087f4a1c5e1cc')
        print(dict(table.properties))
        for value in table._relation_reference.values():
            print(dict(value))
        # print(dict(table._relation_reference))

    def test_rollup_full_case(self):
        table = notion.get_database('c0dbfa46ba0046d294f087f4a1c5e1cc')
        rollup_list = [k for k, v in table.properties.items() if v.type == 'rollup']
        print(rollup_list)


        for r in rollup_list:

            db_filter = filter()
            rollup = table.properties[r]
            relation = table.properties[rollup.rollup['relation_property_name']]
            relation_db_id = relation.relation['database_id']
            relation_refer = table._relation_reference[relation_db_id]
            rollup_property_id = rollup.rollup['rollup_property_id']
            rollup_type = relation_refer[rollup_property_id]

            print('rollup type:', rollup_type)

            # database에서 이를 통해 '릴레이션 데이터' 정보를 생성하여 가지고 다닐것.
            # '릴레이션'에 '릴레이션'을 걸어 '릴레이션'을 걸 수 있을까? -> '롤업'에 대하여는 '릴레이션' 불가
            # -> '롤업'에 대한 '릴레이션'을 추적하여 '릴레이션 타입'만 참고할 수 있도록 하면 될듯 함.
            # api는 접근이 가능한 '릴레이션'에 대하여만 노출을 하여줌.
            # relation_db_id = relation.relation['database_id']


            # print(rollup.name, rollup.type, rollup.rollup.keys(), pdir(rollup))
            # condition_text = filter_text(filter_text.TYPE_RICHTEXT, 'Rollup_text')
            # condition_text.contains('text')
            # condition_rollup = filter_rollup('Rollup_text')
            # condition_rollup.any(condition_text)
            # db_filter.add(condition_rollup)
            #
            # print(db_filter.get_body())
            # result = test_table.get_as_dictionaries(test_table._filter_and_sort(notion_filter=db_filter))
            # print(result)
