from unittest import TestCase
from pprint import pprint

import logging

log_format = '%(asctime)s [%(filename)s:%(lineno)s|%(levelname)s] %(funcName)s(): %(message)s'

# logging.basicConfig(format=log_format, level=logging.DEBUG)
logging.basicConfig(format=log_format, level=logging.INFO)

import notionizer.notion
from notionizer.objects import Database
from notionizer import Page, User
# from notionizer.objects import UserObject
from notionizer.functions import pdir
from notionizer.query import sorts
from notionizer.query import sort_by_timestamp

notion = notionizer.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')


# log = notionize.notion._log
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
        import notionizer.notion

        notion = notionizer.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')
        filter_table = notion.get_database('e8108c53c9cf42259878954a289842fe')
        result = [*filter_table._filter_and_sort()]
        print(*result, sep="\n")


class TestPage(TestCase):
    def test_get_properties(self):
        import notionizer.notion
        notion = notionizer.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')

        # filter_table = notion.get_database('e8108c53c9cf42259878954a289842fe')
        test_page = notion.get_page('e8d28d7c0056414582fe23f2ab7c3928')
        p = test_page.get_properties()
        pprint(p)


class TestDatabase(TestCase):

    def test_create_db_property(self):
        """

        :return:
        """
        import notionizer.notion
        notion = notionizer.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')
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
        import notionizer.notion
        from pprint import pprint
        from notionizer.query import filter
        import time
        notion = notionizer.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')
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
        test_table = notion.get_database('44d6b8fda2734f04968a771a79f97fb6')  # Tast Case Table1 : Full Test
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
        import notionizer.notion
        notion = notionizer.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')

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


class TestUser(TestCase):
    def dtest_user(self) -> None:
        test_table = notion.get_database('44d6b8fda2734f04968a771a79f97fb6')  # Tast Case Table1 : Full Test
        user = notion.get_user('1ecee6f3-2456-4778-8fca-f9c77f34f2b9')
        print(user)
        print(repr(user))
        print(repr(test_table))

    def dtest_user(self) -> None:
        test_table = notion.get_database('44d6b8fda2734f04968a771a79f97fb6')  # Tast Case Table1 : Full Test
        user_list = notion.get_all_users()
        print(user_list)

    def dtest_bots(self) -> None:
        user_list = notion.get_me()
        print(user_list)

    def dtest_database(self):
        me = notion.get_me()
        print('me: ', me)
        print('me: ', repr(me))

        # user_obj = UserObject({'object': 'user', 'id': '1ecee6f3-2456-4778-8fca-f9c77f34f2b9'})

        # print(user_obj)
        test_table = notion.get_database('44d6b8fda2734f04968a771a79f97fb6')  # Tast Case Table1 : Full Test
        print(pdir(test_table))
        print(test_table.created_by)
        print(test_table.last_edited_by)

    def dtest_update_info(self):
        test_table = notion.get_database('44d6b8fda2734f04968a771a79f97fb6')  # Tast Case Table1 : Full Test
        # print(test_table.title)
        # test_table.title = '테스트 케이스 테이블'
        # print(test_table.title)
        user = test_table.created_by
        print(user, pdir(user))
        user.update_info()
        print(user, pdir(user))

    def dtest_page(self):
        test_page = notion.get_page('e8d28d7c0056414582fe23f2ab7c3928')
        print(test_page.created_by)
        print(test_page.last_edited_by)
        people = test_page.properties['User']
        print(people, people.type, people.people,  pdir(people), sep=', ')
        print()

        print(repr(people.people[0]))

