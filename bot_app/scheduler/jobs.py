import calendar
from datetime import datetime

from django.conf import settings

from bot_app.models import SlackUser, SlackProfile, VotingResults
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
    users = list(SlackUser.objects.filter(name__in=settings.HR_USERS))

    client = get_slack_client()
    for user in users:
        params = {"channel": user.slack_id}
        client.post_chat_message(params, text=text)


def notify_about_new_points() -> None:
    today = datetime.now().date()
    today_votes = VotingResults.objects.filter(modified__gt=today)

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

    for user in result.get("members", []):
        if not SlackUser.objects.filter(slack_id=user["id"]).exists():
            slack_profile = SlackProfile.objects.create(
                title=user["profile"]["title"],
                phone=user["profile"]["phone"],
                skype=user["profile"]["skype"],
                real_name=user["profile"]["real_name"],
                real_name_normalized=user["profile"]["real_name_normalized"],
                display_name=user["profile"]["display_name"],
                first_name=user["profile"]["first_name"],
                last_name=user["profile"]["last_name"],
                team=user["profile"]["team"],
            )
            slack_profile.save()

            slack_user = SlackUser.objects.create(
                slack_id=user["id"],
                team_id=user["team_id"],
                name=user["name"],
                deleted=user["deleted"],
                color=user["color"],
                real_name=user["real_name"],
                tz=user["tz"],
                tz_label=user["tz_label"],
                tz_offset=user["tz_offset"],
                is_admin=user["is_admin"],
                is_owner=user["is_owner"],
                is_primary_owner=user["is_primary_owner"],
                is_restricted=user["is_restricted"],
                is_ultra_restricted=user["is_ultra_restricted"],
                is_bot=user["is_bot"],
                is_app_user=user["is_app_user"],
                updated=user["updated"],
                is_email_confirmed=user["is_email_confirmed"],
                who_can_share_contact_card=user["who_can_share_contact_card"],
                profile=slack_profile,
            )
            slack_user.save()
