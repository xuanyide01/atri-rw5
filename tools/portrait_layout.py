"""Display-only portrait geometry; encoded image pixels remain unchanged."""
import math

SCENE_HEIGHT = 286
PORTRAIT_HEIGHT = 310

def aligned_sprite(sprite, image_size, single=False):
    result = dict(sprite)
    width, height = image_size
    # Ceil the width so contain cannot shrink the height through rounding.
    result['width'] = math.ceil(width * PORTRAIT_HEIGHT / height)
    result['height'] = PORTRAIT_HEIGHT
    result['top'] = 0
    center = 216 if single else sprite['left'] + sprite['width'] / 2
    result['left'] = round(center - result['width'] / 2)
    # Keep the head at its original top. The opaque dialogue backdrop clips the
    # lower 24px, hiding the source's cut edge without cropping faces.
    return result

def visible_bottom(sprite, size, alpha_bbox):
    width, height = size
    scale = min(sprite['width'] / width, sprite['height'] / height)
    return sprite['top'] + (sprite['height'] - height * scale) / 2 + alpha_bbox[3] * scale
