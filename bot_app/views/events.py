import json

from django.http import HttpResponseBadRequest, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from bot_app.hmac import verify_request
from bot_app.slack.events import slack_events_adapter


@csrf_exempt
@require_http_methods('POST')
@verify_request
def slack_event(request, *args, **kwargs):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as e:
        return HttpResponseBadRequest(f"Unable to deserialize json: {e}")

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
