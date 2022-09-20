import time
from datetime import date

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import send_mail

logger = get_task_logger(__name__)


@shared_task
def send_email_notification(*args, **kwargs):
    name, surname, email = args

    subject = f"New user has been created [{date.today()}]"
    message = f"""New user: {name} {surname} has been created \n
    email: {email}
    """

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[settings.NOTIFICATION_EMAIL],
        fail_silently=False,
    )

    logger.info(f"{send_email_notification.__name__} just ran")
