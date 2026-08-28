def parse_valdation_error(e):
    errors = []
    for field, _messages in e.message_dict.items():
        errors.append(f"{field}: is in_valid")

    return errors


def parse_serialized_errors(serializer):
    error_fields = []
    for field in serializer.errors.items():
        error_fields.append(f"{field} is invalid")

    return error_fields
