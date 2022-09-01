check_comments_header = {
                "type": "header",
                "block_id": "check_comments_header",
                "text": {
                    "type": "plain_text",
                    "text": "View all comments given to a user",
                    "emoji": True
                }
            }

def build_comments_modal() -> dict:
    modal = x = {
        "title": {
            "type": "plain_text",
            "text": "Voting",
            "emoji": True
        },
        "submit": {
            "type": "plain_text",
            "text": "Submit",
            "emoji": True
        },
        "type": "modal",
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": True
        },
        "blocks": [
            check_comments_header,
            {
                "type": "divider"
            },
            {
                "type": "input",
                "block_id": "select_user",
                "element": {
                    "type": "users_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "User",
                        "emoji": True
                    },
                    "action_id": "select_user-action"
                },
                "label": {
                    "type": "plain_text",
                    "text": "Select user",
                    "emoji": True
                }
            }
        ]
    }

    return modal
