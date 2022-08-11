import calendar
import logging
from datetime import datetime

import pytz
from django.apps import apps
from django.db.models import Sum

from bot_app.apps import BotAppConfig
from bot_app.message import build_text_message
from bot_app.models import Vote, SlackUser, CATEGORIES
from bot_app.slack.client import SlackClient
from bot_app.texts import texts

logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.DEBUG)


def get_slack_client() -> SlackClient:
    return apps.get_app_config(BotAppConfig.name).slack_client


def get_user(slack_id: str) -> SlackUser:
    try:
        return SlackUser.objects.get(slack_id=slack_id)
    except SlackUser.DoesNotExist as e:
        raise ValueError(e)


def calculate_points(voted_user, start: datetime, end: datetime) -> dict:
    """Calculate points for single user in each category.
    Enter input params start and end to calculate points in selected time range.
    You can use 'get_start_end_month' or 'get_start_end_day' method to create start and end parameters.
    @param voted_user: str - slack id
    @param start: datetime
    @param end: datetime
    @rtype: dict
    @return: dict with categories as keys and sum of point as value.
    """
    logger.info('=' * 30)
    logger.info(f'calculate_points')
    points = {
        "points_team_up_to_win": Vote.objects.filter(
            voted_user=get_user(voted_user), created__range=(start, end)
        ).aggregate(Sum("points_team_up_to_win"))["points_team_up_to_win__sum"],
        "points_act_to_deliver": Vote.objects.filter(
            voted_user=get_user(voted_user), created__range=(start, end)
        ).aggregate(Sum("points_act_to_deliver"))["points_act_to_deliver__sum"],
        "points_disrupt_to_grow": Vote.objects.filter(
            voted_user=get_user(voted_user), created__range=(start, end)
        ).aggregate(Sum("points_disrupt_to_grow"))["points_disrupt_to_grow__sum"],
    }
    logger.info('Query was successful.')

    for k, v in points.items():
        if v is None:
            points[k] = 0
    logger.info('Points was calculated')
    logger.info('=' * 30)
    return points


def total_points(start: datetime, end: datetime) -> dict:
    """Calculate sum of points for each user for current month or all time.
    Enter input params start and end to calculate points for selected time range.
    You can use 'get_start_end_month' or 'get_start_end_day' method to create start and end parameters.
    @param start: datetime
    @param end: datetime
    @rtype: dict
    @return : dict contain sum of point for all slack users.
    """
    logger.info('=' * 30)
    logger.info(f'total_points')
    users = SlackUser.objects.all()
    points = {
        user.slack_id: calculate_points(voted_user=user.slack_id, start=start, end=end)
        for user in users
    }
    logger.info('Points was calculated')
    logger.info('=' * 30)
    return points


def send_about_message(user: SlackUser) -> None:
    greeting = texts.greeting(name=user.real_name)
    content = texts.about()
    message = build_text_message(channel=user.slack_id, content=[greeting, content])

    client = get_slack_client()
    client.post_chat_message(message, text="Information about awards program.")


def get_winners_message(start: datetime, end: datetime) -> str:
    """Find the winners in each category for current month or all time.
    Enter input params ts_start and ts_end for searching in time range.
    You can use 'get_start_end_month' method to create ts_start and ts_end parameters for searching in current month.
    @param start: datetime
    @param end: datetime
    @rtype: str
    @return: message contain information about winners
    """
    users_points = total_points(start=start, end=end)

    # Find winners and their points for each category.
    categories_winners = {}.fromkeys(CATEGORIES.keys())
    categories_points = {}.fromkeys(CATEGORIES.keys())
    for category in CATEGORIES.keys():
        winners = []
        winners_points = 0

        for user, values in users_points.items():
            user_points = values[category]
            if user_points > winners_points:
                winners_points = user_points
                winners = [user]
            elif user_points == winners_points:
                winners.append(user)

        categories_winners[category] = winners
        categories_points[category] = winners_points

    # Generate winners message.
    winners_data = []
    for attr, category in CATEGORIES.items():
        points = categories_points[attr]
        users = [user.name for user in SlackUser.objects.filter(slack_id__in=categories_winners[attr], is_bot=False)]
        winners_data.append(dict(category=category, points=points, user=users))
    return texts.announce_winners(values=winners_data)


def get_top5_message(start: datetime, end: datetime) -> str:
    """Find the top 5 performers in each category for current month or all time.
    Enter input params ts_start and ts_end for searching in time range.
    You can use 'get_start_end_month' method to create ts_start and ts_end parameters for searching in current month.
    @param start: datetime
    @param end: datetime
    @rtype: str
    @return: message contain information about the top 5 performers in each category
    """
    users_points = total_points(start=start, end=end)

    # Find top5 and their points for each category.
    each_categories_top5 = {}
    for category in CATEGORIES.keys():
        ordered_users = []
        for user, values in users_points.items():
            userpoints = values[category]
            if len(ordered_users) == 0:
                ordered_users.append([user, userpoints])
                continue
            for i in range(0, len(ordered_users)):
                if userpoints >= ordered_users[i][1]:
                    ordered_users.insert(i, [user, userpoints])
                    break

        each_categories_top5[category] = ordered_users[0:5]

    # Translate slack user ID's into slack usernames

    for category, top5 in each_categories_top5:
        for index, user_w_points in enumerate(top5):
            username = SlackUser.objects.get(slack_id=user_w_points[0]).name
            each_categories_top5[category][index][0] = username

    # Generate top5 message. TODO: Rewrite this segment to use the texts library
    top5_data = {
        CATEGORIES[category]: '\n'.join([f"-{user} z {points} punktami" for user, points in top5])
        for category, top5 in each_categories_top5.items()
    }
    message = "\n".join([f"Top 5 limonek w kategorii {category} w tym miesiącu:\n{top5}"
              for category, top5 in top5_data])

    return message


def get_start_end_month():
    """Calculate timestamp for start and end current month.
    @return:
        start : datetime of beginning current month.
        end : datetime of end current month.
    """
    today = datetime.now()
    start = today.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.UTC
    )
    end = today.replace(
        day=calendar.monthrange(today.year, today.month)[1],
        hour=23,
        minute=59,
        second=59,
        microsecond=9999,
        tzinfo=pytz.UTC,
    )
    return start, end


def save_vote(vote: dict, user_id: str) -> None:
    current_month = get_start_end_month()
    res = Vote.objects.filter(
        voting_user=get_user(user_id),
        voted_user=get_user(vote["selected_user"]),
        created__range=current_month,
    )

    if not res.exists():
        Vote.objects.create(
            voting_user=get_user(user_id),
            voted_user=get_user(vote["selected_user"]),
            points_team_up_to_win=vote["points_team_up_to_win"],
            points_act_to_deliver=vote["points_act_to_deliver"],
            points_disrupt_to_grow=vote["points_disrupt_to_grow"],
        )
    else:
        res = res.first()
        res.points_team_up_to_win = vote["points_team_up_to_win"]
        res.points_act_to_deliver = vote["points_act_to_deliver"]
        res.points_disrupt_to_grow = vote["points_disrupt_to_grow"]
        res.modified = datetime.now()
        res.save(
            update_fields=[
                "points_team_up_to_win",
                "points_act_to_deliver",
                "points_disrupt_to_grow",
                "modified"
            ]
        )


def get_your_votes(user: SlackUser) -> str:
    current_month = get_start_end_month()
    votes = list(Vote.objects.filter(
        voting_user=user,
        created__range=current_month,
    ))

    if not votes:
        return texts.you_have_not_voted()

    users_votes = []
    for vote in votes:
        points = []
        for field, category in CATEGORIES.items():
            points.append({'category': category, 'points': getattr(vote, field)})
        users_votes.append(texts.your_vote(values={'user': vote.voted_user.name, 'points': points}))
    return '\n\n'.join(users_votes)
