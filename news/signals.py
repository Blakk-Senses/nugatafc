from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.storage import default_storage
from .utils import optimize_image

@receiver(post_save)
def optimize_uploaded_images(sender, instance, **kwargs):
    """
    Optimize any uploaded image in MEDIA (e.g., CKEditor uploads).
    """
    if hasattr(instance, "image") and instance.image:
        optimize_image(instance.image.name)
