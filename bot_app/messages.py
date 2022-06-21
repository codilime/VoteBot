def _build_blocks(content: list[str]) -> list[dict]:
    return [{"type": "section", "text": {"type": "mrkdwn", "text": text}} for text in content]


def get_text_message(channel: str, content: list[str], ts: str = None) -> dict:
    return {
        "ts": ts or "",
        "channel": channel,
        "username": "Program Wyróżnień",
        "icon_emoji": ":robot_face:",
        "blocks": _build_blocks(content),
    }
