from typing import Dict, Any

# from notionizer import UserProperty, Database
# from notionizer.objects import NotionUpdateObject, PropertiesProperty, ImmutableProperty, notion_object_init_handler, \
#     HttpRequest, from_plain_text_to_rich_text_array

import notionizer
import notionizer.object_user
import notionizer.properties_property
import notionizer.functions

print(dir(notionizer))

NotionUpdateObject = notionizer.object_basic.NotionUpdateObject
UserProperty = notionizer.object_user.UserProperty
# Database = notionizer.objects.Database
PropertiesProperty = notionizer.properties_property.PropertiesProperty
ImmutableProperty = notionizer.object_user.ImmutableProperty
notion_object_init_handler = notionizer.functions.notion_object_init_handler
HttpRequest = notionizer.http_request.HttpRequest
from_plain_text_to_rich_text_array = notionizer.functions.from_plain_text_to_rich_text_array


class Page(NotionUpdateObject):
    """
    Page Object
    """
    properties = PropertiesProperty(object_type='page')
    id = ImmutableProperty()
    created_by = UserProperty()
    last_edited_by = UserProperty()

    _api_url = 'v1/pages/'

    @notion_object_init_handler
    def __init__(self, request: HttpRequest, data: Dict[str, Any]):

        """

        Args:
            request: Notion._request
            data: returned from ._request
        """

        object_type = data['object']
        assert object_type == 'page', f"data type is not 'database'. (type: {object_type})"
        super().__init__(request, data)

    def __repr__(self) -> str:
        return f"<Page at '{self.id}'>"

    def get_properties(self) -> Dict[str, Any]:
        """
        return value of properties simply
        :return: {'key' : value, ...}
        """
        result = dict()
        for k, v in self.properties.items():
            result[k] = v.get_value()

        return result


    def create_database(self,
                        title: str = '',
                        emoji: str = '',
                        cover: str = '',
                        parent: str = '',
                        properties: list = []
                        ) -> 'Database':

        """

        :param title:
        :param emoji:
        :param cover:
        :param parent:
        :param properties:
        :return: Database

        [Usage]

        from notionizer import Property as Prop
        from notionizer import NumberFormat as NumForm
        from notionizer import OptionColor as OptColor

        db = page.create_database(
            title='DB Title',
            emoji="🎉",
            cover="https://web.image.path/image.jpg",
            properties

            notion.create_database("title", properties = [
                Prop.RichText("text filed"),
                Prop.Number("number", format = NumForm.dollar),
                Prop.Select("select", option = {'opt1': OptColor.blue, 'opt2': OptColor.red}),
                Prop.MultiSelect("multi select", option = {'opt1': OptColor.blue, 'opt2': OptColor.red}),
                ...
                ]
            )
        )

        """

        data: Dict[str, Any] = {'parent': {'type': 'page_id'}, 'properties': {}}
        if parent:
            data['parent']['page_id'] = parent
        else:
            data['parent']['page_id'] = self.id

        if title:
            data['title'] = from_plain_text_to_rich_text_array(title)

        if emoji:
            data['icon'] = {'type': 'emoji'}
            data['icon']['emoji'] = emoji

        if cover:
            data['cover'] = {'type': 'external'}
            data['cover']['external'] = {'url': cover}

        # properties validation
        prop_names = sorted(p.name for p in properties)
        prop_types = sorted(p.prop_type for p in properties)
        assert len(properties) == len(set(prop_names)), f"please check duplicated name of property: {str(prop_names)}"

        # title property should be included.
        if 'title' not in prop_types:
            default_name = 'Name'
            unused_name = default_name
            index = 0
            while unused_name in prop_names:
                index += 1
                unused_name = default_name + str(index).zfill(2)

            data['properties'][unused_name] = {"title": {}}

        for p in properties:
            data['properties'][p.name] = {p.prop_type: {}}

            for opt in p.arguments.keys():
                if opt == 'options':
                    data['properties'][p.name][p.prop_type]['options'] = []
                    for name, color in p.arguments[opt].items():
                        data['properties'][p.name][p.prop_type]['options'].append({'name': name, 'color': color})
                else:
                    data['properties'][p.name][p.prop_type][opt] = p.arguments[opt]

        db_object: 'Database' = __import__('notionizer').objects.Database(*self._request.post('v1/databases/', data))
        return db_object
