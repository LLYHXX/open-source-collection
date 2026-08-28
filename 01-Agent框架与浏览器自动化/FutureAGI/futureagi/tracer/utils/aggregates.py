from django.db.models import Aggregate, JSONField


class JSONBObjectAgg(Aggregate):
    """PostgreSQL jsonb_object_agg(key, value) aggregate."""

    function = "jsonb_object_agg"
    output_field = JSONField()
