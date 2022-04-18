from unittest import TestCase
from pprint import pprint

import logging

log_format = '%(asctime)s [%(filename)s:%(lineno)s|%(levelname)s] %(funcName)s(): %(message)s'

# logging.basicConfig(format=log_format, level=logging.DEBUG)
logging.basicConfig(format=log_format, level=logging.INFO)


import notion_api.notion
from notion_api.objects import Database
from notion_api.objects import Page
from notion_api.functions import pdir
from query import sorts
from query import sort_by_timestamp
notion = notion_api.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')

# log = notion_api.notion._log
# # log.setLevel(logging.DEBUG)
# log.debug('test')


# d3 = notion.get_database('44d6b8fda2734f04968a771a79f97fb6')  # test1

def pdir(obj, level='public'):
    attr_list = dir(obj)
    if level == 'hide':
        attr_list = [a for a in attr_list if a[:2] != '__']
    elif level == 'public':
        attr_list = [a for a in attr_list if a[0] != '_']
    return attr_list


class TestDatabase(TestCase):

    def test_filter(self):
        import notion_api.notion

        notion = notion_api.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')
        filter_table = notion.get_database('e8108c53c9cf42259878954a289842fe')
        result = [*filter_table._filter_and_sort()]
        print(*result, sep="\n")


class TestPage(TestCase):
    def test_get_properties(self):
        import notion_api.notion
        notion = notion_api.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')

        # filter_table = notion.get_database('e8108c53c9cf42259878954a289842fe')
        test_page = notion.get_page('e8d28d7c0056414582fe23f2ab7c3928')
        p = test_page.get_properties()
        pprint(p)


class TestDatabase(TestCase):

    def test_create_db_property(self):
        """

        :return:
        """
        import notion_api.notion
        notion = notion_api.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')
        property_table = notion.get_database('d3bf7c7d8c714f13b31638bfbcd13b36')
        d3 = notion.get_database('44d6b8fda2734f04968a771a79f97fb6')  # test1


        # print(property_table.id)
        # print(d3.id)
        # print(property_table.created_by)
        # print(d3.created_by)
        # print(property_table.properties.keys())
        header = (
            'Property',
            'Type',
            'class level',
            'class1',
            'class2',
            'class3',
            'class4',
            'comment',
            'Description',
            'Example value',
            'Mutability',
            'mutable_event_type',
            'specification',
            '하위설명'
        )

        array = list()

        # for e in property_table.get_tuples(property_table.query(), columns_select=header, header=False):
        for e in property_table.get_as_dictionaries(property_table._filter_and_sort(), columns_select=header):
            if not (
                    e['class level'] == 'class2'
                    and e['class1'] == 'page'
                    and e['class2'] == 'properties'
                    and 'common' not in e['specification']
            ):
                continue
            array.append(e)

        # pprint(array)

        props_dict = dict()
        for e in array:
            props_dict[e['Property']] = e
        # # print(len(props), len(set(props)))
        pprint(props_dict)
        # # print(*props_dict, sep="\n")


    def test_get_databae(self):
        import notion_api.notion
        from pprint import pprint
        from notion_api.query import filter
        import time
        notion = notion_api.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')
        d3 = notion.get_database('44d6b8fda2734f04968a771a79f97fb6')  # test1

        # print(d3, pdir(d3))
        # print('d3.id', d3.id)
        # print(d3.properties._parent)
        # print("d3.properties['Email2']", d3.properties['Email2'])
        # print("d3.properties['Email2']", repr(d3.properties['Email2']))
        # print("d3.properties['Email2']", d3.properties['Email2'].id)
        # e = d3.properties['Email']
        # print('e._object', e._parent)
        # e.name = 'Email'

    def test_update_type(self):
        test_table = notion.get_database('f7001a895f39403eae3d90b6451639f4')  # Tast Case Table2 : Simple Test
        print(test_table.properties.keys())
        n = test_table.properties['Number2']
        # print(n)
        n.type = 'number'

    def test_create_page(self):
        test_table = notion.get_database('44d6b8fda2734f04968a771a79f97fb6') # Tast Case Table1 : Full Test
        print(test_table.properties.keys())

        properties = {
            'Title': '제목을 넣었습니다.',
            'Number': 123,
            'Checkbox': True,
            'PhoneNumber': '010100101010',
            'text': 'some text',
        }

        page = test_table.create_page(properties)
        print(page)

        # test_table.create_page()


class Test_PropertyObject(TestCase):
    def test_properties(self):
        import notion_api.notion
        notion = notion_api.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')

        # filter_table = notion.get_database('e8108c53c9cf42259878954a289842fe')
        test_page = notion.get_page('e8d28d7c0056414582fe23f2ab7c3928')
        # test_table = notion.get_database('44d6b8fda2734f04968a771a79f97fb6') # Tast Case Table1 : Full Test
        test_table = notion.get_database('f7001a895f39403eae3d90b6451639f4')  # Tast Case Table2 : Simple Test
        dp = test_table.properties
        p = test_page.properties
        n = p['Number']
        dn = dp['Number']

        print(pdir(n, 'hide'))
        print(pdir(dn, 'hide'))


