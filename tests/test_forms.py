"""Tests for forms module."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from marshmallow import Schema
from marshmallow import ValidationError as MarshmallowValidationError
from marshmallow import fields, validate
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QDoubleSpinBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from solidity_gui.main.forms.dialog import (
    SimpleFormDialog,
    default_field_renderer,
    default_form_renderer,
    single_choice_field_renderer,
    single_choice_form_renderer,
)
from solidity_gui.main.forms.fields import (
    BoolField,
    FloatField,
    IntField,
    StrField,
    VectorField,
)
from solidity_gui.main.forms.forms import Form, NestedForm, SingleChoiceNestedForm
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
    with pytest.raises(MarshmallowValidationError):
        schema.load(dict(a="a", b="b"))
    with pytest.raises(MarshmallowValidationError):
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
            raise MarshmallowValidationError("bad data")


def test_form_validate():
    """Test form level validation using form schema class."""
    schema = TestForm._marshmallow_class()
    schema.load(dict(a=0, b=1))
    with pytest.raises(MarshmallowValidationError):
        schema.load(dict(a=1, b=0))


def test_form_validate_sub_class():
    """Test inheritance of `validate` in Form sub-classes."""

    class SubForm(TestForm):
        c = StrField()

    schema = SubForm._marshmallow_class()
    schema.load(dict(a=0, b=1, c="a"))
    with pytest.raises(MarshmallowValidationError):
        schema.load(dict(a=0, b=1, c=1))
    with pytest.raises(MarshmallowValidationError):
        schema.load(dict(a=1, b=0, c="a"))


def test_form_validate_sub_class_multiple_inheritance():
    """Test inheritance of `validate` in Form sub-classes with multiple inheritance."""

    class DummyMixin:
        pass

    class SubForm(DummyMixin, TestForm):
        pass

    schema = SubForm._marshmallow_class()
    schema.load(dict(a=0, b=1))
    with pytest.raises(MarshmallowValidationError):
        schema.load(dict(a=1, b=0))

    class SubForm(TestForm, DummyMixin):
        pass

    schema = SubForm._marshmallow_class()
    schema.load(dict(a=0, b=1))
    with pytest.raises(MarshmallowValidationError):
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
    assert not input_.isChecked()


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


def _check_field(layout, field_info, qwidget_class, check_header=True):
    pos = 0
    if field_info.header and check_header:
        pos = _check_label(layout, pos, f"{field_info.header.capitalize()}:")
    if field_info.description:
        pos = _check_label(layout, pos, field_info.description)
    if field_info.errors:
        for error in field_info.errors[0]:
            pos = _check_label(layout, pos, error)
    input_ = layout.itemAt(pos).widget()
    assert isinstance(input_, qwidget_class)


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
def test_default_field_renderer(qtbot, kwargs):
    """Check default_form_renderer function when passed a single field."""
    qwidget_class = QSpinBox
    field_info = FieldInfo(input=[qwidget_class()], **kwargs)
    layout = default_field_renderer(field_info, 0)
    _check_field(layout, field_info, qwidget_class)


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
def test_default_field_renderer_multiple_inputs(qtbot, kwargs):
    """Check default_form_renderer function when passed a single composite field."""
    if "errors" not in kwargs:
        kwargs["errors"] = {}

    field_info = FieldInfo(input=[QSpinBox(), QSpinBox()], **kwargs)
    layout = default_field_renderer(field_info, level=0)
    pos = 0
    if header := kwargs.get("header"):
        pos = _check_label(layout, pos, f"{header.capitalize()}:")
    if description := kwargs.get("description"):
        pos = _check_label(layout, pos, description)
    for i in range(len(field_info.input)):
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


def test_nested_form(qtbot):
    """Test nesting of form classes."""

    class TestNestedForm(Form):
        b = StrField()
        c = FloatField()

    class TestForm(Form):
        a = NestedForm(TestNestedForm)
        d = IntField()

    TestForm._marshmallow_class().load(dict(a=dict(b="22", c=3), d=4))

    form_info = TestForm().form_info()
    assert (
        form_info.fields["a"].fields.keys()
        == TestNestedForm().form_info().fields.keys()
    )

    form_info.fields["a"].fields["b"].input[0].setText("aoeu")
    form_info.fields["a"].fields["c"].input[0].setValue(3.5)
    form_info.fields["d"].input[0].setValue(8)

    data = TestForm().process(form_info)
    assert data == dict(a=dict(b="aoeu", c=3.5), d=8)


def test_nested_form_errors(qtbot):
    """Test generation of field errors for nested forms."""

    class TestNestedForm(Form):
        b = IntField(validators=[validate.Range(min=0)])

    class TestForm(Form):
        a = NestedForm(TestNestedForm)

    data = dict(a=dict(b=-5))
    try:
        TestForm()._marshmallow_class().load(data)
    except MarshmallowValidationError as e:
        assert e.messages == dict(a=dict(b=["Must be greater than or equal to 0."]))


def test_nested_form_schema_errors(qtbot):
    """Test generation of schema errors for nested forms."""

    class TestNestedForm(Form):
        b = IntField()

        def validate(self, data, **kwargs):
            if data["b"] == -5:
                raise MarshmallowValidationError("bad data")

    class TestForm(Form):
        a = NestedForm(TestNestedForm)

    data = dict(a=dict(b=-5))

    try:
        TestForm()._marshmallow_class().load(data)
    except MarshmallowValidationError as e:
        assert e.messages == dict(a=dict(_schema=["bad data"]))


@pytest.mark.parametrize(
    "kwargs",
    (
        dict(header="header"),
        dict(description="description"),
        dict(header="header", description="description"),
        dict(errors={0: ["error text 1"]}),
        dict(
            header="header",
            description="description",
            errors={0: ["error text 1"]},
        ),
    ),
)
def test_default_form_renderer_nested_form(qtbot, kwargs):
    """Check default_form_renderer function when passed a single field."""
    form_info = FormInfo(
        fields=dict(
            a=FormInfo(
                fields=dict(b=FieldInfo(input=[QSpinBox()], **kwargs)),
            ),
            c=FieldInfo(input=[QDoubleSpinBox()], header="outer header"),
        ),
    )
    layout = default_form_renderer(form_info)
    nested_layout = layout.itemAt(0).layout()
    assert isinstance(nested_layout, QVBoxLayout)

    field_layout = nested_layout.itemAt(0).layout()
    assert isinstance(field_layout, QVBoxLayout)
    pos = 0
    if header := kwargs.get("header"):
        pos = _check_label(field_layout, pos, f"{header.capitalize()}:")
    if description := kwargs.get("description"):
        pos = _check_label(field_layout, pos, description)
    if errors := kwargs.get("errors"):
        for error in errors[0]:
            pos = _check_label(field_layout, pos, error)

    assert isinstance(field_layout.itemAt(pos).widget(), QSpinBox)

    field2_layout = layout.itemAt(1).layout()
    _check_label(field2_layout, 0, "Outer header:")
    assert isinstance(field2_layout.itemAt(1).widget(), QDoubleSpinBox)


def test_nested_form_info(qtbot):
    """Test the form_info method of Form classes with nested forms."""

    class TestNestedForm(Form):
        a = FloatField()
        b = IntField()

    class TestForm(Form):
        c = NestedForm(TestNestedForm)
        d = FloatField()

    data = dict(c=dict(a=0.5, b=2), d=3.5)
    errors = dict(c=dict(_schema=["schema2"], a={0: "fielda"}), d={0: "fieldd"})
    form_info = TestForm().form_info(
        data=data, errors=errors, schema_errors=["schema1"]
    )
    nested_form_info = form_info.fields["c"]
    assert nested_form_info.schema_errors == errors["c"]["_schema"]
    assert nested_form_info.fields["a"].errors == errors["c"]["a"]
    assert nested_form_info.fields["b"].errors == {}
    assert form_info.fields["d"].errors == errors["d"]

    assert form_info.fields["d"].input[0].value() == data["d"]
    assert nested_form_info.fields["a"].input[0].value() == data["c"]["a"]
    assert nested_form_info.fields["b"].input[0].value() == data["c"]["b"]


def test_single_choice_process(qtbot):
    """Check data is not retrieved for disabled fields."""

    class TestNestedForm(Form):
        a = FloatField()
        b = IntField()

    class TestForm(Form):
        c = SingleChoiceNestedForm(TestNestedForm)
        d = FloatField()

    data = dict(c=dict(a=0.5, b=2), d=3.5)
    form_info = TestForm().form_info(data=data)

    # renderer is usually responsible for disabling fields
    form_info.fields["c"].fields["a"].disabled = True

    data["c"].pop("a")
    assert TestForm().process(form_info) == data


def test_single_choice_render_nested_form_not_supported(qtbot):
    """Check that nesting forms inside a SingleChoiceNestedForm is not supported."""

    class TestNestedNestedForm(Form):
        pass

    class TestNestedForm(Form):
        b = NestedForm(TestNestedNestedForm)

    class TestForm(Form):
        a = SingleChoiceNestedForm(TestNestedForm)

    with pytest.raises(ValueError, match="not supported"):
        default_form_renderer(TestForm().form_info())


@pytest.mark.parametrize("checked", (True, False))
def test_single_choice_field_renderer(qtbot, checked):
    """Check rendering of SingleChoiceNestedForm."""
    qwidget_class = QSpinBox
    field_info = FieldInfo(input=[qwidget_class()], header="header text", errors=dict())

    level = 1
    layout = single_choice_field_renderer(
        field_info=field_info, level=level, checked=checked
    )
    radio_button = layout.itemAt(0).widget()
    assert isinstance(radio_button, QRadioButton)
    assert radio_button.text() == field_info.header

    # check toggled signal handler
    assert field_info.disabled == (not checked)
    radio_button.toggled.emit(not checked)
    assert field_info.disabled == checked

    field_layout = layout.itemAt(1).layout()
    _check_field(field_layout, field_info, qwidget_class, check_header=False)


@patch("solidity_gui.main.forms.dialog.single_choice_field_renderer")
@pytest.mark.parametrize("schema_errors", ([], ["error text"]))
def test_single_choice_form_renderer(
    field_renderer_mock: MagicMock, qtbot, schema_errors
):
    """Test layout created by single_choice_form_renderer method."""
    field_renderer_mock.side_effect = lambda *args, **kwargs: QVBoxLayout()
    a = FieldInfo(input=[QSpinBox()])
    b = FieldInfo(input=[QLineEdit()])
    form_info = FormInfo(
        fields=dict(a=a, b=b), schema_errors=schema_errors, single_choice=True
    )

    layout = single_choice_form_renderer(form_info, level=0)

    field_renderer_mock.assert_any_call(a, 0, checked=True)
    field_renderer_mock.assert_called_with(b, 0, checked=False)

    group_box = layout.itemAt(0).widget()
    assert isinstance(group_box, QGroupBox)
    box_layout = group_box.layout()
    assert isinstance(box_layout, QVBoxLayout)

    assert box_layout.count() == 2

    if schema_errors:
        error_label = layout.itemAt(1).widget()
        assert isinstance(error_label, QLabel)
        assert error_label.text() == schema_errors[0]
