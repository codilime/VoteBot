import calendar
from datetime import datetime

from django.conf import settings

from bot_app.models import SlackUser
from bot_app.texts import texts
from bot_app.utils import get_slack_client, get_start_end_month, get_winners_message


def send_periodic_messages() -> None:
    today = datetime.now()
    last_day_of_month = calendar.monthrange(today.year, today.month)[1]

    if today.day == last_day_of_month - 1:
        remind_about_program()
    elif today.day == last_day_of_month:
        announce_winners()


def remind_about_program() -> None:
    text = texts.remind_about_program()

    users = list(SlackUser.objects.filter(is_bot=False))
    client = get_slack_client()
    for user in users:
        params = {"channel": user.slack_id}
        client.post_chat_message(params, text=text)


def announce_winners() -> None:
    start, end = get_start_end_month()
    text = get_winners_message(start=start, end=end)
    users = list(SlackUser.objects.filter(name__in=settings.HR_USERS))

    client = get_slack_client()
    for user in users:
        params = {"channel": user.slack_id}
        client.post_chat_message(params, text=text)
