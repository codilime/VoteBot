import json
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from pyee import EventEmitter

from bot_app.forms import validate_token
from bot_app.utils import get_slack_client, get_user, send_about_message

KEYWORDS = ["wyróżnień", "wyroznien"]


class SlackEventAdapter(EventEmitter):
    def __init__(self, verification_token):
        EventEmitter.__init__(self)
        self.verification_token = verification_token


slack_events_adapter = SlackEventAdapter(settings.SLACK_VERIFICATION_TOKEN)


@csrf_exempt
@require_http_methods('POST')
def slack_events(request, *args, **kwargs):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as e:
        return HttpResponseBadRequest(f"Unable to deserialize json: {e}")

    # Verify the request token
    try:
        validate_token(value=data.get('token'))
    except ValidationError as e:
        return HttpResponseBadRequest(e)

    # Echo the URL verification challenge code to validate with Slack API.
    # https://api.slack.com/events/url_verification
    if challenge := data.get('challenge'):
        return JsonResponse({'challenge': challenge})

    # Parse the event payload and emit the event to the listener
    if event := data.get("event", {}):
        event_type = event.get("type")
        slack_events_adapter.emit(event_type, event)
        return HttpResponse()

    return HttpResponseBadRequest("Not a valid event.")


def contains_keywords(message: str) -> bool:
    msg = message.lower()
    msg = msg.translate(str.maketrans("", "", string.punctuation))
    return any(word in msg for word in KEYWORDS)


@slack_events_adapter.on("message")
def on_message(payload: dict) -> None:
    """ Respond to user's message with info about awards program, if message contains predefined phrases. """
    user_id = payload.get("user")
    channel_id = payload.get("channel")
    ts = payload.get("ts")
    text = payload.get("text")

    client = get_slack_client()
    user = get_user(slack_id=user_id)
    if user.is_bot or user_id == client.bot_id:
        return

    if not contains_keywords(message=text.lower()):
        return

    msg = dict(channel=channel_id, thread_ts=ts)
    text = "Informacje o pragramie wyróżnień przesłałem Ci na pw."
    client.post_chat_message(msg, text=text)

    send_about_message(user=user)  # TODO send only once for hour on each channel
    return
