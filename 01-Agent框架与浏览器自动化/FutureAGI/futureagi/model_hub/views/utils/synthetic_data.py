from model_hub.models.choices import DataTypeChoices


def determine_data_type_syn_data(data_type):
    value = getattr(DataTypeChoices, data_type.upper()).value
    return value
