from io import BytesIO

from celery import shared_task
from django.core.files.base import ContentFile
from PIL import Image

from .models import ProductImage


@shared_task
def process_product_image(image_id):
    try:
        product_image = ProductImage.objects.get(pk=image_id)
    except ProductImage.DoesNotExist:
        return "missing-image"

    if not product_image.image:
        return "no-file"

    with product_image.image.open("rb") as f:
        img = Image.open(f)
        img = img.convert("RGB")
        img.thumbnail((1200, 1200))

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)

        filename = product_image.image.name.rsplit(".", 1)[0] + ".jpg"
        product_image.image.save(filename, ContentFile(buffer.read()), save=True)

    return "processed"
