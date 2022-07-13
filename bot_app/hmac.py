import hashlib
import hmac
import time
from typing import Callable

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest


def verify_request(func: Callable) -> Callable:
    """ Wrapper for endpoints methods, to verify if request comes from Slack API. """
    # TODO Make into middleware?
    def wrapper(request: HttpRequest, *args, **kwargs) -> None:
        _verify_request(request=request)
        return func(request=request, *args, **kwargs)

    return wrapper


def _verify_request(request: HttpRequest, version: str = 'v0') -> None:
    """ By checking request's signature verifies the request actually comes from Slack API."""
    timestamp = request.headers.get('X-Slack-Request-Timestamp')

    try:
        timestamp_diff = int(time.time()) - int(timestamp)
    except (ValueError, TypeError):
        timestamp_diff = None

    if timestamp_diff is None or timestamp_diff > 60 * 5:
        raise PermissionDenied('Request timestamp invalid.')

    slack_signature = request.headers.get('X-Slack-Signature', '')
    base_string = f'{version}:{timestamp}:{request.body.decode("utf-8")}'

    hash_string = hash_data(data=base_string)
    if f'{version}={hash_string}' != slack_signature:
        raise PermissionDenied('Request signature invalid.')


def hash_data(data: str) -> str:
    """ Hashes given data with HMAC SHA256 using given key."""
    return hmac.new(
        key=bytes(settings.SIGNING_SECRET, 'utf-8'),
        msg=bytes(data, 'utf-8'),
        digestmod=hashlib.sha256).hexdigest()
