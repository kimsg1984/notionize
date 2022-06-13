
# __all__ = ["query", "notion", "objects", "exception"]

from .notion import Notion

from .objects import User
from .objects import UserProperty
from .objects import Database
from .objects import Page

from .exception import NotionApiException
from .exception import NotionApiPropertyException
from .exception import NotionApiPropertyUnassignedException
from .exception import NotionApiQueoryException

__version__ = "0.0.1"

def __go(lcls):
    global __all__
    import inspect as _inspect

    __all__ = sorted(
        name
        for name, obj in lcls.items()
        if not (name.startswith("_") or _inspect.ismodule(obj))
    )

__go(locals())

