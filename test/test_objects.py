from unittest import TestCase
from notionizer import Notion
from notionizer import Property as Prop
from notionizer import NumberFormat as NumForm
from notionizer import OptionColor as OptColor
from notionizer import RollupFunction as RFunc


class TestPage(TestCase):
    def test_get_properties(self):
        self.fail()


class TestPage(TestCase):

    # TODO: build up fully test
    def test_create_database(self):
        notion = Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')
        page = notion.get_page('e8d28d7c0056414582fe23f2ab7c3928')
        db = page.create_database(
            title='식당 리스트',
            # emoji="🎉",
            # cover='https://media.wired.com/photos/5b899992404e112d2df1e94e/master/pass/trash2-01.jpg',
            properties=[
                Prop.RichText("식당 이름"),
                Prop.Number("점수", format=NumForm.dollar),
                Prop.Select("종류", options={'중식': OptColor.blue, '양식': OptColor.red, "한식": OptColor.brown}),
                # Prop.MultiSelect("multi select", options={'opt1': OptColor.blue, 'opt2': OptColor.red}),
                # Prop.Relation("relation", "44d6b8fda2734f04968a771a79f97fb6"),
                # Prop.Rollup(
                #     "rollup",
                #     rollup_property_name="Title",
                #     relation_property_name="relation",
                #     function=RFunc.count,
                # ),
            ]
        )
        # print(page.get_properties())
    def test_option(self):
        notion = Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')



