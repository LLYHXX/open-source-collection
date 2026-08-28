# Note: Signals are registered via AppConfig.ready() in tfc/apps.py
# Do NOT import signals here as it causes Django import issues
# when importing tfc.telemetry before Django is configured.
