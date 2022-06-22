def get_slash_command_data(command: str, token: str = None, user_id: str = None) -> dict:
    return {
        "command": command,
        "text": "",
        "token": token or "token",
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


def get_text_from_file(filename: str) -> str:
    with open('./texts/' + filename) as f:
        return f.read()


slack_users_data = {
    "members": [
        dict(
            id="id",
            team_id="team_id",
            name="name",
            deleted=False,
            color="color",
            real_name="real_name",
            tz="tz",
            tz_label="tz_label",
            tz_offset="tz_offset",
            is_admin=False,
            is_owner=False,
            is_primary_owner=False,
            is_restricted=False,
            is_ultra_restricted=False,
            is_bot=False,
            is_app_user=False,
            updated=0,
            is_email_confirmed=True,
            who_can_share_contact_card="who_can_share_contact_card",
            profile=dict(
                title="title",
                phone="phone",
                skype="skype",
                real_name="real_name",
                real_name_normalized="real_name_normalized",
                display_name="display_name",
                first_name="first_name",
                last_name="last_name",
                team="team",
            ),
        )
    ]
}
