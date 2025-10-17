from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        """
        Import signals khi app được load
        Method này được gọi khi Django khởi động
        """
        import users.signals  # noqa
