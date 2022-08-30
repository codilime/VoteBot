import json
import logging

from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from bot_app.utils import get_slack_client, get_start_end_half_year
from bot_app.slack.client import SlackClient
from bot_app.message import build_text_message
from bot_app.hmac import verify_request
from bot_app.models import SlackUser, CATEGORIES, Vote
from bot_app.utils import save_vote
from bot_app.views.slash import logger
from bot_app.modals.get_comments import check_comments_header


@csrf_exempt
@require_http_methods('POST')
@verify_request
def interactive(request):
    """ Endpoint for receiving interactivity requests from Slack. Currently, handles submitted voting form and user
    selection form for viewing a user's comments. """
    try:
        data = json.loads(request.POST.get('payload', ''))
    except json.JSONDecodeError as e:
        return HttpResponseBadRequest(e)
    logger.warning(f"<DEBUG>data:\n{json.dumps(data, indent=4)}")
    if data.get('type') != 'view_submission':
        return HttpResponseBadRequest('Not a view submission.')

    # TODO: fix this abomination ( looking for slack block in payload ). perhaps you can set ID of an entire form ?
    if check_comments_header in data['view']['blocks']:
        selected_user_slack_id = data['view']['state']['values']['select_user']['select_user-action']['selected_user']
        selected_user = SlackUser.objects.get(slack_id=selected_user_slack_id)

        start, end = get_start_end_half_year()
        comments_authors = [(vote.comment, vote.voting_user.real_name)
                            for vote in Vote.objects.filter(voted_user=selected_user, created__range=(start, end))]
        # TODO: use the texts module
        comments_message_header = f"Komentarze dane użytkownikowi {selected_user.real_name} w tym półroczu:"
        comment_list = '\n\n'.join([f"• {author}: {comment}" for comment, author in comments_authors])

        message = build_text_message(channel=data["user"]["id"], content=[comments_message_header, comment_list])
        client = get_slack_client()
        client.post_chat_message(message, text="Information about awards program.")
    else:

        # Get vote data.
        total_points = 0
        try:
            values = {}
            raw_values = data['view']['state']['values']
            # logging.warning(json.dumps(raw_values, indent=4))

            selected_user_slack_id = raw_values['select_user']['select_user-action']['selected_user']
            values['selected_user'] = selected_user_slack_id
            values["comment"] = raw_values["comment"][f'comment-action']['value']

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
            voted_user = SlackUser.objects.get(slack_id=selected_user_slack_id)
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
        if total_points != 3:
            errors[list(values.keys())[-1]] = "You must give out exactly 3 points in total!"
        if errors:
            response = {
                "response_action": "errors",
                "errors": errors
            }
            return JsonResponse(response)

        save_vote(vote=values, user_id=user.slack_id)
    return HttpResponse()
