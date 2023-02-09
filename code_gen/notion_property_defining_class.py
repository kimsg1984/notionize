class Number:
    def __init__(self, name, number_format=''):
        self.name = name

class Select:
    def __init__(self, name, options={}):

        self.name = name
        self.options = options

class MultiSelect:
    def __init__(self, name, options={}):

        self.name = name
        self.options = options



prop_list = [
    "title",
    "rich_text",
    "number",
    "select",
    "multi_select",
    "date",
    "people",
    "files",
    "checkbox",
    "url",
    "email",
    "phone_number",
    "formula",
    "relation",
    "rollup",
    # "created_time",
    # "created_by",
    # "last_edited_time",
    # "last_edited_by"
]


args_dict = {
    'relation': ['database_id'],
    'rollup': [
        'rollup_property_name',
        'relation_property_name',
        'function',
    ],
}

kwargs_dict = {
    'number': {'format':"''"},
    'select': {'options':"{}"},
    'multi_select': {'options':"{}"},
}

docstring_dict = {
    'number': '''            """

            :param name:
            :param format:

            [Usage]
            from notionizer import NumberFormat as NumForm
            notion.create_database("title", properties = [Prop.Number("number", format = NumForm.dollar), ...])
            """''',
    'select': '''            """

            :param name:
            :param options: dictionary

            [Usage]

            from notionizer import OptionColor as OptColor

            notion.create_database("title", properties = [
                Prop.Select(
                    "prop. name",
                    options={'option name': OptColor.red}
                ), ...
                ]
            )
            """''',
    'multi_select':'''            """
            :param name:
            :param options: dictionary

            [Usage]

            from notionizer import OptionColor as OptColor
            notion.create_database("title", properties = [
                Prop.MultiSelect(
                    "prop. name",
                    options={'option name': OptColor.red}
                ), ...
                ]
            )
            """''',
    'relation': '''            """

            :param name:
            :param database_id: UUID(str)

            [Usage]
            notion.create_database("title", properties = [Prop.Relation("relation", "668d797c-76fa-4934-9b05-ad288df2d136"), ...])
            """''',
        'rollup': '''            """

            :param name:
            :param rollup_property_name: property name from relation(str)
            :param relation_property_name: relation property name (str)
            :param function: count_all, count_values, count_unique_values, count_empty, count_not_empty, percent_empty, percent_not_empty, sum, average, median, min, max, range, show_original (str)

            [Usage]


            from notionizer import RollupFunction as RFunc
            notion.create_database("title", properties = [
                Prop.Rollup(
                    "rollup", 
                    rollup_property_name = "name", 
                    relation_property_name = "Meals",
                    function = RFunc.count,
                    ), ...
                ])
            """''',
}

class_format = """    class {name}:
        def __init__(self, name{parameter}):
{docstring}
            self.name = name
            self.prop_type = '{prop}'
            self.arguments = {{}}
{option}"""


option_statements = """
            if {par}:
                self.arguments['{par}'] = {par}
"""

for prop in prop_list:
    prop_name = prop.title().replace('_', '')
    parameter = ''
    docstring = ''
    option = ''

    if prop in args_dict:
        opt_list = args_dict[prop]
        for par in opt_list:
            parameter += f", {par}"
            option += f"            self.arguments['{par}'] = {par}\n"

    if prop in kwargs_dict:
        opt_dict = kwargs_dict[prop]
        for par in opt_dict.keys():
            parameter += f", {par}={opt_dict[par]}"
            option += option_statements.format(par = par)

    docstring = docstring_dict.get(prop, '')
    # print(prop_name)
    # print(prop)
    print(class_format.format(
        name = prop_name,
        parameter = parameter,
        docstring = docstring,
        prop = prop,
        option = option
        ))