from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # Import custom signal
        from .signals import start_report_generation, start_report_generation_handler
        start_report_generation.connect(start_report_generation_handler)