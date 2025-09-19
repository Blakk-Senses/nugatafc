from PIL import Image
import os
from django.conf import settings

def optimize_image(image_path, max_width=1200, quality=75):
    """
    Resize and compress uploaded images.
    - max_width = maximum width (px)
    - quality = JPEG quality (0–100)
    """
    full_path = os.path.join(settings.MEDIA_ROOT, image_path)

    if not os.path.exists(full_path):
        return

    try:
        img = Image.open(full_path)

        # Only resize if wider than max_width
        if img.width > max_width:
            ratio = max_width / float(img.width)
            height = int((float(img.height) * ratio))
            img = img.resize((max_width, height), Image.LANCZOS)

        # Convert to RGB (fixes PNG with alpha)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Save optimized
        img.save(full_path, optimize=True, quality=quality)
    except Exception as e:
        print("⚠️ Image optimization failed:", e)
