"""Tests covering the Datastore datastructures used in the codebase."""
from meshio import Mesh

from solidity_gui.main.datastore import Datastore
from solidity_gui.main.material import (
    Material,
    MaterialAssignment,
    material_assignment_datastore,
    material_datastore,
)
from solidity_gui.main.meshes import mesh_datastore


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


def _setup_assignments_sync_test():
    """Common logic for tests of material_assignment_datastore sync behaviour."""
    material = Material(name="foo")
    material_id = material_datastore.add(material)

    cell_set_name = "cell_set_name"
    mesh = Mesh(points=[], cells={"line": []}, cell_sets={cell_set_name: [[]]})
    mesh_id = mesh_datastore.add(mesh)

    assignment = MaterialAssignment(
        material_id=material_id, cell_set_name=cell_set_name
    )
    material_assignment_datastore.add(assignment)
    return material_id, mesh_id


def test_sync_assignments_material_removed():
    """Check sync of material_assignment_datastore when a material is deleted."""
    material_id, _ = _setup_assignments_sync_test()
    assert len(material_assignment_datastore) == 1

    del material_datastore[material_id]

    assert len(material_assignment_datastore) == 0


def test_sync_assignments_mesh_removed():
    """Check sync of material_assignment_datastore when a mesh is deleted."""
    _, mesh_id = _setup_assignments_sync_test()

    del mesh_datastore[mesh_id]

    assert len(material_assignment_datastore) == 0
