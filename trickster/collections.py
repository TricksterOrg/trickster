"""Usefull collections."""

import abc
from typing import Any, Dict, Generic, Iterator, List, Optional, TypeVar


class IdItem(abc.ABC):
    """Item containing id and serializable to json."""

    def __init__(self, id: str):
        self.id = id

    def serialize(self) -> Dict[str, Any]:
        """Serialize item to json."""
        return {'id': self.id}


IdItemType = TypeVar('IdItemType', bound=IdItem)


class IdList(Generic[IdItemType]):
    """List of items with ID."""

    def __init__(self) -> None:
        self.items: List[IdItemType] = []

    def get(self, key: str) -> Optional[IdItemType]:
        """Get item with given key or None."""
        for item in self.items:
            if item.id == key:
                return item
        return None

    def __iter__(self) -> Iterator[IdItemType]:
        """Iterate over all items in list."""
        yield from self.items

    def serialize(self) -> List[Dict[str, Any]]:
        """Convert list to json."""
        return [item.serialize() for item in self]

    def __contains__(self, key: str) -> bool:
        """Return True if item with given key is present in list."""
        for item in self:
            if item.id == key:
                return True
        return False

    def __len__(self) -> int:
        """Get number of elements in list."""
        return len(self.items)

    def index(self, item_id: str) -> Optional[int]:
        """Get index of item in list of None."""
        for index, present_item in enumerate(self.items):
            if present_item.id == item_id:
                return index
        return None

    def add(self, item: IdItemType) -> None:
        """Add item to list."""
        if item.id in self:
            raise KeyError(f'Cannot insert item "{item.id}", key already exists.')
        self.items.append(item)

    def remove(self, item_id: str) -> None:
        """Remove item from list."""
        if (index := self.index(item_id)) is not None:
            del self.items[index]

    def replace(self, item_id: str, item: IdItemType) -> None:
        """Replace item on given index with new item."""
        if (index := self.index(item_id)) is None:
            raise KeyError(f'Item id "{item_id}" does\'t exist.')
        self.items[index] = item
