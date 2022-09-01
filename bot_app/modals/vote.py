import logging
import json

from bot_app.models import CATEGORIES


def _get_points_field(block_id: str, text: str, values: list) -> dict:
    options = [
        {
            "text": {
                "type": "plain_text",
                "text": str(value),
                "emoji": True
            },
            "value": f"value-{value}"
        } for value in values]
    return {
        "type": "input",
        "block_id": block_id,
        "element": {
            "type": "static_select",
            "placeholder": {
                "type": "plain_text",
                "text": "Select amount of points",
                "emoji": True,
            },
            "options": options,
            "action_id": f"{block_id}-action"
        },
        "label": {
            "type": "plain_text",
            "text": text,
            "emoji": True,
        },
    }


_header = {
    "type": "header",
    "text": {
        "type": "plain_text",
        "text": "Grant somebody points in our awards program!"
    }
}
_select_user = {
    "type": "input",
    "block_id": 'select_user',
    "element": {
        "type": "users_select",
        "placeholder": {
            "type": "plain_text",
            "text": "User",
            "emoji": True,
        },
        "action_id": "select_user-action",
    },
    "label": {"type": "plain_text", "text": "Select user", "emoji": True},
}
_divider = {
    "type": "divider"
}
_points_context = {
    "type": "context",
    "elements": [
        {
            "type": "plain_text",
            "text": "You must give out exactly 3 points in total:",
            "emoji": True,
        }
    ],
}
_points_fields = [
    _get_points_field(block_id=field, text=f"{text}:", values=[0, 1, 2, 3])
    for field, text in CATEGORIES.items()

]

_comment = {
    "type": "input",

    "block_id": "comment",
    "element": {
        "type": "plain_text_input",
        "min_length": 30,
        "action_id": "comment-action"
    },
    "label": {
        "type": "plain_text",
        "text": "Comment",
        "emoji": True
    }
}
_comment_context = {
    "type": "context",
    "elements": [
        {
            "type": "plain_text",
            "text": "Describe why You're casting the vote the way You are",
            "emoji": True
        }
    ]
}


def build_voting_modal() -> dict:
    result = {
        "type": "modal",
        "title": {"type": "plain_text", "text": "Voting", "emoji": True},
        "submit": {"type": "plain_text", "text": "Submit", "emoji": True},
        "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        "blocks": [
            _header,
            _select_user,
            _divider,
            _points_context,
            *_points_fields,
            _comment,
            _comment_context
        ],
    }

    logging.warning(json.dumps(result, indent=4))
    return result

