def get_data_points_columns(metrics=None):
    if metrics is None:
        metrics = []
    columns = [
        {"label": "Input", "value": "input", "enabled": True},
        {"label": "Output", "value": "output", "enabled": True},
    ]
    columns.append({"label": "Date Created", "value": "dateCreated", "enabled": True})
    for metric in metrics:
        columns.append(
            {
                "label": metric["name"],
                "value": str(metric["id"]),
                "enabled": True,
            }
        )

    return columns
