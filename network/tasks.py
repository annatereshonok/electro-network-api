from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from .models import Unit

User = get_user_model()


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_notification_debt(self):
    qs = (
        Unit.objects.filter(debt_to_supplier__gt=0)
        .select_related("supplier")
        .exclude(email__isnull=True)
        .exclude(email__exact="")
    )

    today = timezone.now().date().isoformat()
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")

    for unit in qs:
        company = unit.name
        supplier_name = unit.supplier.name if unit.supplier else "Поставщик не указан"
        debt = unit.debt_to_supplier

        subject = f"Задолженность компании «{company}» перед «{supplier_name}»"
        message = (
            f"Добрый день!\n\n"
            f"На {today} сумма задолженности составляет: {debt}.\n"
            f"Поставщик: {supplier_name}.\n\n"
            f"Если вы уже произвели оплату — игнорируйте это письмо."
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[unit.email],
            fail_silently=False,
        )
