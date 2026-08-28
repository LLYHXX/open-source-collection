dataset_table_columns = [
    {"label": "Environment", "value": "environment", "enabled": True},
    {"label": "Version", "value": "version", "enabled": True},
    {"label": "Volume", "value": "volume", "enabled": True},
    {"label": "Start Date", "value": "startDate", "enabled": True},
    {"label": "End Date", "value": "endDate", "enabled": True},
]

optimize_table_columns = [
    {"label": "Optimization Name", "value": "name", "enabled": True},
    {"label": "Environment", "value": "environment", "enabled": True},
    {"label": "Version", "value": "version", "enabled": True},
    {"label": "Optimization Status", "value": "status", "enabled": True},
    {"label": "Created At", "value": "createdAt", "enabled": True},
    {"label": "Optimization Type", "value": "optimizeType", "enabled": True},
]

journey_operator_map = {
    "equal": "=",
    "notEqual": "!=",
    "greaterThan": ">",
    "greaterThanEqualTo": ">=",
    "lessThan": "<",
    "lessThanEqualTo": "<=",
}
