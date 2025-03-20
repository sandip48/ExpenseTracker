from django.apps import AppConfig
import importlib

class MyPocketConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'MyPocket'

    def ready(self):
        """ Import signals to ensure they are always loaded """
        try:
            importlib.import_module('MyPocket.signals')  # ✅ More reliable import
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to import signals: {e}")
