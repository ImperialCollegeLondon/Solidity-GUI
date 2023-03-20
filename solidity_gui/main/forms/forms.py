"""Submodule defining the Form class used for data collection and validation.

Form classes aim to provide a simple, declarative approach to defining GUI components
that gather structured data from the user.
"""

from collections.abc import Mapping
from itertools import chain
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

from marshmallow import Schema
from marshmallow import ValidationError as MarshmallowValidationError
from marshmallow import fields as marshmallow_fields
from marshmallow import validates_schema

from .fields import BaseField
from .info import FieldInfo, FormInfo


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


# Define some custom recursive types to support nested forms
FormFieldType = Dict[str, Union[BaseField, "FormFieldType"]]
# Using Mapping instead of Dict below as MyPy was complaining about Dicts being
# invariant, not totally sure why that came up here only
FormErrorsType = Mapping[str, Union[Mapping[int, List[str]], "FormErrorsType"]]


class Form:
    """A Form object for collection and validation of data.

    This class should be sub-classed to add data fields to the form. Any attributes
    added that are fields.BaseField subclasses are used to define the data collected and
    validated by the form. The name of each field is taken from the name of attribute.

    By default form fields are ordered according to the orderin which they are defined
    on the class. This can be manually overridden by setting the field_order attribute
    of the class to an iterable of field names. Fields will then be ordered according to
    the specified field names with any left over fields following in the default order.

    Form sub-classes may optionally have a `validate` method. If present, this is used
    as a schema level validator for the Marshmallow Schema of the form.
    """

    fields: FormFieldType
    _marshmallow_class: type
    field_order: Optional[List[str]] = None

    def __init_subclass__(cls) -> None:
        """Initialise subclasses with additional attributes.

        When constructing a new Form subclass, this method looks for attributes that are
        Field subclasses and 1) adds a new dictionary `field` attribute containing
        name->attribute mappings and 2) uses the marshmallow method of each field to
        construct a Marshmallow Schema class for data validation.
        """
        super().__init_subclass__()
        marshmallow_attrs: Dict[str, marshmallow_fields.Field | Callable] = {}
        cls.fields = {}

        # iter through __dict__ for bases using __mro__ in order to preserve
        # order of fields according to the order they are defined
        for attr_name, attr in chain(
            *(c.__dict__.items() for c in reversed(cls.__mro__))
        ):
            if isinstance(attr, BaseField):
                cls.fields[attr_name] = attr
                marshmallow_attrs[attr_name] = attr.marshmallow()
            elif isinstance(attr, NestedForm):
                cls.fields[attr_name] = attr.form_class.fields
                marshmallow_attrs[attr_name] = marshmallow_fields.Nested(
                    attr.form_class._marshmallow_class
                )

        if schema_validator := getattr(cls, "validate", None):
            marshmallow_attrs["schema_validator"] = validates_schema(schema_validator)

        # could have used Schema.from_dict rather than the below but expected function
        # signature is not compatible with the return type of validates_schema
        cls._marshmallow_class = type(
            f"{cls.__name__}Schema", (Schema,), marshmallow_attrs
        )

    def _iter_ordered_field_items(self) -> Iterable[Tuple[str, BaseField]]:
        """Iterate over fields respecting the value of self.field_order."""
        keys = self.field_order if self.field_order else []
        for key in self.fields.keys():
            if key not in keys:
                keys.append(key)
        return ((key, getattr(self, key)) for key in keys)

    def form_info(
        self,
        data: Dict[str, Any] = {},
        errors: FormErrorsType = {},
        schema_errors: List[str] = [],
        header: Optional[str] = None,
    ) -> FormInfo:
        """Return a FormInfo object for this Form."""
        fields: Dict[str, FieldInfo | FormInfo] = {}
        for name, field in self._iter_ordered_field_items():
            # below casts differentiate between the expected datastructures
            # for fields and nested forms.
            if isinstance(field, NestedForm):
                nested_errors = cast(FormErrorsType, errors.get(name, dict()))
                fields[name] = field.form_class().form_info(
                    data.get(name, dict()),
                    errors=cast(FormErrorsType, nested_errors),
                    schema_errors=cast(List[str], nested_errors.get("_schema", [])),
                    header=field.display_name if field.display_name else name,
                )
            else:
                fields[name] = field.field_info(
                    name,
                    data.get(name, None),
                    errors=cast(Dict[int, List[str]], errors.get(name, dict())),
                )
        return FormInfo(fields=fields, schema_errors=schema_errors, header=header)

    def process(self, form_info: FormInfo, validate: bool = True) -> Dict[str, Any]:
        """Extract form data from the provided FormInfo object.

        Args:
          form_info: FormInfo object containing form data
          validate: whether to validate form data using Marshmallow
        """
        try:
            data = {}
            for name, field in self._iter_ordered_field_items():
                if isinstance(field, BaseField):
                    data[name] = field.process(
                        cast(FieldInfo, form_info.fields[name]).input
                    )
                elif isinstance(field, NestedForm):
                    # note validation is skipped for nested forms, this will be done
                    # all at once when the top level schema is validated
                    data[name] = field.form_class().process(
                        form_info.fields[name], validate=False
                    )
            if validate:
                return self._marshmallow_class().load(data)
            else:
                return data
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


class NestedForm:
    """Special Field Class denoting a NestedForm."""

    def __init__(
        self, form_class: Type[Form], display_name: Optional[str] = None
    ) -> None:
        """Create a new NestedForm.

        Args:
          form_class: the class of the form to nest
          display_name: a human friendly name for the nested form
        """
        self.form_class = form_class
        self.display_name = display_name
