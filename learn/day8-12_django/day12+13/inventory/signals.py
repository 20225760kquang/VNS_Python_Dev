from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ProductImage
from .tasks import process_product_image


@receiver(post_save, sender=ProductImage)
def enqueue_image_processing(sender, instance, created, **kwargs):
    if created and instance.image:
        process_product_image.delay(instance.pk)
