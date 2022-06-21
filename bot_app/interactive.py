import json

from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from bot_app.forms import validate_token
from bot_app.models import SlackUser
from bot_app.slash import logger
from bot_app.utils import CATEGORIES, save_vote


@csrf_exempt
@require_http_methods('POST')
def interactive(request):
    """ Endpoint for receiving interactivity requests from Slack. Currently, handles submitted voting form. """
    try:
        data = json.loads(request.POST.get('payload', ''))
    except json.JSONDecodeError as e:
        return HttpResponseBadRequest(e)

    try:
        validate_token(value=data.get('token'))
    except ValidationError as e:
        return HttpResponseBadRequest(e)

    if data.get('type') != 'view_submission':
        return HttpResponseBadRequest('Not a view submission.')

    # Get vote data.
    total_points = 0
    try:
        values = {}
        raw_values = data['view']['state']['values']

        selected_user = raw_values['select_user']['select_user-action']['selected_user']
        values['selected_user'] = selected_user

        for field in CATEGORIES.keys():
            selected_option = raw_values[field][f'{field}-action']['selected_option']
            if selected_option:
                points = int(selected_option['text']['text'])
                values[field] = points
                total_points += points
    except KeyError as e:
        msg = f'Invalid view data: {e}'
        logger.warning(msg)
        return HttpResponseBadRequest(msg)

    try:
        user = SlackUser.objects.get(slack_id=data["user"]["id"])
    except ValueError:
        msg = 'Voting user does not exist.'
        logger.warning(msg)
        return HttpResponseBadRequest(msg)
    except KeyError as e:
        logger.warning(e)
        return HttpResponseBadRequest(f'Invalid view data: {e}')

    try:
        voted_user = SlackUser.objects.get(slack_id=selected_user)
    except SlackUser.DoesNotExist:
        msg = 'Voted user does not exist.'
        logger.warning(msg)
        return HttpResponseBadRequest(msg)

    # Validate vote.
    errors = {}
    if voted_user.slack_id == user.slack_id:
        errors["select_user"] = "You cannot vote for yourself!"
    if voted_user.is_bot:
        errors["select_user"] = "You cannot vote for bots!"
    if not 0 < total_points <= 3:
        errors[list(values.keys())[-1]] = "You must give out exactly 3 points in total!"
    if errors:
        response = {
            "response_action": "errors",
            "errors": errors
        }
        return JsonResponse(response)

    save_vote(vote=values, user_id=user.slack_id)
    return HttpResponse()
