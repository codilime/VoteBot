"""
The module contains a collection of methods that
support voting in the award program.
"""
import json
import logging
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, Http404
from django.core.exceptions import PermissionDenied

from .adapter_slackclient import slack_events_adapter, SLACK_VERIFICATION_TOKEN
from .message import DialogWidow
from .scrap_users import get_user
from .utils import (
    calculate_points,
    create_text,
    prepare_data,
    validate,
    error_message,
    save_votes,
    get_start_end_month,
    winner,
    get_name,
)

CLIENT = settings.CLIENT
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

BOT_ID = CLIENT.api_call("auth.test")["user_id"]
CATEGORIES = ["Team up to win", "Act to deliver", "Disrupt to grow"]
info_channels = {}


@csrf_exempt
def vote(request):
    """Supports the slash method - '/vote'.
    Sends the voting form to the user.
    """
    logger.info('=' * 30)
    logger.info(f'vote')
    if request.method == "POST":
        data = prepare_data(request=request)
        logger.info('Data was decode successfully.')

        user_id = data.get("user_id")
        trigger_id = data["trigger_id"]

        vote_form = DialogWidow(channel=user_id)
        logger.info('Dialog window has been created.')

        message = vote_form.vote_message()
        logger.info('Message has been created.')

        response = CLIENT.views_open(trigger_id=trigger_id, view=message)
        logger.info('The message has been sent successfully.')
        logger.info('=' * 30)
        return HttpResponse(status=200)
    logger.error('Method POST not received.')


@csrf_exempt
def interactive(request):
    """Endpoint for receiving interactivity requests from Slack.
    The method handles the submitted voting form.
    Saves data in the database and sends the user information about the vote.
    """
    logger.info('=' * 30)
    logger.info('interactive')
    if request.method == "POST":
        data = json.loads(request.POST["payload"])
        logger.info('Data was decode successfully.')

        voting_user_id = data["user"].get("id")

        voting_results = {}
        try:
            """Prepare data (voting results) for saving in database. """
            counter = 0
            for idx in data["view"]["blocks"]:
                if idx["type"] == "input":
                    voting_results[counter] = {"block_id": idx["block_id"]}
                    counter += 1
            logger.info('Block names were correctly retrieved.')

            for counter, (block, values) in enumerate(
                    data["view"]["state"]["values"].items()
            ):
                if block == voting_results[counter]["block_id"]:
                    try:
                        if "user_select-action" in values:
                            voting_results[counter]["block_name"] = "User select"
                            voting_results[counter]["selected_user"] = values[
                                "user_select-action"
                            ]["selected_user"]
                            logger.info(f'The data on voting for the user has been correctly saved.')
                        else:
                            voting_results[counter]["block_name"] = CATEGORIES[counter - 1]
                            voting_results[counter]["points"] = int(
                                values["static_select-action"]["selected_option"]["text"][
                                    "text"
                                ]
                            )
                            logger.info('Voted points has been saved successfully.')
                    except TypeError as e:
                        voting_results[counter]["points"] = 0
                        logger.error(f"An error occurred while saving data: {e}.")
                else:
                    logger.error('There is no block_id in voting_results')
        except Exception as e:
            logger.error(f'{e}')
            logger.info('=' * 30)

        """Check if data is validate. If not send message contain errors."""
        voting_user = get_user(slack_id=voting_user_id)
        response_message = DialogWidow(channel=voting_user_id)
        logger.info('Dialog window has been created.')
        name = get_name(voting_user_id=voting_user_id)

        try:
            if not validate(voting_results=voting_results, voting_user_id=voting_user_id):
                text = error_message(voting_results, voting_user_id)
                message = response_message.check_points_message(name=name, text=text)
                response = CLIENT.chat_postMessage(**message, text="Check your votes.")
                logger.info(f'Error message has been sent successfully. Text: {text}')
                logger.info('=' * 30)
                return HttpResponse(status=200)

            else:
                """Save voting results in database and send message with voting results."""
                save_votes(voting_results=voting_results, voting_user=voting_user_id)
                logger.info('Votes has been saved.')
                text = create_text(
                    voting_user_id=voting_user_id,
                    voted_user=voting_results[0]['selected_user']
                )
                message = response_message.check_points_message(name=name, text=text)
                logger.info(f'Message has been created. Text: {text}')

                response = CLIENT.chat_postMessage(**message, text="Check your votes.")
                logger.info('Information about the voting result has been successfully sent.')
                logger.info('=' * 30)
                return HttpResponse(status=200)
        except Exception as e:
            logger.error(f'{e}')
            logger.info('=' * 30)
    logger.error('Method POST not received.')


@csrf_exempt
def check_votes(request):
    """Check user votes.
    @param request
    @return:
    """
    logger.info('=' * 30)
    logger.info('check_votes')
    if request.method == "POST":
        data = prepare_data(request=request)
        logger.info('Data was decode successfully.')

        voting_user_id = data.get("user_id")

        try:
            text = create_text(voting_user_id=voting_user_id)

            name = get_name(voting_user_id=voting_user_id)
            response_message = DialogWidow(channel=voting_user_id)
            logger.info('Dialog window has been created.')

            message = response_message.check_points_message(name=name, text=text)
            logger.info('Message has been created.')

            CLIENT.chat_postMessage(**message, text="Check your votes.")
            logger.info('The message has been sent successfully.')
            return HttpResponse(status=200)
        except Exception as e:
            logger.error(f'{e}')
    logger.error('Method POST not received.')


@csrf_exempt
def check_points(request):
    """Check the points you get in current month.
    @param: request
    @return:
    """
    logger.info('=' * 30)
    logger.info('check_points')
    data = prepare_data(request=request)
    logger.info('Data was decode successfully.')

    voted_user = data.get("user_id")
    current_month = get_start_end_month()
    try:
        points = calculate_points(
            voted_user=voted_user, start=current_month[0], end=current_month[1]
        )
        logger.info('Points were calculated correctly.')
        points_message = DialogWidow(channel=voted_user)
        logger.info('Dialog window has been created.')

        name = get_name(voting_user_id=voted_user)
        text = (
            f"Twoje punkty w kategorii 'Team up to win' to {points['points_team_up_to_win']}.\n"
            f"Twoje punkty w kategorii 'Act to deliver' to {points['points_act_to_deliver']}.\n"
            f"Twoje punkty w kategorii 'Disrupt to grow' to {points['points_disrupt_to_grow']}."
        )
        message = points_message.check_points_message(name=name, text=text)
        logger.info('Message has been created.')

        CLIENT.chat_postMessage(**message, text="Check the points you get in current month")
        logger.info('The message has been sent successfully.')
        logger.info('=' * 30)

        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f'{e}')
        logger.info('=' * 30)


@csrf_exempt
def check_winner_month(request):
    """Check winner of current month.
    @param: request
    @return:
    """
    logger.info('=' * 30)
    logger.info('check_winner_month')

    data = prepare_data(request=request)
    logger.info('Data was decode successfully.')

    voting_user_id = data.get("user_id")
    current_month = get_start_end_month()

    try:
        message = DialogWidow(channel=voting_user_id)
        logger.info('Dialog window has been created.')

        name = get_name(voting_user_id=voting_user_id)
        text = winner(start=current_month[0], end=current_month[1])
        message = message.check_points_message(name=name, text=text)
        logger.info('Message has been created.')

        CLIENT.chat_postMessage(**message, text="Check winner month.")
        logger.info('The message has been sent successfully.')
        logger.info('=' * 30)
        return HttpResponse(status=200)
    except Exception as e:
        logger.error(f'{e}')
        logger.info('=' * 30)


@csrf_exempt
def about(request):
    """Supports the slash method - '/about'.
    Send message with information about award program.
    """
    logger.info('=' * 30)
    logger.info('about')
    data = prepare_data(request=request)
    user_id = data.get("user_id")

    try:
        name = f"*Cześć {get_user(user_id).name.split('.')[0].capitalize()}.*\n"
        info_message = DialogWidow(channel=user_id)
        logger.info('Dialog window has been created.')

        message = info_message.about_message(name)
        logger.info('Message has been created.')

        CLIENT.chat_postMessage(**message, text="See information about award program")
        logger.info('The message has been sent successfully.')

        logger.info('=' * 30)
        return HttpResponse(status=200)

    except Exception as e:
        logger.error(f'{e}')
        logger.info('=' * 30)


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

