import urllib.parse

from django.http import HttpResponse
from django.test import override_settings

from bot_app.models import SlackUser
from tests.base import BaseTestCase, get_signature_headers
from tests.data import get_slash_command_data, get_text_from_file


@override_settings(SIGNING_SECRET='signing_secret')
class TestSlashCommands(BaseTestCase):
    """ Simple cases testing if app properly responds to Slack's slash commands like /about. """
    token = 'very_important_slack_token'

    def setUp(self) -> None:
        self._mock_slack_client()
        self._add_simple_test_data()

    def _post_command(self, command: str, data: dict) -> HttpResponse:
        data = urllib.parse.urlencode(data)
        return self.client.post(
            command,
            data=data,
            content_type="application/x-www-form-urlencoded",
            **get_signature_headers(data=data)
        )

    @override_settings(SLACK_VERIFICATION_TOKEN=token)
    def test_about(self) -> None:
        command = "/about"
        data = get_slash_command_data(command=command, token=self.token, user_id=self.slack_user1.slack_id)
        text = get_text_from_file(filename='about')

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["channel"] == self.slack_user1.slack_id

        content = [c.get('text', {}).get('text') for c in call_args["blocks"]]
        assert text in content

    @override_settings(SLACK_VERIFICATION_TOKEN=token)
    def test_vote(self) -> None:
        command = "/vote"
        data = get_slash_command_data(command=command, token=self.token, user_id=self.slack_user1.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.views_open.assert_called_once()
        call_args = self.slack_client_mock.views_open.call_args[1]
        assert call_args["trigger_id"] == data["trigger_id"]
        # TODO validate view?

    @override_settings(SLACK_VERIFICATION_TOKEN=token)
    def test_check_votes(self) -> None:
        your_votes_text = f"""Użytkownikowi {self.slack_user2.name} przyznano:
{self.voting_result.points_team_up_to_win} w kategorii Team up to win
{self.voting_result.points_act_to_deliver} w kategorii Act to deliver
{self.voting_result.points_disrupt_to_grow} w kategorii Disrupt to grow"""
        command = "/check-votes"
        data = get_slash_command_data(command=command, token=self.token, user_id=self.slack_user1.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["channel"] == self.slack_user1.slack_id
        assert self.slack_user1.real_name.split(' ')[0] in str(call_args['blocks'][0])
        assert call_args['blocks'][1]['text']['text'] == your_votes_text

    @override_settings(SLACK_VERIFICATION_TOKEN=token)
    def test_check_points(self) -> None:
        your_points_text = f"""Masz {self.voting_result.points_team_up_to_win} punktów w kategorii Team up to win.
Masz {self.voting_result.points_act_to_deliver} punktów w kategorii Act to deliver.
Masz {self.voting_result.points_disrupt_to_grow} punktów w kategorii Disrupt to grow."""
        command = "/check-points"
        data = get_slash_command_data(command=command, token=self.token, user_id=self.slack_user2.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["channel"] == self.slack_user2.slack_id
        assert self.slack_user1.real_name.split(' ')[0] in str(call_args['blocks'][0])

        msg = call_args['blocks'][1]['text']['text']
        assert msg == your_points_text

    @override_settings(SLACK_VERIFICATION_TOKEN=token)
    def test_check_winners(self) -> None:
        winners_text = f"""Wyniki głosowania w programie wyróżnień:
W kategorii Team up to win mając {self.voting_result.points_team_up_to_win} głosów wygrywa {self.slack_user1.real_name}.
W kategorii Act to deliver mając {self.voting_result.points_act_to_deliver} głosów wygrywa {self.slack_user2.real_name}.
W kategorii Disrupt to grow mając {self.voting_result.points_disrupt_to_grow} głosów wygrywa {self.slack_user2.real_name}."""

        hr_user1 = SlackUser.objects.create(slack_id="hr_user1_id", name="hr.user.1", is_hr=True)
        command = "/check-winners"
        data = get_slash_command_data(command=command, token=self.token, user_id=hr_user1.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["channel"] == hr_user1.slack_id

        msg = call_args['blocks'][1]['text']['text']
        assert msg == winners_text

    @override_settings(SLACK_VERIFICATION_TOKEN=token)
    def test_forbidden_check_winners(self) -> None:
        command = "/check-winners"
        data = get_slash_command_data(command=command, token=self.token, user_id=self.slack_user1.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 403
