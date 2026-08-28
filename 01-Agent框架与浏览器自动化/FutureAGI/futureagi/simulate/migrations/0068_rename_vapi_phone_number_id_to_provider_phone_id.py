"""Rename vapi_phone_number_id → provider_phone_id on SimulationPhoneNumber.

Provider-agnostic naming to support both VAPI and LiveKit phone numbers.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("simulate", "0067_merge_20260203_1444"),
    ]

    operations = [
        migrations.RenameField(
            model_name="simulationphonenumber",
            old_name="vapi_phone_number_id",
            new_name="provider_phone_id",
        ),
    ]
