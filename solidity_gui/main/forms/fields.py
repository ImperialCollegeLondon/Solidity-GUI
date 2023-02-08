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

from typing import Callable, Dict, Generic, Iterable, List, Optional, Type, TypeVar

from marshmallow import fields as marshmallow_fields
from marshmallow import validate
from PySide6.QtWidgets import QWidget

from .info import FieldInfo
from .widgets import DoubleSpinBoxWidget, LineEditWidget, SpinBoxWidget, Widget

DataType = TypeVar("DataType")


class BaseField(Generic[DataType]):
    """Base class for all Fields."""

    _marshmallow_field: Type[marshmallow_fields.Field]
    _default_widget_class: Widget

    def __init__(
        self,
        length: int,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        validators: Iterable[Callable] = [],
        widget_class: Optional[Widget] = None,
        field_validators: List[Callable] = [],
    ):
        """Initialise a new instance.

        Args:
          length: number of values represented by the field
          display_name: human friendly name
          description: human friendly description of the field's purpose
          validators: marshmallow compatible functions to validate individual values
          widget_class: the GUI widget displayed to the user
          field_validators: marshmallow compatible functions to validate the full field
        """
        self.display_name = display_name
        self.description = description
        self.validators = validators
        self.widget_class = widget_class if widget_class else self._default_widget_class
        self.length = length
        self.field_validators = field_validators

    def input(self, data: Optional[DataType] = None) -> QWidget:
        """Generates the GUI widget for display to the user.

        Args:
          data: value to pre-populate into the widget
        """
        return self.widget_class.input(data, self.validators)

    def field_info(
        self,
        name: str,
        data: Optional[DataType | List[DataType]],
        errors: Dict[int, List[str]] = {},
    ) -> FieldInfo:
        """Return a FieldInfo object for this Field."""
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

    def marshmallow(self) -> marshmallow_fields.Field:
        """Generates a corresponding Marshmallow Field for use in a Schema."""
        return marshmallow_fields.List(
            marshmallow_fields.Float(validate=self.validators),
            validate=self.field_validators,
        )


class CompositeField(BaseField, Generic[DataType]):
    """Base class class for all Fields that collect multiple values."""

    def process(self, inputs: List[QWidget]) -> List[DataType]:
        """Return data for the field.

        Args:
          inputs: the gui widget instances
        """
        return [self.widget_class.process(input_) for input_ in inputs]


class SingleField(BaseField, Generic[DataType]):
    """Base class for all Fields that collection single values."""

    def __init__(
        self,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        validators: Iterable[Callable] = [],
        widget_class: Optional[Widget] = None,
    ):
        """Initialise a new SingleField instance."""
        super().__init__(
            length=1,
            display_name=display_name,
            description=description,
            validators=validators,
            widget_class=widget_class,
            field_validators=[],
        )

    def marshmallow(self) -> marshmallow_fields.Field:
        """Generates a corresponding Marshmallow Field for use in a Schema."""
        return self._marshmallow_field(validate=self.validators)

    def process(self, inputs: List[QWidget]) -> DataType:
        """Return data for the field.

        Args:
          inputs: the gui widget instances
        """
        return [self.widget_class.process(input_) for input_ in inputs][0]


class StrField(SingleField[str]):
    """A field for string data."""

    _marshmallow_field = marshmallow_fields.Str
    _default_widget_class = LineEditWidget()


class IntField(SingleField[int]):
    """A field for integer data."""

    _marshmallow_field = marshmallow_fields.Int
    _default_widget_class = SpinBoxWidget()


class FloatField(SingleField[float]):
    """A field for float data."""

    _marshmallow_field = marshmallow_fields.Float
    _default_widget_class = DoubleSpinBoxWidget()


class VectorField(CompositeField[Iterable[float]]):
    """A field for multiple float values treated as a vector."""

    _marshmallow_field = marshmallow_fields.Float
    _default_widget_class = DoubleSpinBoxWidget()

    def __init__(
        self,
        length: int = 3,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        validators: Iterable[Callable] = [],
        widget_class: Optional[Widget] = None,
        vector_validators: List[Callable] = [],
    ):
        """Initialise a new VectorField instance."""
        super().__init__(
            length,
            display_name,
            description,
            validators,
            widget_class,
            field_validators=[validate.Length(equal=length)] + vector_validators,
        )
