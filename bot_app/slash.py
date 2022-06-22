"""
The module contains a collection of methods that
support voting in the award program.
"""
import logging

from django.http import HttpResponse, HttpRequest, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from bot_app.forms import UserForm, TriggerForm
from bot_app.messages import get_text_message
from bot_app.modals import get_voting_modal
from bot_app.models import SlackUser
from bot_app.texts import texts
from bot_app.utils import CATEGORIES
from bot_app.utils import calculate_points, get_start_end_month, get_winners_message, get_slack_client, get_your_votes, \
    send_about_message

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

info_channels = {}


@csrf_exempt
@require_http_methods('POST')
def vote(request):
    """ Handles '/vote' slash command. Shows user the voting form. """
    form = TriggerForm(request.POST)
    if not form.is_valid():
        errors = form.errors.as_json()
        logger.warning(errors)
        return HttpResponseBadRequest(errors)

    client = get_slack_client()
    client.open_view(trigger_id=form.cleaned_data['trigger_id'], view=get_voting_modal())
    return HttpResponse()


@csrf_exempt
@require_http_methods('POST')
def check_votes(request):
    """ Handles /check-votes slash command. Check points you've given in the current month. """
    form = UserForm(request.POST)
    if not form.is_valid():
        errors = form.errors.as_json()
        logger.warning(errors)
        return HttpResponseBadRequest(errors)

    try:
        user = SlackUser.objects.get(slack_id=form.cleaned_data['user_id'])
    except SlackUser.DoesNotExist:
        return HttpResponseBadRequest('User does not exist.')

    greeting = texts.greeting(name=user.real_name)
    votes = get_your_votes(user=user)
    message = get_text_message(channel=user.slack_id, content=[greeting, '\n\n'.join(votes)])

    client = get_slack_client()
    client.post_chat_message(message, text="Check points you've given in the current month.")
    return HttpResponse()


@csrf_exempt
@require_http_methods('POST')
def check_points(request: HttpRequest) -> HttpResponse:
    """ Handles /check-points slash command. Check your points in the current month. """
    form = UserForm(request.POST)
    if not form.is_valid():
        errors = form.errors.as_json()
        logger.warning(errors)
        return HttpResponseBadRequest(errors)

    try:
        user = SlackUser.objects.get(slack_id=form.cleaned_data['user_id'])
    except SlackUser.DoesNotExist:
        return HttpResponseBadRequest('User does not exist.')

    start, end = get_start_end_month()
    points = calculate_points(voted_user=user.slack_id, start=start, end=end)

    categories_points = []
    for field, category in CATEGORIES.items():
        categories_points.append(dict(category=category, points=points[field]))
    content = texts.your_points(values=categories_points)

    greeting = texts.greeting(name=user.real_name)
    message = get_text_message(channel=user.slack_id, content=[greeting, content])

    client = get_slack_client()
    client.post_chat_message(message, text="Check your points in the current month.")
    return HttpResponse()


@csrf_exempt
@require_http_methods('POST')
def check_winners(request):
    """ Handles /check-winners slash command. Check winners in the current month. """
    form = UserForm(request.POST)
    if not form.is_valid():
        errors = form.errors.as_json()
        logger.warning(errors)
        return HttpResponseBadRequest(errors)

    try:
        user = SlackUser.objects.get(slack_id=form.cleaned_data['user_id'])
    except SlackUser.DoesNotExist:
        return HttpResponseBadRequest('User does not exist.')

    if not user.is_hr:
        return HttpResponseForbidden('Only HR users can check winners.')  # TODO reply on slack

    start, end = get_start_end_month()
    greeting = texts.greeting(name=user.real_name)
    content = get_winners_message(start=start, end=end)
    message = get_text_message(channel=user.slack_id, content=[greeting, content])

    client = get_slack_client()
    client.post_chat_message(message, text="Check this month's winners!")
    return HttpResponse()


@csrf_exempt
@require_http_methods('POST')
def about(request: HttpRequest) -> HttpResponse:
    """ Handles /about slash command. Sends message with info on awards program. """
    form = UserForm(request.POST)
    if not form.is_valid():
        errors = form.errors.as_json()
        logger.warning(errors)
        return HttpResponseBadRequest(errors)

    try:
        user = SlackUser.objects.get(slack_id=form.cleaned_data['user_id'])
    except SlackUser.DoesNotExist:
        return HttpResponseBadRequest('User does not exist.')

    send_about_message(user=user)
    return HttpResponse()
