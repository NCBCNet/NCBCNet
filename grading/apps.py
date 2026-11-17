from django.apps import AppConfig


class GradingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "grading"

    def ready(self):
        from . import signals  # noqa: F401

