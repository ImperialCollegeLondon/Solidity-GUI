"""Support for rendering Form objects as individual dialog boxes."""

from typing import Any, Callable, Dict, Optional, Type

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLayout,
    QVBoxLayout,
    QWidget,
)

from .forms import Form, ValidationError
from .info import FormInfo


def _create_named_label(text: str, object_name: str) -> QLabel:
    """Helper function for creating QLabels with ObjectName set."""
    label = QLabel(text)
    label.setObjectName(object_name)
    return label


def default_form_renderer(form_info: FormInfo) -> QLayout:
    """Render a FormInfo instance into a QVBoxLayout.

    This function aims to provide a sensible default layout agnostic to use
    context. Field errors, headers and descriptions are displayed as QLabel objects with
    appropriate ObjectName values to allow simple and consistent styling. Errors are
    displayed immediately after the most relevant context (e.g. input widget for field
    level errors, end of form for schema level errors).

    Args:
      form_info: description of the form to render
    """
    layout = QVBoxLayout()

    for field_info in form_info.fields.values():
        if field_info.header:
            layout.addWidget(
                _create_named_label(f"{field_info.header.capitalize()}:", "header")
            )
        if field_info.description:
            layout.addWidget(_create_named_label(field_info.description, "description"))
        for i, input_ in enumerate(field_info.input):
            if isinstance(field_info.errors, dict):
                if errors := field_info.errors.get(i, None):
                    for error in errors:
                        layout.addWidget(_create_named_label(error, "error"))
            layout.addWidget(input_)
        if isinstance(field_info.errors, list):
            for error in field_info.errors:
                layout.addWidget(_create_named_label(error, "error"))

    for error in form_info.schema_errors:
        layout.addWidget(_create_named_label(error, "error"))
    return layout


class SimpleFormDialog(QDialog):
    """A dedicated QDialog subclass for presenting a form to the user.

    This dialog displays the form according to the provided render function, adds an
    OK/Cancel button pair and wires up basic signal handlers. In the event of the
    submitted form failing validation, the dialog contents are re-rendered with error
    messages.

    This class is designed to be extensible and indeed must be extended to in order to
    do anything useful. The `_ok_clicked` handler provides sensible default behaviour in
    the case of invalid data being provided but does not do anything in the case of
    valid data.

    The simplest intended use case for this form is therefore as below:

    ```
    class FunctionalDialog(SimpleFormDialog):
        def _ok_clicked(self):
            if data := super()._ok_clicked():
                # do something useful with data
    ```

    This preserves the data validation behaviour and tacks on additional actions to
    perform with data that passes validation. Alternatively, you can overwrite
    `_ok_clicked` without calling the superclass implementation. This gives more
    flexibility but you will probably need to implement data validation and form update
    behaviours.
    """

    def __init__(
        self,
        form_class: Type[Form],
        form_renderer: Callable[[FormInfo], QLayout] = default_form_renderer,
        **kwargs: Any,
    ):
        """Initialise a new SimpleFormDialog.

        Args:
          form_class: form to display
          form_renderer: renderer that creates GUI elements from a FormInfo instance
        """
        super().__init__(**kwargs)
        self.form_class = form_class
        self.form_info = self.form_class().form_info()
        self.form_renderer = form_renderer
        contents = self._create_contents(self.form_info)
        self.setLayout(contents)
        # style different label types in form
        self.setStyleSheet(
            "QLabel#error { color: red } "
            "QLabel#description { color: gray } "
            "QLabel#header { font-weight: bold }"
        )

    def _create_contents(self, form_info: FormInfo) -> QLayout:
        """Create the contents of the dialog from a FormInfo instance."""
        contents = self.form_renderer(form_info)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        contents.addWidget(button_box)
        # mypy doesn't think accepted and rejected below are defined for some reason
        # some __getattr__ shenanigans from pyside?
        button_box.accepted.connect(self._ok_clicked)  # type: ignore[attr-defined]
        button_box.rejected.connect(self._cancel_clicked)  # type: ignore[attr-defined]
        return contents

    def _cancel_clicked(self) -> None:
        """Signal handler for clicking cancel button."""
        self.close()

    def _ok_clicked(self) -> Optional[Dict[str, Any]]:
        """Signal handler for clicking ok button.

        In case of form data passing validation, returns the data. In case of validation
        failure, updates dialog contents and returns None.
        """
        try:
            return self.form_class().process(self.form_info)
        except ValidationError as e:
            self.form_info = self.form_class().form_info(
                data=e.form_data, errors=e.field_errors, schema_errors=e.schema_errors
            )
            # below hackery is required to update the layout of the dialog
            # QT won't let us set a new layout when one already exists so we reparent
            # the current layout to void it.
            QWidget().setLayout(self.layout())
            # then set the content we want
            contents = self._create_contents(self.form_info)
            self.setLayout(contents)
            return None
