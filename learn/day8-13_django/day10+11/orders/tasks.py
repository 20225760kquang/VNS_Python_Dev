from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Order


@shared_task
def send_order_confirmation_email(order_id):
    try:
        order = Order.objects.select_related('user').prefetch_related('items').get(pk=order_id)
    except Order.DoesNotExist:
        return 'missing-order'

    if not order.customer_email:
        return 'missing-customer-email'

    subject = f'Order #{order.id} confirmed'
    message = render_to_string(
        'orders/order_confirmation_email.txt',
        {
            'order': order,
            'items': order.items.all(),
        },
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=None,
        recipient_list=[order.customer_email],
        fail_silently=False,
    )
    return 'sent'
