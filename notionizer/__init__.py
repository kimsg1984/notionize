
# __all__ = ["query", "notion", "objects", "exception"]

from .notion import Notion

from .object_user import UserProperty, User
from .objects import Database
from .object_page import Page
from .objects import Property
from .enum import OptionColor, NumberFormat, RollupFunction

from .exception import NotionApiException
from .exception import NotionApiPropertyException
from .exception import NotionApiPropertyUnassignedException
from .exception import NotionApiQueoryException

__version__ = "0.0.1"


def __go(lcls) -> None:  # type: ignore
    global __all__
    import inspect as _inspect

    __all__ = sorted(  # type: ignore
        name
        for name, obj in lcls.items()
        if not (name.startswith("_") or _inspect.ismodule(obj))
    )


__go(locals())

