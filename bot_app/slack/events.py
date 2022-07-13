import string

from pyee import EventEmitter

from bot_app.utils import get_slack_client, get_user, send_about_message

KEYWORDS = ["wyróżnień", "wyroznien"]

slack_events_adapter = EventEmitter()


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

    send_about_message(user=user)  # TODO send only once for hour on each channel?
    return
