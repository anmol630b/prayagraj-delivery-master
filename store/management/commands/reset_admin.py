from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            u = User.objects.get(username='admin')
            u.set_password('Admin@1234')
            u.is_superuser = True
            u.is_staff = True
            u.save()
            self.stdout.write('Password reset done!')
        except User.DoesNotExist:
            User.objects.create_superuser('admin', 'admin@prayagraj.com', 'Admin@1234')
            self.stdout.write('Superuser created!')
