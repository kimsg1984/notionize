from functools import wraps as _wraps


def _from_rich_text_array_to_plain_text(array):
    return ' '.join([e['plain_text'].replace(u'\xa0', u' ') for e in array])


def _from_plain_text_to_rich_text_array(string):
    return [{"text": {"content": string}, 'plain_text': string}]


def _notion_object_init_handler(init_function):
    """
    All notion object having '_update' method should be wrapped by 'this decorator'.
    If '__init__' method is called with  'key' keyword argument, wrapper will not execute it
    because '__new__' method executes with '__init__' to handle namespace.
    """

    @_wraps(init_function)
    def wrapper_function(*args, **kwargs):
        if 'instance_id' not in kwargs:
            return init_function(*args, **kwargs)

    return wrapper_function