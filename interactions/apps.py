# backend/interactions/apps.py

from django.apps import AppConfig


class InteractionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interactions'

    def ready(self):
        """
        Uygulama hazır olduğunda sinyalleri import eder.
        Bu, sinyallerin Django tarafından tanınmasını sağlar.
        """
        import interactions.signals  # Sinyal dosyamızı import et
