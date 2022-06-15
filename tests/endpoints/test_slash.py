import urllib.parse
from unittest import mock
from django.http import HttpResponse
from django.test import TestCase
from django.apps import apps

from bot_app.models import SlackProfile, SlackUser, VotingResults


def get_slash_command_data(command: str, user_id: str = None) -> dict:
    return {
        "command": command,
        "text": "",
        "token": "token",
        "team_id": "team_id",
        "team_domain": "team_domain",
        "channel_id": "channel_id",
        "channel_name": "channel_name",
        "user_id": user_id or "user_id",
        "user_name": "user.name",
        "api_app_id": "api_app_id",
        "is_enterprise_install": "false",
        "response_url": "response_url",
        "trigger_id": "trigger_id",
    }


class TestSlashCommands(TestCase):
    """ Simple cases testing if app properly responds to Slack's slash commands like /about. """

    def setUp(self) -> None:
        self.slack_client_mock = mock.MagicMock()
        apps.get_app_config('bot_app').slack_client._client = self.slack_client_mock

        self.profile1 = SlackProfile.objects.create(real_name="Test User 1")
        self.slack_user1 = SlackUser.objects.create(
            slack_id="slack_user1_id", name="test.user.1", profile=self.profile1
        )

        self.profile2 = SlackProfile.objects.create(real_name="Test User 2")
        self.slack_user2 = SlackUser.objects.create(
            slack_id="slack_user2_id", name="test.user.2", profile=self.profile2
        )

        self.voting_result = VotingResults.objects.create(
            voted_user=self.slack_user2,
            voting_user_id=self.slack_user1,
            points_team_up_to_win=0,
            points_act_to_deliver=1,
            points_disrupt_to_grow=2,
        )

    def _post_command(self, command: str, data: dict) -> HttpResponse:
        return self.client.post(
            command,
            data=urllib.parse.urlencode(data),
            content_type="application/x-www-form-urlencoded",
        )

    def test_about(self) -> None:
        command = "/about"
        data = get_slash_command_data(command=command, user_id=self.slack_user1.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["text"] == "See information about award program"  # TODO move to common var
        assert call_args["channel"] == self.slack_user1.slack_id
        assert "Lorem Ipsum" in str(call_args["blocks"])  # TODO move to common var

    def test_vote(self) -> None:
        command = "/vote"
        data = get_slash_command_data(command=command, user_id=self.slack_user1.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.views_open.assert_called_once()
        call_args = self.slack_client_mock.views_open.call_args[1]
        assert call_args["trigger_id"] == data["trigger_id"]
        # TODO validate view?

    def test_check_votes(self) -> None:
        command = "/check-votes"
        data = get_slash_command_data(command=command, user_id=self.slack_user1.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["text"] == "Check your votes."  # TODO move to common var
        assert call_args["channel"] == self.slack_user1.slack_id
        assert self.profile1.real_name.split(' ')[0] in str(call_args['blocks'][0])

        msg = str(call_args['blocks'][1])
        assert self.slack_user2.name in msg
        assert f'Team up to win przyznano {self.voting_result.points_team_up_to_win}' in msg
        assert f'Act to deliver przyznano {self.voting_result.points_act_to_deliver}' in msg
        assert f'Disrupt to grow przyznano {self.voting_result.points_disrupt_to_grow}' in msg

    def test_check_points(self) -> None:
        command = "/check-points"
        data = get_slash_command_data(command=command, user_id=self.slack_user2.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["text"] == "Check the points you get in current month"  # TODO move to common var
        assert call_args["channel"] == self.slack_user2.slack_id
        assert self.profile2.real_name.split(' ')[0] in str(call_args['blocks'][0])

        msg = str(call_args['blocks'][1])
        assert f"Team up to win' to {self.voting_result.points_team_up_to_win}" in msg
        assert f"Act to deliver' to {self.voting_result.points_act_to_deliver}" in msg
        assert f"Disrupt to grow' to {self.voting_result.points_disrupt_to_grow}" in msg

    def test_check_winner_month(self) -> None:
        command = "/check-winner-month"
        data = get_slash_command_data(command=command, user_id=self.slack_user1.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["text"] == "Check winner month."  # TODO move to common var
        assert call_args["channel"] == self.slack_user1.slack_id

        msg = str(call_args['blocks'][1])
        # 'Team up to win' wygrywa 'test.user.1', liczba głosów 0. # TODO what about draws?
        assert f"'Act to deliver' wygrywa '{self.slack_user2.name}', liczba głosów {self.voting_result.points_act_to_deliver}." in msg
        assert f"'Disrupt to grow' wygrywa '{self.slack_user2.name}', liczba głosów {self.voting_result.points_disrupt_to_grow}." in msg
