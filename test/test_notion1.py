
from notion import Notion

from pprint import pprint

from query import filter
from query import filter_text
from query import filter_number
from query import filter_checkbox

from query import sorts
from query import sort_by_timestamp

from setting import setting

notion_api_key = setting.notion_api_key
db_id = setting.db_id
db3_id = setting.db3_id
db4_id = setting.db4_id

import logging
# logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

# format=f"%(asctime)s %(module)s.%(funcName)s() \t: %(message)s",
logging.basicConfig(
    format=f"%(asctime)s \t: %(message)s",
    level=logging.DEBUG,
)


def ntest_get_database():
    notion = Notion(notion_api_key)

    d1 = notion.get_database(db_id)
    ftext = filter(filter.AND)
    ftext.add(filter_text(filter_text.TYPE_TITLE).contains('api'))

    pprint(d1._filter_and_sort(notion_filter=ftext))


def each_filter_text(filter_base, db):
    if 'text' not in db.test_types:
        return

    filter_conditions = [
        filter_text(filter_text.TYPE_TITLE).equals('관측일기'),
        filter_text(filter_text.TYPE_TITLE).does_not_equal('api'),
        filter_text(filter_text.TYPE_TITLE).contains('api'),
        filter_text(filter_text.TYPE_TITLE).does_not_contain('api'),
        filter_text(filter_text.TYPE_TITLE).starts_with('창'),
        filter_text(filter_text.TYPE_TITLE).ends_with('평가'),
        # filter_text(filter_text.TYPE_TITLE).equals('관측일기'),

    ]
    for f in filter_conditions:
        filter_base.clear()
        filter_base.add(f)
        result = len(db._filter_and_sort(notion_filter=filter_base)[1]['results'])
        print('result:', str(filter_base._body), result)

        if not result:
            raise Exception('No result:' + str(filter_base._body))


def each_filter_number(filter_base, db):
    if 'number' not in db.test_types:
        return

    filter_conditions = [
        filter_number('이용금액').equals(12500),
        filter_number('이용금액').does_not_equal(12500),
        filter_number('이용금액').greater_than(12500),
        filter_number('이용금액').less_than(12500),
        filter_number('이용금액').greater_than_or_equal_to(12500),
        filter_number('이용금액').less_than_or_equal_to(12500),


    ]
    for f in filter_conditions:
        filter_base.clear()
        filter_base.add(f)
        result = len(db._filter_and_sort(notion_filter=filter_base)[1]['results'])
        print('result:', str(filter_base._body), result)

        if not result:
            raise Exception('No result:' + str(filter_base._body))


def each_filter_check_box(filter_base, db):
    if 'check_box' not in db.test_types:
        return

    filter_conditions = [
        [filter_checkbox('열').equals(True)],
        [filter_checkbox('열').does_not_equal(True)],
        [filter_checkbox('열').equals(False), filter_checkbox('열').does_not_equal(False)],

    ]
    for f in filter_conditions:
        filter_base.clear()
        for each_f in f:
            filter_base.add(each_f)

        # print(db.query(filter=filter_base)[1])
        # result = len(['results'])
        result = db._filter_and_sort(notion_filter=filter_base)[1]


        if 'results' in result:
            print('result:', str(filter_base._body), len(result['results']))
        else:
            print('No result:' + str(filter_base._body))


def each_filter_queried(filter_base, db):
    if 'queried_page_iterator' not in db.test_types:
        return

    filter_conditions = [
        # [filter_text(filter_text.TYPE_TEXT, '날짜').is_not_empty()]
        # [filter_text(filter_text.TYPE_TEXT, '날짜').is_empty()],
        [filter_number('금액').equals(200000)],
    ]
    for f in filter_conditions:
        filter_base.clear()
        for each_f in f:
            filter_base.add(each_f)

        result = db._filter_and_sort(notion_filter=filter_base, page_size=100)
        for i in result:
            print(i)

        print(i.properties)


def each_database(db):
    filters = [
        filter(),
        filter(filter.AND),
    ]

    for f in filters:
        each_filter_text(f, db)
        each_filter_number(f, db)
        each_filter_check_box(f, db)
        each_filter_queried(f, db)

def test_get_database():
    notion = Notion(notion_api_key)

    # d1 = notion.get_database(db_id)
    # d1.test_types = ['text']
    # d2 = notion.get_database('a16b9c30da6d4f6481f7cb3a7e654199')
    # d1.test_types = ['number']
    d3 = notion.get_database(db3_id)
    d3.test_types = ['check_box']

    d4 = notion.get_database(db4_id)
    d4.test_types = ['queried_page_iterator']
    database_cases = [
        # d1,
        # d2,
        # d3,
        d4,
    ]

    # assert False
    # https://www.notion.so/seongyo/989cc0ed5d164c6bb7fe852e51fb8e19?v=4cfc5a55c6d64fc0bf4942591876faff
    for d in database_cases:
        print(d)
        each_database(d)


