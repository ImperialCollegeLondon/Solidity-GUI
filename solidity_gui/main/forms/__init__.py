"""Module for acquiring data from user via forms.

This module aims to provide:

- a simple, declarative approach to specifying structured data to gather from the user.
- powerful and flexible validation of data with reporting of human-readable errors.
- integration with the GUI framework to support rendering of appropriate input and
  informational components for data collection.

Using this module, creating a dialog box to gather data from the user is as simple as:

```
class MyForm(Form):
    name = StrField(description="Your full name")
    age = IntField(display_name="Total Age", validators=[Range(min=0)])

dialog = SimpleFormDialog(form_class=MyForm)
```

This carries out the following:

- Creates a QDialog displaying a form with two fields and 'OK' and 'Cancel' buttons.
- Renders each field with a header, optional description text and error message.
- Applies different styling to the headers, descriptions and error messages.
- Provides a QLineEdit for the name data and QSpinBox for the age data.
- Limits the values that can be entered into the QSpinBox widget according to the
  provided Range validator.
- Validates provided data when OK is clicked and displays human readable error messages
  back to the user in the case of validation failure.

For further information, please see:

- The [forms](./forms) submodule for details on creating Form objects.
- The [fields](./fields) submodule for details of the available Field types.
- The [dialog](./dialog) submodule for Form rendering and display.
- The [widgets](./widgets) submodule for details of the GUI widgets used in Forms.
"""

from . import fields  # noqa: F401
from . import widgets  # noqa: F401
from .dialog import SimpleFormDialog  # noqa: F401
from .forms import Form, NestedForm  # noqa: F401
