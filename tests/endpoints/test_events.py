import json
from unittest import mock
from django.apps import apps
from django.test import TestCase

from bot_app.events import WORDS_SEARCHED
from bot_app.models import SlackProfile, SlackUser


class TestEventEndpoint(TestCase):
    url = '/event/hook/'
    token = 'very_important_slack_token'

    def setUp(self) -> None:
        self.slack_client_mock = mock.MagicMock()
        apps.get_app_config('bot_app').slack_client._client = self.slack_client_mock

        self.profile1 = SlackProfile.objects.create(real_name="Test User 1")
        self.slack_user1 = SlackUser.objects.create(
            slack_id="slack_user1_id", name="test.user.1", profile=self.profile1
        )

    def test_slack_api_challenge(self) -> None:
        challenge = 'slack_challenge'
        event_data = {'token': self.token, 'challenge': challenge, 'type': 'url_verification'}

        response = self.client.post(
            self.url,
            data=json.dumps(event_data),
            content_type="application/json",
        )
        assert response.status_code == 200

        data = response.json()
        assert data['challenge'] == challenge

    @mock.patch('bot_app.events.SLACK_VERIFICATION_TOKEN', token)
    def test_keyword_event(self) -> None:
        channel = 'some_channel_id'
        thread = 'some_thread_id'
        text = WORDS_SEARCHED[0]
        event_data = {
            'token': self.token,
            'event': {
                'type': 'message',
                'text': text,
                'user': self.slack_user1.slack_id,
                'ts': thread,
                'channel': channel,
                'channel_type': 'group'
            },
            'type': 'event_callback',
        }

        response = self.client.post(
            self.url,
            data=json.dumps(event_data),
            content_type="application/json",
        )
        assert response.status_code == 200

        assert self.slack_client_mock.chat_postMessage.call_count == 2
        call_args = self.slack_client_mock.chat_postMessage.call_args_list

        args = call_args[0][1]
        assert args['channel'] == channel
        assert args['thread_ts'] == thread
        assert "Sprawdź swoją skrzynkę" in args['text']  # TODO move to common var

        args = call_args[1][1]
        assert args['channel'] == f'@{self.slack_user1.slack_id}'
        assert "Lorem Ipsum" in str(args["blocks"])  # TODO move to common var
