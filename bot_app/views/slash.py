from django.http import HttpResponse, HttpRequest, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from bot_app.forms import UserForm, TriggerForm
from bot_app.hmac import verify_request
from bot_app.message import build_text_message
from bot_app.modals.vote import build_voting_modal
from bot_app.models import SlackUser, CATEGORIES
from bot_app.texts import texts
from bot_app.utils import calculate_points, get_start_end_month, get_winners_message, get_slack_client, get_your_votes, \
    send_about_message, logger


@csrf_exempt
@require_http_methods('POST')
@verify_request
def vote(request):
    """ Handles '/vote' slash command. Shows user the voting form. """
    form = TriggerForm(request.POST)
    if not form.is_valid():
        errors = form.errors.as_json()
        logger.warning(errors)
        return HttpResponseBadRequest(errors)

    client = get_slack_client()
    client.open_view(trigger_id=form.cleaned_data['trigger_id'], view=build_voting_modal())
    return HttpResponse()


@csrf_exempt
@require_http_methods('POST')
@verify_request
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
    votes_text = get_your_votes(user=user)
    message = build_text_message(channel=user.slack_id, content=[greeting, votes_text])

    client = get_slack_client()
    client.post_chat_message(message, text="Check points you've given in the current month.")
    return HttpResponse()


@csrf_exempt
@require_http_methods('POST')
@verify_request
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
    message = build_text_message(channel=user.slack_id, content=[greeting, content])

    client = get_slack_client()
    client.post_chat_message(message, text="Check your points in the current month.")
    return HttpResponse()


@csrf_exempt
@require_http_methods('POST')
@verify_request
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
        content = texts.no_permissions()
    else:
        start, end = get_start_end_month()
        content = get_winners_message(start=start, end=end)

    greeting = texts.greeting(name=user.real_name)
    message = build_text_message(channel=user.slack_id, content=[greeting, content])

    client = get_slack_client()
    client.post_chat_message(message, text="Check this month's winners!")
    return HttpResponse()


@csrf_exempt
@require_http_methods('POST')
@verify_request
def about(request: HttpRequest) -> HttpResponse:
    """ Handles /about slash command. Sends message with info on awards program. """
    form = UserForm(request.POST)
    if not form.is_valid():
        errors = form.errors.as_json()
        logger.warning(errors)
        return HttpResponseBadRequest(errors)

    user_id = form.cleaned_data['user_id']
    try:
        user = SlackUser.objects.get(slack_id=user_id)
    except SlackUser.DoesNotExist:
        msg = f'User {user_id} does not exist.'
        logger.warning(msg)
        return HttpResponseBadRequest(msg)

    send_about_message(user=user)
    return HttpResponse()
