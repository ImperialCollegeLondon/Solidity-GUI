"""Submodule related to individual form fields.

Fields are used to build up forms and represent semantically distinct items of
data. This is entirely analogous to fields used in libraries such as Marshmallow,
WTForms or Django Forms. Fields are intended only to be used as attributes of Form
classes.

For our purposes, a Field class ties together a Marshmallow field class and a Widget
class with additional data for display to the user. The Marshmallow class of a Field
effectively defines the underlying datatype and is used by a Form instance to construct
a Marshmallow Schema for data validation. Validator functions may also be provided to a
Field and these are passed to the Marshmallow field when the Schema is constructed.

The Widget class specified for a Field represents the actual GUI component that should
be presented to the user. All usable Field classes provide a default Widget class
however the Widget class may also be provided at initialisation time.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from typing import Any, Generic, TypeVar

from marshmallow import fields as marshmallow_fields
from marshmallow import validate
from PySide6.QtWidgets import QWidget

from .info import FieldInfo
from .widgets import (
    CheckBoxWidget,
    ComboBox,
    DoubleSpinBoxWidget,
    LargeFloatLineWidget,
    LineEditWidget,
    SpinBoxWidget,
    TrueWidget,
    Widget,
)

DataType = TypeVar("DataType")


class BaseField(ABC, Generic[DataType]):
    """Base class for all Fields."""

    _marshmallow_field: type[marshmallow_fields.Field]
    _default_widget: Widget

    def __init__(
        self,
        length: int,
        display_name: str | None = None,
        description: str | None = None,
        validators: Iterable[Callable] = [],
        widget: Widget | None = None,
        field_validators: list[Callable] = [],
    ):
        """Initialise a new instance.

        Args:
          length: number of values represented by the field
          display_name: human friendly name
          description: human friendly description of the field's purpose
          validators: marshmallow compatible functions to validate individual values
          widget: the GUI widget displayed to the user
          field_validators: marshmallow compatible functions to validate the full field
        """
        self.display_name = display_name
        self.description = description
        self.validators = validators
        self.widget = widget if widget else self._default_widget
        self.length = length
        self.field_validators = field_validators

    def input(self, data: DataType | None = None) -> QWidget:
        """Generates the GUI widget for display to the user.

        Args:
          data: value to pre-populate into the widget
        """
        return self.widget.create(data, self.validators)

    def field_info(
        self,
        name: str,
        data: DataType | list[DataType] | None,
        errors: dict[int, list[str]] = {},
    ) -> FieldInfo:
        """Return a FieldInfo object for this Field.

        Args:
          name: the name of the field
          data: data for pre-population of inputs
          errors: error messages for individual inputs
        """
        header = self.display_name if self.display_name else name
        if data:
            if isinstance(data, list):
                if len(data) != self.length:
                    raise ValueError("Number of data items must match Field length.")
                inputs = [self.input(d) for d in data]
            else:
                if self.length != 1:
                    raise ValueError("Expected a list of data items.")
                inputs = [self.input(data)]
        else:
            inputs = [self.input() for _ in range(self.length)]
        if len(inputs) != self.length:
            raise ValueError("Number of values provided by `data` is incorrect.")

        return FieldInfo(
            input=inputs,
            errors=errors,
            header=header,
            description=self.description,
        )

    @abstractmethod
    def marshmallow(self) -> marshmallow_fields.Field:
        """Generates a corresponding Marshmallow Field for use in a Schema."""
        pass

    @abstractmethod
    def process(self, inputs: list[QWidget]) -> Any:
        """Return data for the field.

        Args:
          inputs: the gui widget instance(s).
        """


class CompositeField(BaseField, Generic[DataType]):
    """Base class for all Fields that collect multiple values."""

    def process(self, inputs: list[QWidget]) -> list[DataType]:
        """Return data for the field.

        Args:
          inputs: the gui widget instances
        """
        return [self.widget.process(input_) for input_ in inputs]

    def marshmallow(self) -> marshmallow_fields.Field:
        """Generates a corresponding Marshmallow Field for use in a Schema."""
        return marshmallow_fields.List(
            self._marshmallow_field(validate=self.validators),
            validate=self.field_validators,
        )


class SingleField(BaseField, Generic[DataType]):
    """Base class for all Fields that collection single values."""

    def __init__(
        self,
        display_name: str | None = None,
        description: str | None = None,
        validators: Iterable[Callable] = [],
        widget: Widget | None = None,
    ):
        """Initialise a new SingleField instance.

        Args:
          display_name: human friendly name
          description: human friendly description of the field's purpose
          validators: marshmallow compatible functions to validate individual values
          widget: the GUI widget displayed to the user
        """
        super().__init__(
            length=1,
            display_name=display_name,
            description=description,
            validators=validators,
            widget=widget,
            field_validators=[],
        )

    def marshmallow(self) -> marshmallow_fields.Field:
        """Generates a corresponding Marshmallow Field for use in a Schema."""
        return self._marshmallow_field(validate=self.validators)

    def process(self, inputs: list[QWidget]) -> DataType:
        """Return data for the field.

        Args:
          inputs: the gui widget instances
        """
        return self.widget.process(inputs[0])


class StrField(SingleField[str]):
    """A field for string data."""

    _marshmallow_field = marshmallow_fields.Str
    _default_widget = LineEditWidget()


class IntField(SingleField[int]):
    """A field for integer data."""

    _marshmallow_field = marshmallow_fields.Int
    _default_widget = SpinBoxWidget()


class FloatField(SingleField[float]):
    """A field for float data."""

    _marshmallow_field = marshmallow_fields.Float
    _default_widget = DoubleSpinBoxWidget()


class LargeFloatField(SingleField[float]):
    """A field for large float data, requiring a line edit widget."""

    _marshmallow_field = marshmallow_fields.Float
    _default_widget = LargeFloatLineWidget()


class WiderFloatField(FloatField):
    """FloatField with widget providing more decimals."""

    _default_widget = DoubleSpinBoxWidget(decimals=8)


class EvenWiderFloatField(FloatField):
    """FloatField with widget providing even more decimals."""

    _default_widget = DoubleSpinBoxWidget(decimals=10)


class BoolField(SingleField[bool]):
    """A field for float data."""

    _marshmallow_field = marshmallow_fields.Boolean
    _default_widget = CheckBoxWidget()


class VectorField(CompositeField[Iterable[float]]):
    """A field for multiple float values treated as a vector."""

    _marshmallow_field = marshmallow_fields.Float
    _default_widget = DoubleSpinBoxWidget()

    def __init__(
        self,
        length: int = 3,
        display_name: str | None = None,
        description: str | None = None,
        validators: Iterable[Callable] = [],
        widget: Widget | None = None,
        vector_validators: list[Callable] = [],
    ):
        """Initialise a new VectorField instance."""
        super().__init__(
            length,
            display_name,
            description,
            validators,
            widget,
            field_validators=[validate.Length(equal=length)] + vector_validators,
        )


class BlankField(SingleField[bool]):
    """A field that always has a value of True."""

    _marshmallow_field = marshmallow_fields.Boolean
    _default_widget = TrueWidget()

    def __init__(
        self,
        display_name: str | None = None,
        description: str | None = None,
        widget: Widget | None = None,
    ):
        """Initialise a new BlankField instance.

        Args:
          display_name: human friendly name
          description: human friendly description of the field's purpose
          widget: the GUI widget displayed to the user
        """
        super().__init__(
            display_name=display_name,
            description=description,
            validators=[],
            widget=widget,
        )

    def marshmallow(self) -> marshmallow_fields.Boolean:
        """Generates a corresponding Marshmallow Field for use in a Schema."""
        return self._marshmallow_field(validate=validate.Equal(True))


class ComboBoxField(SingleField[str]):
    """A field for selecting from a list of options."""

    _marshmallow_field = marshmallow_fields.Str

    def __init__(
        self,
        items: list[str],
        display_name: str | None = None,
        widget: ComboBox | None = None,
    ):
        """Initialise a new ComboBoxField instance.

        Args:
          items: list of strings representing the options
          display_name: human friendly name
          widget: the GUI widget displayed to the user
        """
        super().__init__(
            display_name=display_name,
            widget=widget if widget else ComboBox(items),
        )
