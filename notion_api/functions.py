from functools import wraps as _wraps
from typing import List
from typing import Any
from typing import Dict
from typing import Callable


def pdir(obj: object, level: str = 'public') -> List[str]:
    attr_list = dir(obj)
    if level == 'hide':
        attr_list = [a for a in attr_list if a[:2] != '__']
    elif level == 'public':
        attr_list = [a for a in attr_list if a[0] != '_']
    return attr_list


def from_rich_text_array_to_plain_text(array: List[Dict[str, Any]]) -> str:
    return ' '.join([e['plain_text'].replace(u'\xa0', u' ') for e in array])


def parse_date_object(date_obj: Dict[str, Any]) -> str:
    """
    parse date object to string format.

    :param date_obj:
    :return:
    """
    if not date_obj:
        return ''
    content: str = date_obj['start']
    if date_obj['end']:
        content += '~' + date_obj['end']
    return content


def from_plain_text_to_rich_text_array(string: str) -> List[Dict[str, Any]]:
    return [{"text": {"content": string}}]


def notion_object_init_handler(init_function: Callable[[Any], None]) -> object:
    """
    All notion object having '_update' method should be wrapped by 'this decorator'.
    If '__init__' method is called with  'key' keyword argument, wrapper will not execute it
    because '__new__' method executes with '__init__' to handle namespace.

    :param init_function: function
    :return:
    """

    @_wraps(init_function)
    def wrapper_function(*args: List[Any], **kwargs: Dict[str, Any]) -> object:  # type: ignore
        if 'instance_id' not in kwargs:
            return init_function(*args, **kwargs)

    return wrapper_function

