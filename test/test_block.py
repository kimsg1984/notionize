# import sys
# sys.path.append('C:/Users/alp66/Documents/notionized/setting')
# sys.path.append('C:/Users/alp66/Documents/notionized')

import logging

from notionizer import OptionColor



# log_format = '%(lineno)s|%(levelname)s] %(funcName)s(): %(message)s'
log_format = '%(asctime)s [%(filename)s:%(lineno)s|%(levelname)s] %(funcName)s(): %(message)s'

# logging.basicConfig(format=log_format, level=logging.ERROR)
# logging.basicConfig(format=log_format, level=logging.INFO)
logging.basicConfig(format=log_format, level=logging.DEBUG)

log = logging.getLogger(__name__)

from setting import setting
from pprint import pprint

notion_api_key = setting.notion_api_key

from notionizer import Notion
# print(notion_api_key)

def view_without_speacial_method(func):

   """
    A function that filters and displays the attributes and methods of an object, excluding those that start with double underscores (`__`) or single underscores (`_`).

    Parameters:
    func (method): The object for which you want to display the attributes and methods.

    Returns:
    None

    Example:
    >>> class Example:
    ...     def method1(self):
    ...         pass
    ...     def __method2(self):
    ...         pass
    ...
    >>> obj = Example()
    >>> view_without_special_method(obj)
    method1
    """
    for func in dir(func):
        if not func.startswith('__') and not func.startswith('_'):
            print(func)
def wm(item):
    view_without_speacial_method(item)


notion = Notion(notion_api_key)

me = notion.get_me()

# print(me)
# print(type(me))
# print("bot : ",me.bot)
# print("name : ",me.name)
# print("object : ",me.object)
# print("type : ",me.type)
# print(type(me.type))

db = notion.get_block("e9e16d48ba3f4755b81df1bd966c5fba")
# db = notion.get_block("b809926ac85d4d2da79d02071b761b18")
# print(dir(db))
# wm(db)
# print((db.has_children))
# print(dir(db.id))
print("==--=-=-")
# print((db.id))
# print(dir(db.properties))
# print((db.properties))