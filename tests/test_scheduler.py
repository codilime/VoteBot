import calendar
import time
from copy import deepcopy
from datetime import datetime
from unittest import mock

from django.test import TestCase, override_settings
from slack_sdk.web import SlackResponse

from bot_app.models import SlackUser, Vote
from bot_app.scheduler.jobs import (
    remind_about_program,
    announce_winners,
    send_periodic_messages,
    notify_about_new_points,
    create_users_from_slack,
)
from bot_app.scheduler.scheduler import Scheduler
from bot_app.texts import texts
from tests.base import BaseTestCase
from tests.data import slack_users_data


class TestScheduler(TestCase):
    def test_scheduler(self) -> None:
        scheduler = Scheduler(check_rate=1)

        func = mock.MagicMock()
        scheduler.every().second.do(func)
        assert func.call_count == 0

        scheduler.run()
        assert scheduler._thread.is_alive() is True

        time.sleep(3)  # Wait for scheduler to call the func.
        scheduler.stop()
        time.sleep(3)  # Wait for scheduler to stop.

        assert scheduler._thread.is_alive() is False
        assert func.call_count > 0


class TestSchedulerJobs(BaseTestCase):
    def setUp(self) -> None:
        self._mock_slack_client()
        self._add_simple_test_data()

    def test_reminder(self) -> None:
        remind_about_program()
        assert (
                self.slack_client_mock.chat_postMessage.call_count
                == SlackUser.objects.count()
        )

        text = texts.remind_about_program()
        calls = [c[1] for c in self.slack_client_mock.chat_postMessage.call_args_list]
        users_reminded = [c["channel"] for c in calls]
        assert users_reminded == [u.slack_id for u in SlackUser.objects.all()]
        assert all([text in c["text"] for c in calls])

    def test_announce_winners(self) -> None:
        winners_text = f"""Results of voting in the Honors Program:
• in category Team up to win with 2 points, {self.hr_user1.name} wins
• in category Act to deliver with 1 points, {self.slack_user2.name} wins
• in category Disrupt to grow with 2 points, {self.slack_user2.name} wins"""

        announce_winners()
        assert self.slack_client_mock.chat_postMessage.call_count == 1

        call = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call["channel"] == self.hr_user1.slack_id
        assert call["text"] == winners_text

    @mock.patch("bot_app.scheduler.jobs.announce_winners")
    @mock.patch("bot_app.scheduler.jobs.remind_about_program")
    def test_send_periodic_messages(
            self, reminder: mock.MagicMock, announcer: mock.MagicMock
    ) -> None:
        today = datetime.now()
        last_day_of_month = calendar.monthrange(today.year, today.month)[1]

        with mock.patch("bot_app.scheduler.jobs.datetime") as dt:
            dt.now.return_value = today.replace(day=last_day_of_month)
            send_periodic_messages()

        assert reminder.call_count == 0
        assert announcer.call_count == 1

        with mock.patch("bot_app.scheduler.jobs.datetime") as dt:
            dt.now.return_value = today.replace(day=last_day_of_month - 1)
            send_periodic_messages()

        assert reminder.call_count == 1
        assert announcer.call_count == 1

    def test_new_points_notification(self) -> None:
        got_voted_text = f"""1 people voted for you today!
• {self.voting_result.points_team_up_to_win} points in the category Team up to win
• {self.voting_result.points_act_to_deliver} points in the category Act to deliver
• {self.voting_result.points_disrupt_to_grow} points in the category Disrupt to grow"""

        notify_about_new_points()
        assert (
                self.slack_client_mock.chat_postMessage.call_count
                == Vote.objects.count()
        )

        call = self.slack_client_mock.chat_postMessage.call_args[1]
        assert call["channel"] == self.slack_user2.slack_id
        assert call["text"] == got_voted_text


class TestCreateUsersJobs(BaseTestCase):
    def setUp(self) -> None:
        self._mock_slack_client()

    def test_create_users_from_slack(self) -> None:
        assert SlackUser.objects.count() == 0

        # Check if record gets created.
        data = deepcopy(slack_users_data)
        response_mock = mock.MagicMock(SlackResponse)
        response_mock.data = data

        self.slack_client_mock.users_list.return_value = response_mock
        create_users_from_slack()

        assert SlackUser.objects.count() == 1
        user = SlackUser.objects.latest('created')
        assert user.real_name == data['members'][0]['real_name']

        # Check if record is updated, not created again.
        data['members'][0]['real_name'] = 'new_real_name'
        self.slack_client_mock.users_list.return_value = response_mock
        create_users_from_slack()

        assert SlackUser.objects.count() == 1
        user = SlackUser.objects.latest('created')
        assert user.real_name == data['members'][0]['real_name']
