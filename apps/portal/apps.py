from django.apps import AppConfig


class PortalConfig(AppConfig):
    name = 'apps.portal'

    def ready(self):
        from . import checks  # noqa: F401
