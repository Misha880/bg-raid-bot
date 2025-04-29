import re
from datetime import datetime
from functools import wraps
from discord import Interaction
from config import GUILD_LEADER_ROLE_ID, RAID_CAPTAIN_ROLE_ID, GUILD_MEMBER_PING, TEST_CHANNEL_ID

# Permission decorator
def permission_check(func):
    @wraps(func)
    async def wrapper(interaction: Interaction, *args, **kwargs):
        if not any(r.id in (GUILD_LEADER_ROLE_ID, RAID_CAPTAIN_ROLE_ID)
                   for r in interaction.user.roles):
            return await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )
        return await func(interaction, *args, **kwargs)
    return wrapper

def get_ping_mention(channel_id: int) -> str:
    """Return TEST MODE in the test channel, otherwise the real guild member ping."""
    return "TEST MODE" if channel_id == TEST_CHANNEL_ID else GUILD_MEMBER_PING

# Time parsing patterns for user input
_TIME_PATTERNS = [
    (re.compile(r"^(\d{1,2}):?(\d{2})?([AP]M)$", re.IGNORECASE),
     lambda g: f"{g[0]}:{g[1] or '00'}{g[2]}"),
    (re.compile(r"^(\d{1,2})([AP]M)$", re.IGNORECASE),
     lambda g: f"{g[0]}:00{g[1]}"),
    (re.compile(r"^(\d{1,2}):(\d{2})$", re.IGNORECASE),
     lambda g: f"{g[0]}:{g[1]}"),
    (re.compile(r"^(\d{3,4})$", re.IGNORECASE),
     lambda g: f"{g[0][:-2]}:{g[0][-2:]}"),
    (re.compile(r"^(\d{1,2})$", re.IGNORECASE),
     lambda g: f"{g[0]}:00"),
]

async def validate_time_input(time_str: str) -> datetime.time:
    """Parse various time formats into a datetime.time object."""
    s = time_str.upper().replace(" ", "")
    for regex, formatter in _TIME_PATTERNS:
        m = regex.fullmatch(s)
        if not m:
            continue
        formatted = formatter(m.groups())
        try:
            # Detect AM/PM vs 24h format
            if formatted[-2:].upper() in ("AM", "PM"):
                return datetime.strptime(formatted, "%I:%M%p").time()
            return datetime.strptime(formatted, "%H:%M").time()
        except ValueError:
            continue
    raise ValueError("Invalid time format, please try again.")

async def fetch_signup_post(bot, channel_id: int, message_id: int):
    """Fetch the signup message or return None if not found."""
    try:
        channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
        return await channel.fetch_message(message_id)
    except Exception:
        return None

async def edit_signup_post(signup_post, new_content: str, interaction):
    """Edit the signup post; notify if permissions prevent editing."""
    try:
        await signup_post.edit(content=new_content)
    except Exception:
        await interaction.followup.send(
            "Updated in the database but couldn't edit the signup post. Check my permissions?",
            ephemeral=True
        )