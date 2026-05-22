from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db.backends.signals import connection_created

class AuthenticationConfig(AppConfig):
    name = 'authentication'

    def ready(self):
        post_migrate.connect(create_super_admin_signal, sender=self)
        connection_created.connect(create_super_admin_connection_created)


_checked = False

def create_default_super_admin():
    try:
        from django.contrib.auth import get_user_model
        from django.db import connection
        from django.conf import settings
        
        if 'webuser' in connection.introspection.table_names():
            User = get_user_model()
            email = getattr(settings, 'EMAIL_HOST_USER', None)
            if email:
                if not User.objects.filter(email=email).exists():
                    User.objects.create_superuser(
                        email=email,
                        password="AdminPassword123",
                        name="Global Super Admin"
                    )
                    print(f"[*] Auto-created super-admin: {email} / AdminPassword123")
    except Exception as e:
        pass

def create_super_admin_signal(sender, **kwargs):
    create_default_super_admin()

def create_super_admin_connection_created(sender, connection, **kwargs):
    global _checked
    if _checked:
        return
    _checked = True
    create_default_super_admin()


