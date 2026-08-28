import re


def sso_name_validator(text: str):
    """
    Validator to be used For SSO name Validations.
    This is being used in frontend for SSO and catalog name validation
    """
    if re.match("^[a-zA-Z][a-zA-Z0-9-]{2,}(?<!-)$", text) is None:
        raise ValueError(
            "Please enter a value, 3 characters or longer, starting with a letter and ending with an alphanumeric character. - are allowed."
        )
