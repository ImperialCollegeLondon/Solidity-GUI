"""Tests covering the Datastore datastructures used in the codebase."""
from solidity_gui.main.datastore import Datastore


def test_datastore_setitem(send_message_mock):
    """Test adding to datastore via __setitem__."""
    datastore = Datastore("foo")
    key, value = 0, 1
    assert len(datastore) == 0
    datastore[key] = value
    send_message_mock.assert_called_once_with(
        datastore.update_topic, key=key, value=value
    )
    assert datastore[key] == value
    assert len(datastore) == 1


def test_datastore_update(send_message_mock):
    """Test adding to datastore via update method."""
    data = ((0, 1), (2, 3))
    datastore = Datastore("foo", data[:1])
    datastore.update(data)
    send_message_mock.assert_any_call(
        datastore.update_topic, key=data[0][0], value=data[0][1]
    )
    send_message_mock.assert_any_call(
        datastore.update_topic, key=data[1][0], value=data[1][1]
    )


def test_datastore_setdefault(send_message_mock):
    """Test adding to datastore via setdefault method."""
    datastore = Datastore("foo")
    key, value = 0, 1
    assert len(datastore) == 0

    out_value = datastore.setdefault(key, value)

    assert len(datastore) == 1
    send_message_mock.assert_called_once_with(
        datastore.update_topic, key=key, value=value
    )
    assert out_value == value


def test_datastore_delitem(send_message_mock):
    """Test removing data from the datastore."""
    key, value = 0, 1
    datastore = Datastore("foo", {key: value})
    send_message_mock.reset_mock()
    assert len(datastore) == 1

    del datastore[key]

    send_message_mock.assert_called_once_with(
        datastore.remove_topic, key=key, value=value
    )
    assert len(datastore) == 0


def test_datastore_pop(send_message_mock):
    """Test removing data from the datastore via the pop method."""
    key, value = 0, 1
    datastore = Datastore("foo", {key: value})
    send_message_mock.reset_mock()
    assert len(datastore) == 1

    out_value = datastore.pop(key)

    send_message_mock.assert_called_once_with(
        datastore.remove_topic, key=key, value=value
    )
    assert out_value == value
    assert len(datastore) == 0


def test_datastore_popitem(send_message_mock):
    """Test removing data from the datastore via the popitem method."""
    key, value = 0, 1
    datastore = Datastore("foo", {key: value})
    send_message_mock.reset_mock()
    assert len(datastore) == 1

    out_key, out_value = datastore.popitem()

    send_message_mock.assert_called_once_with(
        datastore.remove_topic, key=key, value=value
    )
    assert out_value == value
    assert out_key == key
    assert len(datastore) == 0


def test_datastore_clear(send_message_mock):
    """Test removing data from the datastore via the clear method."""
    data = (("key1", "val2"), ("key2", "val2"))
    datastore = Datastore("foo", data)

    datastore.clear()

    for key, value in data:
        send_message_mock.assert_any_call(datastore.remove_topic, key=key, value=value)
