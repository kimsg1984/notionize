from notionizer.object_adt import DictionaryObject, ImmutableProperty
from notionizer.object_basic import _log
from notionizer.properties_basic import PropertyObject, PagePropertyObject, DbPropertyObject

import notionizer.properties_page
import notionizer.properties_db
from typing import Any
from typing import Dict
from typing import Optional


class PropertiesProperty(DictionaryObject, ImmutableProperty):
    """
    'PropertiesProperty' for 'Database' and 'Page'. Mutable Type
    """

    """
    '_parent' property is assigned with every '__get__' and '__set__' method call event for pointing to
    proper '_data' object.
    """
    _parent: Any

    def __new__(cls, object_type: str) -> 'PropertiesProperty':

        super_cls = super(PropertiesProperty, cls)
        notion_ins = super_cls.__new__(cls)

        _log.debug("PropertiesProperty: " + str(cls))

        return notion_ins

    def __init__(self, object_type: str):
        """
        :param object_type: 'database' or 'page'.
        """
        assert object_type in ['database', 'page']
        self._parent_object_type = object_type
        super().__init__('properties')

    @property
    def _data(self) -> Dict[str, Any]:
        """
        override '_data' property to be a descriptor.
        :return: DictionaryObject
        """
        data: Dict[str, Any] = getattr(self._parent, self.private_name)
        return data

    def __get__(self, owner: object, object_type: Optional[object] = None) -> 'PropertiesProperty':
        """
        before call '__set_item__' or '__get_item__' method, install call itself by '__get__' method.
        """
        self._parent = owner
        return self

    def __set__(self, owner, value: DictionaryObject):

        self.__set_name__(owner, self.name)

        if not self._check_assigned(owner):
            setattr(owner, self.private_name, dict())
        mutable_status = self._mutable
        self._parent = owner
        self._mutable = True
        if self._parent_object_type == 'database':
            properties_mapper = database_properties_mapper
        elif self._parent_object_type == 'page':
            properties_mapper = page_properties_mapper
        else:
            raise NotImplementedError(f"'{self._parent_object_type}' object is not implemented")

        for k, v in value.items():
            property_type: str = v['type']
            if self._parent_object_type == 'database' and property_type == 'rich_text':
                property_type = 'text'

            if property_type in properties_mapper:

                property_cls: PropertyObject = properties_mapper.get(property_type)
                property_ins: PropertyObject = property_cls(self, v, parent_type=self._parent_object_type, name=k)
            else:
                if self._parent_object_type == 'database':
                    property_ins: DbPropertyObject = DbPropertyObject(self, v, parent_type=self._parent_object_type,
                                                                      force_new=True, name=k)
                elif self._parent_object_type == 'page':
                    property_ins: PagePropertyObject = PagePropertyObject(self, v, parent_type=self._parent_object_type,
                                                                          force_new=True, name=k)
            self.__setitem__(k, property_ins)
        self._mutable = mutable_status

    def _update(self, property_name, data):
        """
        generate 'update content' and call '_update' method of '_parent' object.

        :param property_name:
        :param data:
        :return:
        """
        _log.debug(f"self._parent: {self._parent}")
        self._parent._update('properties', {property_name: data})


database_properties_mapper = dict()
page_properties_mapper = dict()


"""
Dynamic Properties Descriptor Assignment
: depend on 'PropertiesProperty'
"""

for key in dir(notionizer.properties_db):
    db_keyword = 'DbProperty'
    if key[:len(db_keyword)] == db_keyword:
        property_cls_db: DbPropertyObject = getattr(notionizer.properties_db, key)
        database_properties_mapper[property_cls_db._type_defined] = property_cls_db

for key in dir(notionizer.properties_page):
    page_keyword = 'PageProperty'
    if key[:len(page_keyword)] == page_keyword:
        property_cls_page: PagePropertyObject = getattr(notionizer.properties_page, key)
        page_properties_mapper[property_cls_page._type_defined] = property_cls_page
