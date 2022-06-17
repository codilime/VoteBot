import urllib.parse

from django.http import HttpResponse

from tests.base import BaseTestCase


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


class TestSlashCommands(BaseTestCase):
    """ Simple cases testing if app properly responds to Slack's slash commands like /about. """

    def setUp(self) -> None:
        self._mock_slack_client()
        self._add_simple_test_data()

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
        your_points_text = f"""Masz {self.voting_result.points_team_up_to_win} punktów w kategorii Team up to win.
Masz {self.voting_result.points_act_to_deliver} punktów w kategorii Act to deliver.
Masz {self.voting_result.points_disrupt_to_grow} punktów w kategorii Disrupt to grow."""
        command = "/check-points"
        data = get_slash_command_data(command=command, user_id=self.slack_user2.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["text"] == "Check the points you get in current month"  # TODO move to common var
        assert call_args["channel"] == self.slack_user2.slack_id
        assert self.profile2.real_name.split(' ')[0] in str(call_args['blocks'][0])

        msg = call_args['blocks'][1]['text']['text']
        assert msg == your_points_text

    def test_check_winner_month(self) -> None:
        # TODO what about draws?
        winners_text = f"""Wyniki głosowania w programie wyróżnień:
W kategorii Team up to win mając {self.voting_result.points_team_up_to_win} głosów wygrywa {self.slack_user1.profile.real_name}
W kategorii Act to deliver mając {self.voting_result.points_act_to_deliver} głosów wygrywa {self.slack_user2.profile.real_name}
W kategorii Disrupt to grow mając {self.voting_result.points_disrupt_to_grow} głosów wygrywa {self.slack_user2.profile.real_name}"""

        command = "/check-winner-month"
        data = get_slash_command_data(command=command, user_id=self.slack_user1.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["text"] == "Check winner month."  # TODO move to common var
        assert call_args["channel"] == self.slack_user1.slack_id

        msg = call_args['blocks'][1]['text']['text']
        assert msg == winners_text
