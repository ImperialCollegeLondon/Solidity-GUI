"""A module for storage and communication of data within the application."""
from collections import UserDict
from typing import Any, TypeVar

import meshio
from pubsub import pub

KeyType = TypeVar("KeyType")
ValueType = TypeVar("ValueType")


class Datastore(UserDict[KeyType, ValueType]):
    """UserDict subclass implementing an observer pattern for data updates."""

    def __init__(self, name: str, *args: Any, **kwargs: Any):
        """Create a new instance.

        Args:
          name: used to identify pubsub messages sent by this instance
          *args: passed to UserDict.__init__
          **kwargs: passed to UserDict.__init__
        """
        self.name = name
        super().__init__(*args, **kwargs)

    def __setitem__(self, key: KeyType, value: ValueType) -> None:
        """Set an item in the datastore and signal via pubsub.

        Once the item has been set a pubsub message is sent. The message topic is
        '{self.name}.add' if the key was not previously present and '{self.name}.update'
        if it was. Both key and value are sent as data.
        """
        super().__setitem__(key, value)
        pub.sendMessage(self.update_topic, key=key, value=value)

    def __delitem__(self, key: KeyType) -> None:
        """Remove an item from the datastore and signal via pubsub.

        The pubsub message topic is of the form '{self.name}.remove' with both the key
        and corresponding value sent as data.
        """
        value = self.data[key]
        super().__delitem__(key)
        pub.sendMessage(self.remove_topic, key=key, value=value)

    @property
    def update_topic(self) -> str:
        """Message topic sent when adding items to Datastore."""
        return f"{self.name}.update"

    @property
    def remove_topic(self) -> str:
        """Message topic sent when removing items from Datastore."""
        return f"{self.name}.remove"


class MeshDatastore(Datastore[str, meshio.Mesh]):
    """Example DataStore subclass with concretised types."""


mesh_datastore = MeshDatastore("geometry_meshes")
"""Example datastore instance"""
