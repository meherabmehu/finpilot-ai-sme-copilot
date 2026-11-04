"""Only an actual supplied asset enables the official sticker; no replacement."""
from django.conf import settings


def buildathon(request):
    for suffix in ('png','jpg','jpeg','webp'):
        asset='buildathon/yunet-aignite-buildathon-2026-sticker.'+suffix
        if (settings.BASE_DIR/'static'/asset).is_file():
            return {'buildathon_sticker':asset}
    return {'buildathon_sticker':None}
