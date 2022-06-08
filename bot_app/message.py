from typing import Dict

CATEGORIES = ["Team up to win", "Act to deliver", "Disrupt to grow"]


class DialogWidow:
    """Create a message with voting form."""

    """Message header"""
    START_TEXT = {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": ":mag: Search for the user you want to vote for in fallowing category.",
            "emoji": True,
        },
    }

    """Split text / message."""
    DIVIDER = {"type": "divider"}

    """Open file contain information about awards program."""
    with open("about", encoding="UTF8") as file:
        about_text = file.read()

    voting_form = {
        "type": "modal",
        "title": {"type": "plain_text", "text": "Voting Bot", "emoji": True},
        "submit": {"type": "plain_text", "text": "Submit", "emoji": True},
        "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Here is the form where you can vote in the awards program.",
                },
            },
            {
                "type": "input",
                "element": {
                    "type": "users_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select users",
                        "emoji": True,
                    },
                    "action_id": "user_select-action",
                },
                "label": {"type": "plain_text", "text": "Select a user", "emoji": True},
            },
            {
                "type": "input",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select point amount",
                        "emoji": True,
                    },
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "0", "emoji": True},
                            "value": "value-0",
                        },
                        {
                            "text": {"type": "plain_text", "text": "1", "emoji": True},
                            "value": "value-1",
                        },
                        {
                            "text": {"type": "plain_text", "text": "2", "emoji": True},
                            "value": "value-2",
                        },
                        {
                            "text": {"type": "plain_text", "text": "3", "emoji": True},
                            "value": "value-3",
                        },
                    ],
                    "action_id": "static_select-action",
                },
                "label": {
                    "type": "plain_text",
                    "text": "Category Team up to win",
                    "emoji": True,
                },
            },
            {
                "type": "input",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select point amount",
                        "emoji": True,
                    },
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "0", "emoji": True},
                            "value": "value-0",
                        },
                        {
                            "text": {"type": "plain_text", "text": "1", "emoji": True},
                            "value": "value-1",
                        },
                        {
                            "text": {"type": "plain_text", "text": "2", "emoji": True},
                            "value": "value-2",
                        },
                        {
                            "text": {"type": "plain_text", "text": "3", "emoji": True},
                            "value": "value-3",
                        },
                    ],
                    "action_id": "static_select-action",
                },
                "label": {
                    "type": "plain_text",
                    "text": "Category Act to deliver",
                    "emoji": True,
                },
            },
            {
                "type": "input",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select point amount",
                        "emoji": True,
                    },
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "0", "emoji": True},
                            "value": "value-0",
                        },
                        {
                            "text": {"type": "plain_text", "text": "1", "emoji": True},
                            "value": "value-1",
                        },
                        {
                            "text": {"type": "plain_text", "text": "2", "emoji": True},
                            "value": "value-2",
                        },
                        {
                            "text": {"type": "plain_text", "text": "3", "emoji": True},
                            "value": "value-3",
                        },
                    ],
                    "action_id": "static_select-action",
                },
                "label": {
                    "type": "plain_text",
                    "text": "Category Disrupt to grow",
                    "emoji": True,
                },
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "plain_text",
                        "text": "Remember:\n * You cannot vote for yourself.\n * You must give out exactly 3 points in total.\n* You can learn more about honors program using /about",
                        "emoji": True,
                    }
                ],
            },
        ],
    }

    def __init__(self, channel) -> None:
        self.channel = channel
        self.icon_emoji = ":robot_face:"
        self.completed = False
        self.timestamp = ""

    @staticmethod
    def get_text(text):
        return {"type": "section", "text": {"type": "mrkdwn", "text": text}}

    def message(self, *args):
        """Prepare complete message.
        @return: dict
        """
        return {
            "ts": self.timestamp,
            "channel": self.channel,
            "username": "Program Wyróżnień - bot",
            "icon_emoji": self.icon_emoji,
            "blocks": [*args],
        }

    def vote_message(self) -> Dict:
        """Prepare complete message.
        @return: dict
        """
        return self.voting_form

    def about_message(self, name) -> Dict:
        return self.message(
            self.get_text(text=name), self.get_text(text=self.about_text), self.DIVIDER
        )

    def check_points_message(self, name, text) -> Dict:
        """
        @rtype: object
        """
        return self.message(
            self.get_text(text=name),
            self.get_text(text=text),
            self.DIVIDER,
        )

    def _get_reaction_task(self):
        checkmark = ":white_check_mark:"
        if not self.completed:
            checkmark = ":white_large_square:"

        text = f"{checkmark} *React to this message!*"

        return {"type": "section", "text": {"type": "mrkdwn", "text": text}}
