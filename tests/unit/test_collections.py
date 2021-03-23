import pytest

from trickster.collections import IdItem, IdList


class Item(IdItem):
    def __init__(self, id):
        self.id = id


@pytest.mark.unit
class TestIdList:
    def test_initialize_empty_idlist(self):
        item_list = IdList()
        assert item_list.items == []

    def test_add_item_to_empty_list(self):
        item_list = IdList()
        item = Item('id1')
        item_list.add(item)
        assert len(item_list) == 1
        assert item_list.items[0] is item

    def test_adding_multiple_items_preserves_order(self):
        item_list = IdList()
        item1 = Item('id1')
        item2 = Item('id2')
        item_list.add(item1)
        item_list.add(item2)
        assert len(item_list) == 2
        assert item_list.items[0] is item1
        assert item_list.items[1] is item2

    def test_add_item_that_already_exists_raises_exception(self):
        item_list = IdList()
        item_list.add(Item('id1'))
        item = Item('id1')
        with pytest.raises(KeyError):
            item_list.add(item)

    def test_contains_returns_false_for_not_present_item(self):
        item_list = IdList()
        assert 'id' not in item_list

    def test_contains_returns_false_for_present_item(self):
        item_list = IdList()
        item_list.add(Item('id1'))
        item_list.add(Item('id2'))
        assert 'id1' in item_list
        assert 'id2' in item_list

    def test_get_index_of_item(self):
        item_list = IdList()
        item_list.add(Item('id1'))
        item_list.add(Item('id2'))
        item_list.add(Item('id3'))
        assert item_list.index('id2') == 1

    def test_get_index_of_not_present_item(self):
        item_list = IdList()
        assert item_list.index('id') is None

    def test_get_not_present_item(self):
        item_list = IdList()
        assert item_list.get('id') is None

    def test_get_present_item(self):
        item_list = IdList()
        item1 = Item('id1')
        item2 = Item('id2')
        item_list.add(item1)
        item_list.add(item2)
        assert item_list.get('id1') is item1
        assert item_list.get('id2') is item2

    def test_serialize_empty_list(self):
        item_list = IdList()
        assert item_list.serialize() == []

    def test_serialize_list_with_items(self):
        item_list = IdList()
        item1 = Item('id1')
        item2 = Item('id2')
        item_list.add(item1)
        item_list.add(item2)
        assert item_list.serialize() == [
            item1.serialize(), item2.serialize()
        ]

    def test_delete_item(self):
        item_list = IdList()
        item_list.add(Item('id1'))
        item_list.remove('id1')
        assert len(item_list) == 0

    def test_delete_not_present_item(self):
        item_list = IdList()
        item_list.remove('id1')
        assert len(item_list) == 0

    def test_replacing_item_preserves_order(self):
        item_list = IdList()
        item1 = Item('id1')
        item2 = Item('id2')
        item3 = Item('id3')
        item4 = Item('id4')
        item_list.add(item1)
        item_list.add(item2)
        item_list.add(item3)
        item_list.replace('id2', item4)
        assert item_list.items == [item1, item4, item3]

    def test_replace_not_present_item_raises_exception(self):
        item_list = IdList()
        with pytest.raises(KeyError):
            item_list.replace('id_doesnt_exist', Item('id1'))
