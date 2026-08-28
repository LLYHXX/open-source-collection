from rest_framework import serializers


def format_validation_error(error) -> str:
    """
    Extract the error message string from a DRF ValidationError or serializer.errors dict.

    Handles:
    - ValidationError with .detail attribute
    - ReturnDict/dict from serializer.errors
    - [ErrorDetail(string='message', code='invalid')] -> 'message'
    - {'field': [ErrorDetail(...)]} -> 'message'

    Returns:
        The clean error message string
    """
    if hasattr(error, "detail"):
        detail = error.detail
    else:
        detail = error

    if isinstance(detail, list) and len(detail) > 0:
        return str(detail[0])

    if isinstance(detail, dict):
        for field, errors in detail.items():
            if isinstance(errors, list) and len(errors) > 0:
                return f"{field}: {str(errors[0])}"
            elif isinstance(errors, dict):
                for nested_field, nested_errors in errors.items():
                    if isinstance(nested_errors, list) and len(nested_errors) > 0:
                        return f"{field}.{nested_field}: {str(nested_errors[0])}"
                    return f"{field}.{nested_field}: {str(nested_errors)}"
            return f"{field}: {str(errors)}"

    return str(detail)


def format_pydantic_error(error) -> str:
    """
    Format a Pydantic ValidationError into a readable message.

    Converts:
        ValidationError([{'loc': ('filters', 'template_type'), 'msg': "Input should be...", ...}])
    Into:
        "filters.template_type: Input should be..."

    Works with both Pydantic v1 and v2.
    """
    try:
        from pydantic import ValidationError

        if isinstance(error, ValidationError):
            messages = []
            for err in error.errors():
                field = ".".join(str(loc) for loc in err.get("loc", []))
                msg = err.get("msg", "")
                messages.append(f"{field}: {msg}" if field else msg)
            return "; ".join(messages[:3])  # Cap at 3 errors to keep it readable
    except ImportError:
        pass

    return str(error)


def format_request_error(error) -> str:
    """
    Format any request validation error (DRF or Pydantic) into a readable message.

    Use this in views where the request body is validated:
        try:
            req = MyPydanticModel(**request.data)
        except Exception as e:
            return bad_request(format_request_error(e))
    """
    try:
        from pydantic import ValidationError as PydanticValidationError

        if isinstance(error, PydanticValidationError):
            return format_pydantic_error(error)
    except ImportError:
        pass

    from rest_framework.exceptions import ValidationError as DRFValidationError

    if isinstance(error, DRFValidationError):
        return format_validation_error(error)

    return str(error)
