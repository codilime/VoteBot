from datetime import datetime

from django.conf import settings
from django.http import HttpResponse, HttpRequest, JsonResponse


def index(_: HttpRequest) -> HttpResponse:
    return JsonResponse({
        'app': 'vote-bot',
        'version': settings.VERSION,
        'timestamp': datetime.now(),
        'status': 'OK',
    })
