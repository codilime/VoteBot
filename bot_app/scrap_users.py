"""Module contain methods for scraping users and save this data in db"""
import json
from django.conf import settings

from .models import SlackProfile, SlackUser


CLIENT = settings.CLIENT
users_store = {}


def save_users(users_array: list) -> None:
    """Put users into the dict.
    @param users_array: user list
    @return: None
    """
    for user in users_array:
        user_id = user["id"]
        users_store[user_id] = user


def save_users_to_json_file() -> None:
    """Create json file and save users data.
    @return: None
    """
    try:
        """Connect to the slack API to get the user list."""
        result = CLIENT.users_list()
        save_users(result["members"])

        """Create json data."""
        json_users = json.dumps(users_store)

        """Save data to json file."""
        with open("json_data.json", "w") as outfile:
            outfile.write(json_users)

    except Exception as error:
        print(error)


def create_users_from_slack() -> None:
    """Connect to the slack API to get the user list.
    Save the list of users in the database.

    @rtype: None
    """
    try:
        """Connect to the slack API to get the user list."""
        result = CLIENT.users_list()
        save_users(result["members"])

        for user, attributes in users_store.items():

            """Check profile if exist in db."""
            if not SlackUser.objects.filter(slack_id=attributes["id"]).exists():
                try:
                    """Create a user profile."""
                    slack_profile = SlackProfile.objects.create(
                        title=attributes["profile"]["title"],
                        phone=attributes["profile"]["phone"],
                        skype=attributes["profile"]["skype"],
                        real_name=attributes["profile"]["real_name"],
                        real_name_normalized=attributes["profile"][
                            "real_name_normalized"
                        ],
                        display_name=attributes["profile"]["display_name"],
                        first_name=attributes["profile"]["first_name"],
                        last_name=attributes["profile"]["last_name"],
                        team=attributes["profile"]["team"],
                    )
                except Exception as error:
                    print(error)
                try:
                    """Create a user."""
                    slack_user = SlackUser.objects.create(
                        slack_id=attributes["id"],
                        team_id=attributes["team_id"],
                        name=attributes["name"],
                        deleted=attributes["deleted"],
                        color=attributes["color"],
                        real_name=attributes["real_name"],
                        tz=attributes["tz"],
                        tz_label=attributes["tz_label"],
                        tz_offset=attributes["tz_offset"],
                        is_admin=attributes["is_admin"],
                        is_owner=attributes["is_owner"],
                        is_primary_owner=attributes["is_primary_owner"],
                        is_restricted=attributes["is_restricted"],
                        is_ultra_restricted=attributes["is_ultra_restricted"],
                        is_bot=attributes["is_bot"],
                        is_app_user=attributes["is_app_user"],
                        updated=attributes["updated"],
                        is_email_confirmed=attributes["is_email_confirmed"],
                        who_can_share_contact_card=attributes[
                            "who_can_share_contact_card"
                        ],
                        profile=slack_profile,
                    )
                except Exception as error:
                    print(error)

                slack_user.save()
                slack_profile.save()
            else:
                print(
                    f"User {attributes['real_name']} exists in database. I skip adding."
                )
    except Exception as error:
        print(error)


def get_users():
    """Get data about users saved in the database."""
    users = SlackUser.objects.all()
    return users


def get_user(slack_id: str):
    """Get data about user saved in the database."""
    try:
        user = SlackUser.objects.get(slack_id=slack_id)
        return user
    except Exception as error:
        print(error)


def update_users_data(user: [dict, json]):
    """Update the data of existing users."""
    if SlackUser.objects.filter(slack_id=user["id"]).exists():
        slack_user = SlackUser.objects.get(slack_id=user["id"]).update(**user)
        slack_user.save()


def delete_user(slack_id: str) -> None:
    """Delete existing user."""
    slack_user = SlackUser.objects.get(slack_id=slack_id)
    slack_user.delete()
