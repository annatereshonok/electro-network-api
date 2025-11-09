from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Создаёт суперпользователя, если его ещё нет"

    def add_arguments(self, parser):
        parser.add_argument("--username", required=False)
        parser.add_argument("--email", required=False)
        parser.add_argument("--password", required=True)

    def handle(self, *args, **opts):
        User = get_user_model()
        username = opts.get("username")
        email = opts.get("email")
        password = opts["password"]

        if not username and not email:
            raise CommandError("Нужно указать --username или --email.")

        user = None
        if email:
            user = User.objects.filter(email=email).first()
        if user is None and username:
            user = User.objects.filter(username=username).first()

        if user:
            if not user.is_superuser or not user.is_staff:
                user.is_superuser = True
                user.is_staff = True
                user.is_active = True
                if password:
                    user.set_password(password)
                user.save(
                    update_fields=["is_superuser", "is_staff", "is_active", "password"]
                )
                self.stdout.write(self.style.SUCCESS(f"Обновлён суперюзер: {user}"))
            else:
                self.stdout.write(
                    self.style.NOTICE("Суперпользователь уже существует - пропускаю.")
                )
            return

        kwargs = {"is_staff": True, "is_superuser": True, "is_active": True}
        if email:
            kwargs["email"] = email
        if username:
            kwargs["username"] = username

        user = User(**kwargs)
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Создан суперюзер: {user}"))
