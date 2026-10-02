from django.apps import AppConfig


class FleetConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fleet"
    verbose_name = "Fleet Tracker"

    def ready(self):
        from fleet import dashboard  # noqa: F401  registers admin chart components
