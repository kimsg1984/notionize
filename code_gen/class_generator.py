"""
This script used to generate  'properties_page.py' and 'properties_db.py' before refactoring from notion-api
to notionizer. TO REUSE THIS, path and module name should be adjusted.
"""

page_properties_file = '/home/sungyo/PycharmProjects/notion-api/notion_api/properties_page.py'
db_properties_file = '/home/sungyo/PycharmProjects/notion-api/notion_api/properties_db.py'

import pprint

import sys

sys.path.append('/home/sungyo/PycharmProjects/notion-api/')

import notionizer.notion


def get_properties_name(columns, class_type):
    array = list()

    # for e in property_table.get_tuples(property_table.query(), columns_select=header, header=False):
    for e in columns:
        if not (
                e['class level'] == 'class2'
                and e['class1'] == class_type
                and e['class2'] == 'properties'
                and 'common' not in e['specification']
        ):
            continue
        array.append(e)
    props_dict = dict()
    for e in array:
        props_dict[e['Property']] = e

    return props_dict



properties_class_format = '''class {class_type}Property{property_title}({class_type}PropertyObject):
    """
    '{class_type}Property{property_title}'
    """
{properties}
{method}


'''

page_properties_file_header = \
'''from notion_api.functions import from_rich_text_array_to_plain_text
from notion_api.functions import parse_date_object
from notion_api.object_adt import MutableProperty
from notion_api.properties_basic import PagePropertyObject
from notion_api.object_basic import UserObject
from typing import Any, Dict, List


def parse_value_object(obj: Any) -> Any:
    """
    parse value of 'formula' and 'rollup'. 

    """
    obj_type = obj['type']
    value = obj[obj_type]
            
    if obj_type == 'date':
        return parse_date_object(value)

    elif obj_type == 'array':
        return [parse_value_object(e) for e in value]
    
    # 'number', 'string', 'boolean'
    else:
        return value


'''


db_properties_file_header = \
"""from notion_api.properties_basic import DbPropertyObject
from notion_api.properties_basic import TitleProperty
from notion_api.object_adt import DictionaryObject
from notion_api.functions import from_plain_text_to_rich_text_array
from typing import Any
from typing import Dict


"""

page_specific_property = {
    # 'title':'TitleProperty()'
}

db_specific_property = {
    'title':'    title = TitleProperty()',
    'relation':'    relation: DictionaryObject',
}




page_specific_method = {
    'rich_text': '''
    def get_value(self) -> Any:
        """
        parse 'rich_text' to plain 'string' and return
        """
        return from_rich_text_array_to_plain_text(self.rich_text)''',
    'title': '''
    def get_value(self) -> Any:
        """
        parse 'rich_text' to plain 'string' and return
        """
        return from_rich_text_array_to_plain_text(self.title)''',
    
    'date':'''
    def get_value(self) -> Any:
        """
        parse 'date object'
        """
        return parse_date_object(self.date)''',
    
    'formula':'''
    def get_value(self) -> Any:
        """
        parse 'formula object'
        """
        return parse_value_object(self.formula)
        ''',
    
    'rollup':'''
    def get_value(self) -> Any:
        """
        parse 'rollup object'
        """
        return parse_value_object(self.rollup)''',
    'people': '''
    def __init__(self, parent: Any, data: Dict[str, Any], parent_type: str, name: str, force_new: bool = False):
        """

        :param parent: PropertiesProperty
        :param data:
        :param parent_type:
        :param name:
        :param force_new:
        """

        user_list: List[UserObject] = list()
        object_list: List[Dict[str, Any]] = data['people']
        for e in object_list:
            user_list.append(UserObject(e))
        data['people'] = user_list
        super().__init__(parent, data, parent_type, name)''',
}


db_specific_method = {
    'title': '''
    def _convert_to_update(self, value: str) -> Dict[str, Any]:
        """
        convert value to 'title' update from.

        :param value: str
        :return: dictionary
        """
        return {'title': from_plain_text_to_rich_text_array(value)}''',

    'text': '''
    def _convert_to_update(self, value: Any) -> Any:
        """
        convert value to 'text' update from.

        :param value: str or list
        :return: dictionary
        """
        if type(value) is str:
            return {'rich_text': from_plain_text_to_rich_text_array(value)}
        elif type(value) is list:
            return value''',

}



# execlude_list_page = ['title']
execlude_list_page = []
execlude_list_db = []

page_data = {}

validation_map = {
    'array of user objects': '(list, )',
    'boolean': '(bool, )',
    'string': '(str, )',
    'array of file references': '(list, )',
    'array of multi-select option objects.': '(list, )',
    'rich_text': '(str, list)',
    'number': '(int, )',
    'object': '(dict, )',
}

def generate_class(properties, class_type, properties_file, properties_file_header):
    open(properties_file, 'w').write(properties_file_header)
    for k, v in properties.items():
        title = k
        title_splited = title.split('_')
        title =  ''.join([ t.capitalize() for t in title_splited])
        
        # print(v)
        property_name = v['Property']
        property_type = v['Type']
        mutability = v['Mutability']
        properties = ''
        method = ''

        # gather page data:
        if class_type == 'Page':
            page_data[property_name] = {'type': property_type, 'multbility': mutability, 'title':title}

        if class_type == 'Page' and property_name in execlude_list_page:
            continue

        if class_type == 'Db' and property_name in execlude_list_db:
            continue
        

        # property
        properties += f"    _type_defined = '{property_name}'\n"
        if v['Mutability'] == 'mutable' and property_type in ['string', 'number', 'boolean']:
            properties += f"    {property_name} = MutableProperty()\n"

        # validation
        if class_type == 'Db':
            data = {}
            if property_name in page_data:
                data = page_data[property_name]
            else:
                if property_name == 'text':
                    data = page_data['rich_text']
                # print('property_name:', property_name, 'title:', title)
                else:
                    raise Exception(" error")


            if data['multbility'] == 'mutable':
                properties += f"    _mutable = True\n"
                # print(f"'{data['type']}': '',")
                print(validation_map[data['type']])
                properties += f"    _input_validation = {validation_map[data['type']]}\n"
            else:
                properties += f"    _mutable = False\n"

            # print('property_type:', property_type)
            if property_type in db_specific_property:
                properties += db_specific_property[property_type]

            if property_name in db_specific_property:
                properties += db_specific_property[property_name]

            if property_name in db_specific_method:
                method += db_specific_method[property_name]


        # page
        else:
            if property_type in page_specific_property:
                properties += page_specific_property[property_type]

            # method
            if property_name in page_specific_method:
                method += page_specific_method[property_name]

        properties = properties.rstrip()
        # print(f"[{properties}]")
        class_str = properties_class_format.format(
            class_type = class_type
            ,property_title = title
            ,property_name = property_name
            ,properties = properties
            ,method = method
            )
        
        class_str = class_str.strip()
        class_str += '\n\n\n'
        # print(class_str, end='')
        # print(v)

        open(properties_file, 'a').write(class_str)
        

def generate_page_properties_class():

    properties = get_properties_name(columns, 'page')
    generate_class(properties, 'Page', page_properties_file, page_properties_file_header)


def generate_db_properties_class():

    properties = get_properties_name(columns, 'database')
    generate_class(properties, 'Db', db_properties_file, db_properties_file_header)



if __name__  == '__main__':
    
    update = False
    # update = True

    if update:
        notion = notion_api.notion.Notion('secret_rvDkx9qH8AVG3aKBVwZ4r5Byo75uoAPMrQ1I6bo4d6G')
        property_table = notion.get_database('d3bf7c7d8c714f13b31638bfbcd13b36')

        columns = property_table.get_as_dictionaries(property_table.query())
        file = open('columns.py', 'w')

        file.write(f"columns = {pprint.pformat(columns)}")

    

    from columns import columns


    generate_page_properties_class()
    generate_db_properties_class()

    # pprint.pprint(page_data)
    pass