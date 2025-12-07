from django.apps import AppConfig

class GestionDonacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_donaciones'

    def ready(self):
        import gestion_donaciones.signals
