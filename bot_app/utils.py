import datetime
import calendar
import logging

import pytz
from django.db.models import Sum
from .models import VotingResults
from .scrap_users import get_user, get_users

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

CATEGORIES = ["Team up to win", "Act to deliver", "Disrupt to grow"]


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
        "points_team_up_to_win": VotingResults.objects.filter(
            voted_user=get_user(voted_user), created__range=(start, end)
        ).aggregate(Sum("points_team_up_to_win"))["points_team_up_to_win__sum"],
        "points_act_to_deliver": VotingResults.objects.filter(
            voted_user=get_user(voted_user), created__range=(start, end)
        ).aggregate(Sum("points_act_to_deliver"))["points_act_to_deliver__sum"],
        "points_disrupt_to_grow": VotingResults.objects.filter(
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
    users = get_users()
    points = {
        user.slack_id: calculate_points(voted_user=user.slack_id, start=start, end=end)
        for user in users
    }
    logger.info('Points was calculated')
    logger.info('=' * 30)
    return points


def winner(start: datetime, end: datetime) -> str:
    """Find the winners in each category for current month or all time.
    Enter input params ts_start and ts_end for searching in time range.
    You can use 'get_start_end_month' method to create ts_start and ts_end parameters for searching in current month.
    @param start: datetime
    @param end: datetime
    @rtype: str
    @return: message contain information about winners
    """
    logger.info('=' * 30)
    logger.info(f'winner')
    """Collect data form database."""
    users_points = total_points(start=start, end=end)
    attributes = (
        "points_team_up_to_win",
        "points_act_to_deliver",
        "points_disrupt_to_grow",
    )
    winners, points = [], []
    for attr in attributes:
        winn = max(users_points, key=lambda v: users_points[v][attr])
        winners.append(winn)
        points.append(users_points[winn][attr])

    """Create message."""
    text = f"Wyniki głosowania w programie wyróżnień.\n"
    for i in range(3):
        text += (
            f"W kategorii '{CATEGORIES[i]}' wygrywa '{get_user(winners[i]).name}', "
            f"liczba głosów {points[i]}.\n"
        )
    return text


def get_start_end_day():
    """Calculate timestamp for start and end current day.
    @return:
        ts_start : datetime of beginning current day.
        ts_end : datetime of end current day.
    """
    today = datetime.datetime.now()
    start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end = today.replace(hour=23, minute=59, second=59, microsecond=9999)
    return start, end


def get_start_end_month():
    """Calculate timestamp for start and end current month.
    @return:
        start : datetime of beginning current month.
        end : datetime of end current month.
    """
    today = datetime.datetime.now()
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


def validate_votes_himself(voting_results: dict, voting_user_id: str) -> bool:
    """Check if the user voted for himself.
    @rtype: bool
    """
    if voting_results[0]["selected_user"] == voting_user_id:
        return False
    return True


def validate_points_amount(voting_results: dict) -> bool:
    """Check if sum all points is between 0-3.
    @rtype: bool
    """
    points = 0
    for i in range(1, 4):
        if "points" in voting_results[i]:
            points += voting_results[i]["points"]
        else:
            points += 0
    return points == 3


def validate(voting_results: dict, voting_user_id: str) -> bool:
    """Check if data from request is validate.
    @return: bool : is validate data
    """
    return all(
        [
            validate_points_amount(voting_results),
            validate_votes_himself(voting_results, voting_user_id),
        ]
    )


def error_message(voting_results: dict, voting_user_id: str) -> str:
    """Create errors message. Contain all errors.
    @rtype: Tuple[dict, str] : error message
    """
    text = ""
    if not validate_votes_himself(
        voting_results=voting_results, voting_user_id=voting_user_id
    ):
        text += "You cannot vote for yourself.\n"
    if not validate_points_amount(voting_results=voting_results):
        text += "You must give out exactly 3 points in total.\n"
    text += "Results were not saved."
    return text


def save_votes(voting_results: dict, voting_user: str) -> None:
    """Save votes to db.
    Create object and save in db.
    If exist update object with data form slack voting form.
    @return: None
    """
    logger.info('=' * 30)
    logger.info('save_votes')
    current_month = get_start_end_month()

    desc = ''
    logging.info(f'{desc}')
    try:
        desc = VotingResults.objects.filter(
            voting_user_id=get_user(voting_user),
            voted_user=get_user(voting_results[0]["selected_user"]),
            created__range=(current_month[0], current_month[1]),
        ).exists()
        logging.info(f'{desc}')
    except Exception as e:
        logger.error(f'{e}')
        logger.info('=' * 30)

    """If voting user not in db, create object."""
    try:
        if not desc:
            logger.info('Starting create user object.')
            voting_res = VotingResults.objects.create(
                voting_user_id=get_user(voting_user),
                voted_user=get_user(voting_results[0]["selected_user"]),
                points_team_up_to_win=voting_results[1]["points"],
                points_act_to_deliver=voting_results[2]["points"],
                points_disrupt_to_grow=voting_results[3]["points"],
            )
            logger.info(f'{voting_res}')
            voting_res.save()
    except Exception as e:
        logger.error(f'{e}')
        logger.info('=' * 30)

    """If user in db, update object.
    The reason for this is that saving all data form form, 
    even if the form not complete."""
    try:
        if desc:
            logger.info('Updating user object.')
            voting_res = VotingResults.objects.get(
                voting_user_id=get_user(voting_user),
                voted_user=get_user(voting_results[0]["selected_user"]),
                created__range=(current_month[0], current_month[1]),
            )
            logger.info(f'{voting_res}')
            try:
                voting_res.points_team_up_to_win = voting_results[1]["points"]
                voting_res.points_act_to_deliver = voting_results[2]["points"]
                voting_res.points_disrupt_to_grow = voting_results[3]["points"]
                logger.info(f'{voting_res}')
            except Exception as e:
                logger.error(f'{e}')
                logger.info('=' * 30)
            voting_res.save(
                update_fields=[
                    "points_team_up_to_win",
                    "points_act_to_deliver",
                    "points_disrupt_to_grow",
                ]
            )
    except Exception as e:
        logger.error(f'{e}')
        logger.info('=' * 30)


def prepare_data(request):
    """Decode data from request.
    @return: dict
    """
    logger.info('=' * 30)
    logger.info('prepare_data')
    decode_data = request.body.decode("utf-8")

    data = {}
    try:
        logger.info('Preparing data.')
        params = [param for param in decode_data.split("&")]
        for attributes in params:
            item = attributes.split("=")
            data[item[0]] = item[1]
    except Exception as e:
        logger.error(f'{e}')
        logger.info('=' * 30)
    logger.info('Data has been created successfully.')
    logger.info('=' * 30)
    return data


def create_text(voting_user_id: str, voted_user=None) -> str:
    """Create a message containing information on how the user voted.
    @return: str : information on how the user voted
    """
    logging.info('=' * 30)
    logging.info('create_text')
    current_month = get_start_end_month()
    voting_results = ''
    try:
        if voted_user is None:
            voting_results = VotingResults.objects.filter(
                voting_user_id=get_user(slack_id=voting_user_id),
                created__range=(current_month[0], current_month[1]),
            )
            logging.info('User found successfully.')
        else:
            voting_results = VotingResults.objects.filter(
                voting_user_id=get_user(slack_id=voting_user_id),
                created__range=(current_month[0], current_month[1]),
                voted_user=get_user(slack_id=voted_user)
            )
            logging.info('User found successfully.')
    except Exception as e:
        logging.error(f'{e}')
        logger.info('=' * 30)

    text = ''
    for vote in voting_results:
        text += (
            f"Użytkownikowi {vote.voted_user.name}.\n"
            f"W kategorii Team up to win przyznano {vote.points_team_up_to_win} punktów.\n"
            f"W kategorii Act to deliver przyznano {vote.points_act_to_deliver} punktów.\n"
            f"W kategorii Disrupt to grow przyznano {vote.points_disrupt_to_grow} punktów.\n\n"
        )
    logging.info('Text has been created successfully.')
    logging.info('=' * 30)
    return text


def get_name(voting_user_id):
    logging.info('=' * 30)
    logging.info('get_name')
    name = f"*Cześć {get_user(voting_user_id).name.split('.')[0].capitalize()}.*\n"
    logging.info('Success.')
    logging.info('=' * 30)
    return name

"""
1. Dodać logging
2. Save wrzucuć w try except
3. Dodawanie głosów więcej niż na jedną osobę
4. Przypomnienia 
5. submit wysyła tylko kiedy formularz jest poprawnie wypełniony 
6. testy
"""
