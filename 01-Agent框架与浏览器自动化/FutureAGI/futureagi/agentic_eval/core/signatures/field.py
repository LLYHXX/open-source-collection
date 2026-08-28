import pydantic

# The following arguments can be used in tfc Field in addition
# to the standard pydantic.Field arguments. We just hope pydanitc doesn't add these,
# as it would give a name clash.
TFC_FIELD_ARG_NAMES = ["desc", "prefix", "format", "parser", "tfc_field_type"]


def move_kwargs(**kwargs):
    # Pydantic doesn't allow arbitrary arguments to be given to fields,
    # but asks that
    # > any extra data you want to add to the JSON schema should be passed
    # > as a dictionary to the json_schema_extra keyword argument.
    # See: https://docs.pydantic.dev/2.6/migration/#changes-to-pydanticfield
    pydantic_kwargs = {}
    json_schema_extra = {}
    for k, v in kwargs.items():
        if k in TFC_FIELD_ARG_NAMES:
            json_schema_extra[k] = v
        else:
            pydantic_kwargs[k] = v
    # Also copy over the pydantic "description" if no dspy "desc" is given.
    if "description" in kwargs and "desc" not in json_schema_extra:
        json_schema_extra["desc"] = kwargs["description"]
    pydantic_kwargs["json_schema_extra"] = json_schema_extra
    return pydantic_kwargs


def InputField(**kwargs):
    if "default" not in kwargs:
        kwargs["default"] = None
    return pydantic.Field(**move_kwargs(**kwargs, tfc_field_type="input"))


def InputListField(**kwargs):
    if "default" not in kwargs:
        kwargs["default_factory"] = list
    return pydantic.Field(**move_kwargs(**kwargs, tfc_field_type="input_list"))


def ImageField(**kwargs):
    if "default" not in kwargs:
        kwargs["default"] = None
    return pydantic.Field(**move_kwargs(**kwargs, tfc_field_type="image"))


def ImageListField(**kwargs):
    if "default" not in kwargs:
        kwargs["default_factory"] = list
    return pydantic.Field(**move_kwargs(**kwargs, tfc_field_type="image_list"))


def OutputListField(**kwargs):
    if "default" not in kwargs:
        kwargs["default_factory"] = list
    return pydantic.Field(**move_kwargs(**kwargs, tfc_field_type="output_list"))


def OutputField(**kwargs):
    if "default" not in kwargs:
        kwargs["default"] = None
    return pydantic.Field(**move_kwargs(**kwargs, tfc_field_type="output"))
