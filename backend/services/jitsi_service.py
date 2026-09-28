"""
Jitsi Meet integration service.
Generates unique room names and public Jitsi Meet meeting URLs.
Uses the public Jitsi domain: https://meet.jit.si/
"""

import uuid

JITSI_BASE_URL = "https://meet.jit.si"


def generate_meeting_room(request_id: int) -> str:
    """
    Generates a unique, URL-safe room name for a mentorship session.
    Format: mentor_mentee_<request_id>_<random_suffix>
    """
    unique_suffix = uuid.uuid4().hex[:12]
    return f"mentor_mentee_{request_id}_{unique_suffix}"


def get_meeting_url(meeting_room: str) -> str:
    """
    Constructs the full Jitsi Meet URL from a meeting room name.
    """
    if not meeting_room:
        return ""
    clean_room = meeting_room.strip().lstrip('/')
    return f"{JITSI_BASE_URL}/{clean_room}"
