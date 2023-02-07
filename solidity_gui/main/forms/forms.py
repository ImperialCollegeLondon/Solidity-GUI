"""Submodule defining the Form class used for data collection and validation.

Form classes aim to provide a simple, declarative approach to defining GUI components
that gather structured data from the user.
"""

from itertools import chain
from typing import Any, Callable, Dict, List, Tuple, cast

from marshmallow import Schema
from marshmallow import ValidationError as MarshmallowValidationError
from marshmallow import fields as marshmallow_fields
from marshmallow import validates_schema

from .fields import BaseField, CompositeField, SingleField
from .info import FormInfo


class ValidationError(Exception):
    """Custom class for by validation failures.

    This class is used in preference to marshmallow.ValidationError as it provides more
    precise types.
    """

    def __init__(
        self,
        field_errors: Dict[str, Dict[int, List[str]]],
        schema_errors: List[str],
        form_data: Dict[str, Any],
    ):
        """Initialise a new ValidationError."""
        self.field_errors = field_errors
        self.schema_errors = schema_errors
        self.form_data = form_data


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

        for name_, attr in chain(attrs.items()):
            if isinstance(attr, BaseField):
                marshmallow_attrs[name_] = attr.marshmallow()
                attrs["fields"][name_] = attr

        for base in bases:
            for name_ in dir(base):
                if name_ in marshmallow_attrs:
                    # don't overwrite an existing attribute with the base class
                    continue
                attr = getattr(base, name_)
                if isinstance(attr, BaseField):
                    marshmallow_attrs[name_] = attr.marshmallow()
                    attrs["fields"][name_] = attr

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

    fields: Dict[str, SingleField | CompositeField]
    _marshmallow_class: type

    def form_info(
        self,
        data: Dict[str, Any] = {},
        errors: Dict[str, Dict[int, List[str]]] = {},
        schema_errors: List[str] = [],
    ) -> FormInfo:
        """Return a FormInfo object for this Form."""
        fields = {
            name: field.field_info(
                name, data.get(name, None), errors=errors.get(name, dict())
            )
            for name, field in self.fields.items()
        }
        return FormInfo(fields=fields, schema_errors=schema_errors)

    def process(self, form_info: FormInfo) -> Dict[str, Any]:
        """Extract form data from the provided FormInfo object.

        Args:
          form_info: FormInfo object containing form data
        """
        try:
            return self._marshmallow_class().load(
                {
                    name: field.process(form_info.fields[name].input)
                    for name, field in (self.fields.items())
                }
            )
        except MarshmallowValidationError as e:
            # casts below are used to narrow expected return types as many=True is not
            # used by the underlying Marshmallow schema
            errors = cast(Dict[str, List[str] | Dict[int, List[str]]], e.messages)
            data = cast(Dict[str, Any], e.data)
            schema_errors = cast(List[str], errors.pop("_schema", []))
            field_errors = {}
            for key, value in errors.items():
                if isinstance(value, list):
                    field_errors[key] = {0: value}
                elif isinstance(value, dict):
                    field_errors[key] = value
                else:
                    ValueError("Unexpected data in Marshmallow errors")
            raise ValidationError(field_errors, schema_errors, data)
