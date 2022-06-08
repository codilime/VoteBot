import json
import string
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, Http404
from django.core.exceptions import PermissionDenied
from .message import DialogWidow
from .adapter_slackclient import slack_events_adapter, SLACK_VERIFICATION_TOKEN
from .scrap_users import get_user


CLIENT = settings.CLIENT
BOT_ID = CLIENT.api_call("auth.test")["user_id"]
WORDS_SEARCHED = ["program", "wyróżnień", "wyroznien"]

info_channels = {}


def send_info(channel, user):
    """Send info about awards program."""
    if channel not in info_channels:
        info_channels[channel] = {}
    if user in info_channels[channel]:
        return

    name = f"*Cześć {get_user(user).name.split('.')[0].capitalize()}.*\n"
    info = DialogWidow(channel)
    message = info.about_message(name=name)
    response = CLIENT.chat_postMessage(**message, text="pw_bot")
    info.timestamp = response["ts"]
    info_channels[channel][user] = info


def check_if_searched_words(message):
    msg = message.lower()
    msg = msg.translate(str.maketrans("", "", string.punctuation))
    return any(word in msg for word in WORDS_SEARCHED)


@slack_events_adapter.on("message")
def message(payload: json):
    """Respond to the phrases "program", "wyróżnień", "wyroznien".
        The bot adds a comment informing that it is
        sending a message about the highlight program in a private message.
        The bot sends a message with the content specified in the "about" file.
    @param payload: dict
    @rtype: None
    """
    event = payload.get("event", {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")

    if user_id != BOT_ID:
        if check_if_searched_words(text.lower()):
            text = "Informacje o pragramie wyróżnień prześlę Ci na pw. Sprawdź swoją skrzynkę."
            ts = event.get("ts")
            CLIENT.chat_postMessage(channel=channel_id, thread_ts=ts, text=text)
            send_info(f"@{user_id}", user_id)


def render_json_response(request, data, status=None, support_jsonp=False):
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    callback = request.GET.get("callback")
    if not callback:
        callback = request.POST.get("callback")  # in case of POST and JSONP

    if callback and support_jsonp:
        json_str = "%s(%s)" % (callback, json_str)
        response = HttpResponse(
            json_str,
            content_type="application/javascript; charset=UTF-8",
            status=status,
        )
    else:
        response = HttpResponse(
            json_str, content_type="application/json; charset=UTF-8", status=status
        )
    return response


@csrf_exempt
def slack_events(
    request, *args, **kwargs
):  # cf. https://api.slack.com/events/url_verification
    # logging.info(request.method)
    if request.method == "GET":
        raise Http404("These are not the slackbots you're looking for.")

    try:
        # https://stackoverflow.com/questions/29780060/trying-to-parse-request-body-from-post-in-django
        event_data = json.loads(request.body.decode("utf-8"))
    except ValueError as e:  # https://stackoverflow.com/questions/4097461/python-valueerror-error-message
        return HttpResponse("")

    # Echo the URL verification challenge code
    if "challenge" in event_data:
        return render_json_response(request, {"challenge": event_data["challenge"]})

    # Parse the Event payload and emit the event to the event listener
    if "event" in event_data:
        # Verify the request token
        request_token = event_data["token"]
        if request_token != SLACK_VERIFICATION_TOKEN:
            slack_events_adapter.emit("error", "invalid verification token")
            message = (
                "Request contains invalid Slack verification token: %s\n"
                "Slack adapter has: %s" % (request_token, SLACK_VERIFICATION_TOKEN)
            )
            raise PermissionDenied(message)

        event_type = event_data["event"]["type"]
        slack_events_adapter.emit(event_type, event_data)
        return HttpResponse("")

    # default case
    return HttpResponse("")
