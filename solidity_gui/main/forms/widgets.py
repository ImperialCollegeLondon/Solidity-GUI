"""Submodule for form widgets.

Widget classes primarily provide a uniform interface over an underlying QWidget
class. This abstraction allows Field classes to be interoperable with different widgets
providing considerable flexibility in form appearance and behaviour.

Widget classes are also able to provide interoperatibility with Fields by inferring
appropriate modifications to a QWidget based on Field validators. For instance, a Range
validator used to specify acceptable numerical values can be used to set appropriate
minimum and maximum values for a QSpinBox.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from typing import Generic, TypeVar

from marshmallow import validate
from PySide6.QtWidgets import QCheckBox, QComboBox, QDoubleSpinBox, QLineEdit, QSpinBox
from typing_extensions import Protocol

DataType = TypeVar("DataType")


class _SpinBoxProtocol(Protocol, Generic[DataType]):
    """Generic Protocol for type checking of QAbstractSpinBox subclasses.

    This protocol is needed to provide a generic type for different QAbstractSpinBox
    subclasses. This allows a base class containing the common logic for all spin boxes
    with the types concretised for different spin box subclasses.
    """

    def value(self) -> DataType:  # noqa: D102
        pass

    def setMinimum(self, min: DataType) -> None:  # noqa: D102
        pass

    def setMaximum(self, max: DataType) -> None:  # noqa: D102
        pass

    def setValue(self, val: DataType) -> None:  # noqa: D102
        pass


WidgetType = TypeVar("WidgetType")


class Widget(ABC, Generic[WidgetType, DataType]):
    """Abstract base class for Widgets."""

    qt_input_class: type[WidgetType]
    """QWidget class."""

    @staticmethod
    @abstractmethod
    def process(input_: WidgetType) -> DataType:
        """Extract form data from an instance of WidgetType."""
        pass

    @abstractmethod
    def create(
        self, data: DataType | None, validators: Iterable[Callable]
    ) -> WidgetType:
        """Return a WidgetType instance."""
        pass


SpinBoxType = TypeVar("SpinBoxType", bound=_SpinBoxProtocol)


class SpinBoxBase(Widget, Generic[SpinBoxType, DataType]):
    """Base class encapsulating common logic for QAbstractSpinBox subclass Widgets."""

    _default_min = -1000000000
    _default_max = 1000000000

    def create(
        self, data: DataType | None, validators: Iterable[Callable]
    ) -> SpinBoxType:
        """Return a SpinBoxType instance.

        Args:
          data: value to populate into the SpinBox
          validators: marshmallow validators (passed by associated Field)
        """
        for validator in validators:
            if isinstance(validator, validate.Range):
                min_ = validator.min if validator.min is not None else self._default_min
                max_ = validator.max if validator.max is not None else self._default_max
                break
        else:
            min_ = self._default_min
            max_ = self._default_max

        qt_input = self.qt_input_class()
        qt_input.setMinimum(min_)
        qt_input.setMaximum(max_)
        if data is not None:
            qt_input.setValue(data)
        return qt_input

    @staticmethod
    def process(input_: SpinBoxType) -> DataType:
        """Extract form data from an instance of SpinBoxType.

        Args:
          input_: SpinBoxType instance containing data
        """
        return input_.value()


class SpinBoxWidget(SpinBoxBase[QSpinBox, int]):
    """Widget for collecting integers via a QSpinBox."""

    qt_input_class = QSpinBox


class DoubleSpinBoxWidget(SpinBoxBase[QDoubleSpinBox, float]):
    """Widget for collecting floats via a QDoubleSpinBox."""

    qt_input_class = QDoubleSpinBox
    _default_min = -1000000000
    _default_max = 1000000000

    def __init__(self, decimals: int = 3):
        """Initialise a new instance.

        Args:
          decimals: The number of decimal places to display.
        """
        self.decimals = decimals

    def create(
        self, data: float | None, validators: Iterable[Callable]
    ) -> QDoubleSpinBox:
        """Return a QDoubleSpinBox instance.

        Args:
          data: value to populate into the DoubleSpinBox
          validators: marshmallow validators (passed by associated Field)
        """
        qt_input = super().create(data, validators)
        qt_input.setDecimals(self.decimals)

        # irritatingly we have to set the data again because it may have been rounded
        # off before the number of decimals was set correctly
        if data is not None:
            qt_input.setValue(data)
        return qt_input


class LineEditWidget(Widget[QLineEdit, str]):
    """Widget for collecting strings via a QLineEdit."""

    qt_input_class = QLineEdit

    def create(self, data: str | None, validators: Iterable[Callable]) -> QLineEdit:
        """Return a QLineEdit instance.

        Args:
          data: value to populate into the QLineEdit
          validators: marshmallow validators (passed by associated Field)
        """
        qt_input = self.qt_input_class()
        if data is not None:
            qt_input.setText(data)
        return qt_input

    @staticmethod
    def process(input_: QLineEdit) -> str:
        """Extract form data from an instance of QLineEdit.

        Args:
          input_: QLineEdit instance containing data
        """
        return input_.text()


class CheckBoxWidget(Widget[QCheckBox, bool]):
    """Widget for collecting bools via a QCheckBox."""

    qt_input_class = QCheckBox

    def create(self, data: bool | None, validators: Iterable[Callable]) -> QCheckBox:
        """Return a QCheckBox instance.

        Args:
          data: value to populate into the QCheckBox
          validators: marshmallow validators (passed by associated Field)
        """
        qt_input = self.qt_input_class()
        if data is not None:
            qt_input.setChecked(data)
        return qt_input

    @staticmethod
    def process(input_: QCheckBox) -> bool:
        """Extract form data from an instance of QCheckBox.

        Args:
          input_: QCheckBox instance containing data
        """
        return input_.isChecked()


class TrueWidget(CheckBoxWidget):
    """Widget that always provides a value of True."""

    def create(self, data: bool | None, validators: Iterable[Callable]) -> QCheckBox:
        """Return a QCheckBox instance that is not visible.

        Args:
          data: present for API consistency but ignored.
          validators: marshmallow validators (passed by associated Field)
        """
        qt_input = super().create(True, validators)
        qt_input.setVisible(False)
        return qt_input

    @staticmethod
    def process(input_: QCheckBox) -> bool:
        """Returns True.

        Args:
          input_: present for API consistency but ignored.
        """
        return True


class ComboBoxBase(Widget[QComboBox, str]):
    """Widget for collecting strings via a QComboBox."""

    def __init__(self, items: list[str]):
        """Initialise a new instance.

        Args:
          items: The items to populate the QComboBox with.
        """
        self.items = items

    def create(self, data: str | None, validators: Iterable[Callable]) -> QComboBox:
        """Return a QComboBox instance.

        Args:
          data: value to populate into the QComboBox
          validators: marshmallow validators (passed by associated Field)
        """
        qt_input = QComboBox()
        qt_input.addItems(self.items)
        if data is not None:
            qt_input.setCurrentText(data)
        return qt_input

    @staticmethod
    def process(input_: QComboBox) -> str:
        """Extract form data from an instance of QComboBox.

        Args:
          input_: QComboBox instance containing data
        """
        return input_.currentText()
