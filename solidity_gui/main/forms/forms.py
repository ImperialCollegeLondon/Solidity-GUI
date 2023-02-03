"""Submodule defining the Form class used for data collection and validation.

Form classes aim to provide a simple, declarative approach to defining GUI components
that gather structured data from the user.
"""

from itertools import chain
from typing import Any, Callable, Dict, List, Tuple, cast

from marshmallow import Schema
from marshmallow import fields as marshmallow_fields
from marshmallow import validates_schema

from .fields import BaseField, Field
from .info import FormInfo


class FormMeta(type):
    """Metaclass for Form classes that proccesses Field attributes.

    When constructing a new Form class, this metaclass looks for attributes that are
    Field subclasses and 1) adds a new dictionary `field` attribute containing
    name->attribute mappings and 2) uses the marshmallow method of each field to
    construct a Marshmallow Schema class for data validation.
    """

    def __new__(cls, name: str, bases: Tuple[type], attrs: Dict[str, Any]) -> type:
        """Constructor for new classes.

        Args:
          name: the class name
          bases: the base classes
          attrs: class attributes
        """
        marshmallow_attrs: Dict[str, marshmallow_fields.Field | Callable] = {}
        attrs["fields"] = {}

        for name, attr in chain(attrs.items()):
            if isinstance(attr, BaseField):
                marshmallow_attrs[name] = attr.marshmallow()
                attrs["fields"][name] = attr

        for base in bases:
            for name in dir(base):
                if name in marshmallow_attrs:
                    # don't overwrite an existing attribute with the base class
                    continue
                attr = getattr(base, name)
                if isinstance(attr, BaseField):
                    marshmallow_attrs[name] = attr.marshmallow()
                    attrs["fields"][name] = attr

        schema_validator = attrs.get("validate", None)
        if not schema_validator:
            for base in bases:
                if schema_validator := getattr(base, "validate", None):
                    break

        if schema_validator:
            marshmallow_attrs["schema_validator"] = validates_schema(schema_validator)
        # could have used Schema.from_dict rather than the below but expected function
        # signature is not compatible with the return type of validates_schema
        attrs["_marshmallow_class"] = type(
            f"{name}Schema", (Schema,), marshmallow_attrs
        )

        return super().__new__(cls, name, bases, attrs)


class Form(metaclass=FormMeta):
    """A Form object for collection and validation of data.

    Form sub-classes may optionally have a `validate` method. If present, this is used
    as a schema level validator for the Marshmallow Schema of the form.
    """

    fields: Dict[str, Field]
    _marshmallow_class: type

    def form_info(
        self,
        data: Dict[str, Any] = {},
        errors: Dict[str, List[str] | Dict[int, List[str]]] = {},
    ) -> FormInfo:
        """Return a FormInfo object for this Form."""
        fields = {
            name: field.field_info(
                name, data.get(name, None), errors=errors.get(name, field.error_default)
            )
            for name, field in self.fields.items()
        }
        # cast used to convey that schema level errors are always a list of strings
        return FormInfo(
            fields=fields,
            schema_errors=cast(List[str], errors.get("_schema", [])),
        )

    def process(self, form_info: FormInfo) -> Dict[str, Any]:
        """Extract form data from the provided FormInfo object.

        Args:
          form_info: FormInfo object containing form data
        """
        return self._marshmallow_class().load(
            {
                name: field.process(form_info.fields[name].input)
                for name, field in (self.fields.items())
            }
        )
