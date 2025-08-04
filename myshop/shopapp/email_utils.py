from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import threading


def send_mail_async(subject, message, from_email, recipient_list, html_message=None):

    def _send_mail_thread():
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            html_message=html_message,
            fail_silently=True
        )

    thread = threading.Thread(target=_send_mail_thread)
    thread.daemon = True
    thread.start()


def send_registration_email(user):
    if not user.email:
        return

    subject = 'Добро пожаловать в магазин MehaAndShubi!'
    html_message = render_to_string('emails/registration.html', {'user': user})
    plain_message = strip_tags(html_message)

    send_mail_async(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message
    )


def send_order_confirmation_email(order):
    if not order.user.email:
        return

    subject = f'Подтверждение заказа #{order.id}'
    html_message = render_to_string('emails/order_confirmation.html', {
        'order': order,
        'user': order.user
    })
    plain_message = strip_tags(html_message)

    send_mail_async(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        html_message=html_message
    )