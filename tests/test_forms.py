"""Tests for forms module."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from marshmallow import Schema, ValidationError, fields, validate
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QSpinBox,
)

from solidity_gui.main.forms.dialog import SimpleFormDialog, default_form_renderer
from solidity_gui.main.forms.fields import (
    BoolField,
    FloatField,
    IntField,
    StrField,
    VectorField,
)
from solidity_gui.main.forms.forms import Form
from solidity_gui.main.forms.info import FieldInfo, FormInfo
from solidity_gui.main.forms.widgets import (
    CheckBoxWidget,
    DoubleSpinBoxWidget,
    LineEditWidget,
    SpinBoxWidget,
)


@pytest.mark.parametrize(
    "field_class,data,qwidget_class",
    (
        (StrField, "aa", QLineEdit),
        (IntField, 1, QSpinBox),
        (FloatField, 1.0, QDoubleSpinBox),
    ),
)
def test_field_subclass(qtbot, field_class, data, qwidget_class):
    """Basic tests for the subclasses of fields.Field."""
    display_name = "foo"
    description = "bar"
    validators = [validate.Equal(data)]
    field = field_class(
        display_name=display_name, description=description, validators=validators
    )

    marshmallow_field = field.marshmallow()
    assert isinstance(marshmallow_field, field_class._marshmallow_field)
    assert marshmallow_field.validators == validators

    input_ = field.input(data)
    assert field.process([input_]) == data

    errors = ["error text"]
    field_info = field.field_info("field", data, errors=errors)
    assert isinstance(field_info.input[0], qwidget_class)
    field_info.header = display_name
    field_info.description = description
    field_info.errors = errors


def test_vector_field():
    """Basic test of VectorField class."""
    validators = [validate.Equal(5)]
    field = VectorField(validators=validators)

    marshmallow_field = field.marshmallow()
    assert isinstance(marshmallow_field, fields.List)
    assert marshmallow_field.validators == field.field_validators

    assert isinstance(marshmallow_field.inner, fields.Float)
    assert marshmallow_field.inner.validators == validators

    data = [1, 2, 3]
    inputs = [field.input(d) for d in data]
    assert field.process(inputs) == data


def test_vector_field_field_info(qtbot):
    """Test field_info method of VectorField class."""
    field = VectorField()
    field_info = field.field_info(name="name", data=None)
    assert all(isinstance(input_, QDoubleSpinBox) for input_ in field_info.input)


def test_vector_field_field_info_data(qtbot):
    """Test field_info method of VectorField class with valid data."""
    data = [1, 2, 3]
    field = VectorField()
    field_info = field.field_info(name="name", data=data)
    assert [input_.value() for input_ in field_info.input] == data


@pytest.mark.parametrize("data", ([1, 2], [1, 2, 3, 4]))
def test_vector_field_field_info_data_wrong_length(qtbot, data):
    """Test field_info method of VectorField class whit invalid data."""
    field = VectorField()
    with pytest.raises(ValueError):
        field.field_info(name="name", data=data)


def test_float_field(qtbot):
    """Basic test of FloatField class."""
    validators = [validate.Equal(5)]
    field = FloatField(validators=validators)

    marshmallow_field = field.marshmallow()
    assert isinstance(marshmallow_field, fields.Float)
    assert marshmallow_field.validators == field.validators

    data = 1.1
    qt_input = field.input(data)
    assert field.process([qt_input]) == data


def test_int_field(qtbot):
    """Basic test of FloatField class."""
    validators = [validate.Equal(5)]
    field = IntField(validators=validators)

    marshmallow_field = field.marshmallow()
    assert isinstance(marshmallow_field, fields.Int)
    assert marshmallow_field.validators == field.validators

    data = 1
    qt_input = field.input(data)
    assert field.process([qt_input]) == data


def test_bool_field(qtbot):
    """Basic test of FloatField class."""
    validators = [validate.Equal(True)]
    field = BoolField(validators=validators)

    marshmallow_field = field.marshmallow()
    assert isinstance(marshmallow_field, fields.Bool)
    assert marshmallow_field.validators == field.validators

    data = True
    qt_input = field.input(data)
    assert field.process([qt_input]) == data


def test_form_subclass():
    """Test FormMeta metaclass behaviour for multiple Form sub-classes."""

    class BaseForm(Form):
        a = FloatField()

    class ExtendForm(BaseForm):
        b = StrField()

    assert isinstance(ExtendForm.a, FloatField)
    assert isinstance(ExtendForm.b, StrField)

    assert ExtendForm.fields == dict(a=ExtendForm.a, b=ExtendForm.b)

    schema = ExtendForm._marshmallow_class()
    assert isinstance(schema, Schema)

    schema.load(dict(a=1, b="a"))
    with pytest.raises(ValidationError):
        schema.load(dict(a="a", b="b"))
    with pytest.raises(ValidationError):
        schema.load(dict(label=1, b=1))


def test_form_subclass_triple():
    """Test FormMeta metaclass behaviour with three Form sub-classes."""

    class BaseForm(Form):
        a = FloatField()

    class ExtendFormInter(BaseForm):
        b = StrField()

    class ExtendForm(ExtendFormInter):
        label = StrField()

    assert ExtendForm.fields == dict(
        a=ExtendForm.a, b=ExtendForm.b, label=ExtendForm.label
    )


def test_form_subclass_overwrite():
    """Test inherited attributes are overwritten correctly for Form sub-clasess."""

    class BaseForm(Form):
        a = FloatField()

    class SubForm(BaseForm):
        a = IntField()

    assert isinstance(SubForm.a, IntField)
    assert SubForm.fields == dict(a=SubForm.a)


class TestForm(Form):
    """Simple Form sub class for use in tests."""

    a = FloatField()
    b = FloatField()

    def validate(self, data, **kwargs):
        """Form validation method."""
        if data["a"] > data["b"]:
            raise ValidationError("bad data")


def test_form_validate():
    """Test form level validation using form schema class."""
    schema = TestForm._marshmallow_class()
    schema.load(dict(a=0, b=1))
    with pytest.raises(ValidationError):
        schema.load(dict(a=1, b=0))


def test_form_validate_sub_class():
    """Test inheritance of `validate` in Form sub-classes."""

    class SubForm(TestForm):
        c = StrField()

    schema = SubForm._marshmallow_class()
    schema.load(dict(a=0, b=1, c="a"))
    with pytest.raises(ValidationError):
        schema.load(dict(a=0, b=1, c=1))
    with pytest.raises(ValidationError):
        schema.load(dict(a=1, b=0, c="a"))


def test_form_validate_sub_class_multiple_inheritance():
    """Test inheritance of `validate` in Form sub-classes with multiple inheritance."""

    class DummyMixin:
        pass

    class SubForm(DummyMixin, TestForm):
        pass

    schema = SubForm._marshmallow_class()
    schema.load(dict(a=0, b=1))
    with pytest.raises(ValidationError):
        schema.load(dict(a=1, b=0))

    class SubForm(TestForm, DummyMixin):
        pass

    schema = SubForm._marshmallow_class()
    schema.load(dict(a=0, b=1))
    with pytest.raises(ValidationError):
        schema.load(dict(a=1, b=0))


def test_form_field_order_preserved(qtbot):
    """Check order of fields in FormInfo is perserved from definition."""

    class SubForm(TestForm):
        c = FloatField()

    form_info = SubForm().form_info()
    assert list(form_info.fields.keys()) == ["a", "b", "c"]


def test_form_field_order_override(qtbot):
    """Check order of fields can be controlled via field_order attribute."""
    order = ["c", "b", "a"]

    class SubForm(TestForm):
        c = FloatField()
        field_order = order

    form_info = SubForm().form_info()
    assert list(form_info.fields.keys()) == order


def test_form_field_order_override_subset(qtbot):
    """Check order of fields when only specifying a subset of field names."""

    class SubForm(TestForm):
        c = FloatField()
        field_order = ["c"]

    form_info = SubForm().form_info()
    assert list(form_info.fields.keys()) == ["c", "a", "b"]


@pytest.mark.parametrize("widget_class", (SpinBoxWidget, DoubleSpinBoxWidget))
def test_spin_box_widget(qtbot, widget_class):
    """Test SpinBoxBase sub-classes."""
    input_ = widget_class().create(None, [])
    assert isinstance(input_, widget_class.qt_input_class)

    assert input_.minimum() == widget_class._default_min
    assert input_.maximum() == widget_class._default_max
    assert input_.value() == 0


@pytest.mark.parametrize("widget_class", (SpinBoxWidget, DoubleSpinBoxWidget))
def test_spin_box_widget_data(qtbot, widget_class):
    """Test SpinBoxBase sub-classes input method with data."""
    data = 5
    input_ = widget_class().create(data, [])
    assert input_.value() == data


@pytest.mark.parametrize("widget_class", (SpinBoxWidget, DoubleSpinBoxWidget))
def test_spin_box_widget_range(qtbot, widget_class):
    """Test QWidget attributes when range validator is passed."""
    min_, max_ = -5, 5
    input_ = widget_class().create(
        None,
        [
            validate.OneOf([0]),  # decoy validator that doesn't affect widget
            validate.Range(min=min_, max=max_),
        ],
    )
    assert input_.minimum() == min_
    assert input_.maximum() == max_


@pytest.mark.parametrize("widget_class", (SpinBoxWidget, DoubleSpinBoxWidget))
def test_spin_box_process(qtbot, widget_class):
    """Test process method of SpinBoxBase sub-clasess."""
    data = 4
    input_ = widget_class.qt_input_class()
    input_.setValue(data)
    assert widget_class().process(input_) == data


def test_double_spin_box_decimals(qtbot):
    """Test settings of decimals attribute by DoubleSpinBoxWidget class."""
    decimals = 5
    widget = DoubleSpinBoxWidget(decimals=decimals)
    input_ = widget.create(None, [])
    assert input_.decimals() == decimals


def test_line_edit_widget(qtbot):
    """Test LineEditWidget class."""
    input_ = LineEditWidget().create(None, [])
    assert input_.text() == ""


def test_line_edit_widget_data(qtbot):
    """Test LineEditWidget class sets QLineEdit data."""
    data = "aaa"
    input_ = LineEditWidget().create(data, [])
    assert input_.text() == data


def test_line_edit_widget_process(qtbot):
    """Test process method of LineEditWidget."""
    data = "aaa"
    input_ = LineEditWidget.qt_input_class()
    input_.setText(data)
    assert LineEditWidget().process(input_) == data


def test_check_box_widget(qtbot):
    """Test CheckBoxWidget class."""
    input_ = CheckBoxWidget().create(None, [])
    assert input_.isChecked() == False


def test_check_box_widget_data(qtbot):
    """Test CheckBoxWidget class sets QCheckBox data."""
    data = True
    input_ = CheckBoxWidget().create(data, [])
    assert input_.isChecked() == data


def test_check_box_widget_process(qtbot):
    """Test process method of CheckBoxWidget."""
    data = True
    input_ = CheckBoxWidget.qt_input_class()
    input_.setChecked(data)
    assert CheckBoxWidget().process(input_) == data


def _check_label(layout, pos, text):
    label = layout.itemAt(pos).widget()
    assert isinstance(label, QLabel)
    assert label.text() == text
    return pos + 1


@pytest.mark.parametrize(
    "kwargs",
    (
        dict(header="header"),
        dict(description="description"),
        dict(header="header", description="description"),
        dict(errors={0: ["error text 1"]}),
        dict(errors={0: ["error text 1", "error text 2"]}),
        dict(
            header="header",
            description="description",
            errors={0: ["error text 1", "error text 2"]},
        ),
    ),
)
def test_default_form_renderer_field(qtbot, kwargs):
    """Check default_form_renderer function when passed a single field."""
    form_info = FormInfo(fields=dict(a=FieldInfo(input=[QSpinBox()], **kwargs)))
    layout = default_form_renderer(form_info)
    pos = 0
    if header := kwargs.get("header"):
        pos = _check_label(layout, pos, f"{header.capitalize()}:")
    if description := kwargs.get("description"):
        pos = _check_label(layout, pos, description)
    if errors := kwargs.get("errors"):
        for error in errors[0]:
            pos = _check_label(layout, pos, error)
    input_ = layout.itemAt(pos).widget()
    assert isinstance(input_, QSpinBox)


@pytest.mark.parametrize(
    "kwargs",
    (
        dict(header="header"),
        dict(description="description"),
        dict(header="header", description="description"),
        dict(errors={0: ["error text 1"]}),
        dict(errors={1: ["error text 1"]}),
        dict(errors={0: ["error text 1"], 1: ["error text 2"]}),
        dict(
            header="header",
            description="description",
            errors={0: ["error text 1"], 1: ["error text 2"]},
        ),
    ),
)
def test_default_form_renderer_multiple_inputs(qtbot, kwargs):
    """Check default_form_renderer function when passed a single composite field."""
    if "errors" not in kwargs:
        kwargs["errors"] = {}

    field = FieldInfo(input=[QSpinBox(), QSpinBox()], **kwargs)
    form_info = FormInfo(fields=dict(a=field))
    layout = default_form_renderer(form_info)
    pos = 0
    if header := kwargs.get("header"):
        pos = _check_label(layout, pos, f"{header.capitalize()}:")
    if description := kwargs.get("description"):
        pos = _check_label(layout, pos, description)
    for i in range(len(field.input)):
        if errors := kwargs.get("errors", {}).get(i, None):
            for error in errors:
                pos = _check_label(layout, pos, error)
        input_ = layout.itemAt(pos).widget()
        assert isinstance(input_, QSpinBox)
        pos += 1


def test_default_form_renderer_schema_error(qtbot):
    """Check rendering of schema level errors by default_form_renderer."""
    form_info = FormInfo(
        fields=dict(a=FieldInfo(input=[QSpinBox()])), schema_errors=["error1", "error2"]
    )
    layout = default_form_renderer(form_info)
    _check_label(layout, 1, form_info.schema_errors[0])
    _check_label(layout, 2, form_info.schema_errors[1])


@pytest.fixture
def handler_mocks(monkeypatch):
    """Fixture that mocks the signal handlers of the SimpleFormDialog class."""
    ok_mock = MagicMock()
    monkeypatch.setattr(SimpleFormDialog, "_ok_clicked", ok_mock)
    cancel_mock = MagicMock()
    monkeypatch.setattr(SimpleFormDialog, "_cancel_clicked", cancel_mock)
    return SimpleNamespace(ok=ok_mock, cancel=cancel_mock)


def test_simple_form_dialog(qtbot, handler_mocks):
    """Test SimpleFormDialog class."""
    dialog = SimpleFormDialog(TestForm)
    form_info = FormInfo(fields=dict(a=FieldInfo(input=[QSpinBox()])))

    dialog_layout = dialog._create_contents(form_info)
    form_layout = default_form_renderer(form_info)
    assert dialog_layout.count() == form_layout.count() + 1

    button_box = dialog_layout.itemAt(dialog_layout.count() - 1).widget()
    assert isinstance(button_box, QDialogButtonBox)

    # simplest way to check that signal handlers seems to be to replace handlers with a
    # mock then trigger the signal and check the calls
    handler_mocks.ok.assert_not_called()
    button_box.accepted.emit()
    handler_mocks.ok.assert_called()

    handler_mocks.cancel.assert_not_called()
    button_box.rejected.emit()
    handler_mocks.ok.assert_called()


def test_simple_form_dialog_ok_clicked(qtbot):
    """Test SimpleFormDialog._ok_clicked."""
    dialog = SimpleFormDialog(TestForm)
    layout = dialog.layout()

    data = dict(a=5, b=6)
    for name, value in data.items():
        dialog.form_info.fields[name].input[0].setValue(value)

    processed_data = dialog._ok_clicked()
    assert data == processed_data
    assert dialog.layout() is layout  # layout was not updated


def test_simple_form_dialog_ok_clicked_bad_data(qtbot):
    """Test SimpleFormDialog._ok_clicked with invalid data."""
    dialog = SimpleFormDialog(TestForm)
    layout = dialog.layout()
    assert not dialog.form_info.schema_errors

    data = dict(a=6, b=5)  # violates schema level validation
    for name, value in data.items():
        dialog.form_info.fields[name].input[0].setValue(value)

    assert dialog._ok_clicked() is None
    assert dialog.form_info.schema_errors
    assert dialog.layout() is not layout  # layout was updated
