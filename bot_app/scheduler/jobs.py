import calendar
from datetime import datetime

from bot_app.models import SlackUser, Vote
from bot_app.texts import texts
from bot_app.utils import (
    get_slack_client,
    get_start_end_month,
    get_winners_message,
    CATEGORIES,
)


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
    users = list(SlackUser.objects.filter(is_hr=True))

    client = get_slack_client()
    for user in users:
        params = {"channel": user.slack_id}
        client.post_chat_message(params, text=text)


def notify_about_new_points() -> None:
    today = datetime.now().date()
    today_votes = Vote.objects.filter(modified__gt=today)

    # Count votes per person.
    today_scores = {
        vote.voted_user.slack_id: {
            "points": dict.fromkeys(CATEGORIES.keys(), 0),
            "people": 0,
        }
        for vote in today_votes
    }

    for vote in today_votes:
        score = today_scores[vote.voted_user.slack_id]
        score["people"] += 1

        for field in CATEGORIES.keys():
            score["points"][field] += getattr(vote, field)

    # Send messages.
    client = get_slack_client()
    for user, data in today_scores.items():
        params = {"channel": user}
        text = texts.got_voted(
            {
                "people": data["people"],
                "points": [
                    {"category": CATEGORIES[field], "points": points}
                    for field, points in data["points"].items()
                ],
            }
        )
        client.post_chat_message(params, text=text)


def create_users_from_slack() -> None:
    client = get_slack_client()
    result = client.users_list()

    for data in result.data.get("members", []):
        if user := SlackUser.objects.filter(slack_id=data["id"]).first():
            user.slack_id = data["id"]
            user.name = data["name"]
            user.real_name = data["real_name"]
            user.deleted = data["deleted"]
            user.is_bot = data["is_bot"]
            user.updated = data["updated"]
        else:
            user = SlackUser.objects.create(
                slack_id=data["id"],
                name=data["name"],
                real_name=data["real_name"],
                deleted=data["deleted"],
                is_bot=data["is_bot"],
                updated=data["updated"],
            )
        user.save()
