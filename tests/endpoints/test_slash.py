import urllib.parse

from django.http import HttpResponse
from django.test import override_settings

from bot_app.models import SlackUser
from tests.base import BaseTestCase, get_signature_headers
from tests.data import get_slash_command_data, get_text_from_file


@override_settings(SIGNING_SECRET='signing_secret')
class TestSlashCommands(BaseTestCase):
    """ Simple cases testing if app properly responds to Slack's slash commands like /about. """

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

    def test_about(self) -> None:
        command = "/about"
        data = get_slash_command_data(command=command,  user_id=self.slack_user1.slack_id)
        text = get_text_from_file(filename='about')

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["channel"] == self.slack_user1.slack_id

        content = [c.get('text', {}).get('text') for c in call_args["blocks"]]
        assert text in content

    def test_vote(self) -> None:
        command = "/vote"
        data = get_slash_command_data(command=command,  user_id=self.slack_user1.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.views_open.assert_called_once()
        call_args = self.slack_client_mock.views_open.call_args[1]
        assert call_args["trigger_id"] == data["trigger_id"]
        # TODO validate view?

    def test_check_votes(self) -> None:
        your_votes_text = f"""You voted for user {self.slack_user2.name} by awarding them:
• {self.voting_result.points_team_up_to_win} points in the category Team up to win
• {self.voting_result.points_act_to_deliver} points in the category Act to deliver
• {self.voting_result.points_disrupt_to_grow} points in the category Disrupt to grow"""
        command = "/check-votes"
        data = get_slash_command_data(command=command,  user_id=self.slack_user1.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["channel"] == self.slack_user1.slack_id
        assert self.slack_user1.real_name.split(' ')[0] in str(call_args['blocks'][0])
        assert call_args['blocks'][1]['text']['text'] == your_votes_text

    def test_check_points(self) -> None:
        your_points_text = f"""You have {self.voting_result.points_team_up_to_win} points in the Team up to win category. Congratulations!
You have {self.voting_result.points_act_to_deliver} points in the Act to deliver category. Congratulations!
You have {self.voting_result.points_disrupt_to_grow} points in the Disrupt to grow category. Congratulations!"""
        command = "/check-points"
        data = get_slash_command_data(command=command,  user_id=self.slack_user2.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["channel"] == self.slack_user2.slack_id
        assert self.slack_user2.real_name in str(call_args['blocks'][0])

        msg = call_args['blocks'][1]['text']['text']
        assert msg == your_points_text

    def test_check_winners(self) -> None:
        winners_text = f"""Results of voting in the Honors Program:
• in category Team up to win with 2 points, {self.hr_user1.name} wins
• in category Act to deliver with 1 points, {self.slack_user2.name} wins
• in category Disrupt to grow with 2 points, {self.slack_user2.name} wins"""

        command = "/check-winners"
        data = get_slash_command_data(command=command,  user_id=self.hr_user1.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["channel"] == self.hr_user1.slack_id

        msg = call_args['blocks'][1]['text']['text']
        assert msg == winners_text

    def test_forbidden_check_winners(self) -> None:
        text = get_text_from_file(filename='no_permissions')
        command = "/check-winners"
        data = get_slash_command_data(command=command,  user_id=self.slack_user1.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["channel"] == self.slack_user1.slack_id

        msg = call_args['blocks'][1]['text']['text']
        assert msg == text

    def test_top5(self) -> None:
        text = f"""Top 5 Limes in category points_team_up_to_win in a current half of year:
• {self.hr_user1.name} with 2 points
• {self.slack_user1.name} with 0 points
• {self.slack_user2.name} with 0 points
Top 5 Limes in category points_act_to_deliver in a current half of year:
• {self.slack_user2.name} with 1 points
• {self.slack_user1.name} with 0 points
• {self.hr_user1.name} with 0 points
Top 5 Limes in category points_disrupt_to_grow in a current half of year:
• {self.slack_user2.name} with 2 points
• {self.hr_user1.name} with 1 points
• {self.slack_user1.name} with 0 points"""
        command = "/check-top5"
        data = get_slash_command_data(command=command, user_id=self.hr_user1.slack_id)

        response = self._post_command(command=command, data=data)
        assert response.status_code == 200

        self.slack_client_mock.chat_postMessage.assert_called_once()
        call_args = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call_args["channel"] == self.hr_user1.slack_id

        msg = call_args['blocks'][1]['text']['text']
        assert msg == text
