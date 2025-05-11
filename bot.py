import asyncio, logging, os
from datetime import datetime
from typing import Dict, List, Set, Tuple

import discord
from discord import Interaction
from discord.ext import commands
from discord.ui import Select, View
import pytz

from config import GUILD_MEMBER_PING, RAID_REACTIONS, RAID_TEMPLATES, SIGNUP_MAPPINGS, TIMEZONE_MAPPING, TEST_CHANNEL_ID
from database import db
from utils import permission_check ,get_ping_mention, validate_time_input, fetch_signup_post, edit_signup_post, get_sorted_display_names
from views import CreateRaidFlow, CreateRaidView, UpdateRaidView

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants and configuration
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    logger.critical("DISCORD_TOKEN is not set; aborting startup.")
    import sys
    sys.exit(1)

active_raids = {}  # In-memory storage for active raids

# In-memory cache for reactions by message
signups_cache: Dict[int, Dict[str, Set[int]]] = {}

# Bot initialization
class RaidBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=[], intents=discord.Intents(guilds=True, guild_reactions=True, members=True))

    async def setup_hook(self):
        await db.initialize()
        await self.load_persistent_raids()
        await self.tree.sync()
        logger.info("Slash commands synchronized and persistent raids loaded!")

    async def load_persistent_raids(self):
        raids = await db.fetchall("""
            SELECT raid_id, raid_name, channel_id, ping_timestamp, raid_type
            FROM active_raids
        """)
        current_time = datetime.now(pytz.utc)
        for raid in raids:
            raid_id, raid_name, channel_id_str, ping_timestamp, raid_type = raid
            channel_id = int(channel_id_str)
            try:
                channel = self.get_channel(channel_id)
                if not channel:
                    channel = await self.fetch_channel(channel_id)
            except Exception as e:
                logger.warning(f"Could not fetch channel {channel_id} for raid {raid_id}: {e}")
                continue
            
            # Initialize the active_raids entry so we can cache the Message
            active_raids[raid_id] = {
                "ping_task":  None,
                "name":       raid_name,
                "raid_type":  raid_type,
                "channel_id": channel_id,
                "message":    None
                }
            # Pre-populate the in-memory sign-ups cache for this raid_id
            try:
                # Fetch the original signup message
                raid_message = await channel.fetch_message(raid_id)
                # Store it back in the cache
                active_raids[raid_id]["message"] = raid_message

                # Build the reaction cache from the message’s existing reactions
                cache: Dict[str, Set[int]] = {}
                for reaction in raid_message.reactions:
                    emoji = str(reaction.emoji)
                    uid_set: Set[int] = set()
                    async for user in reaction.users():
                        if user.bot:
                            continue
                        uid_set.add(user.id)
                    cache[emoji] = uid_set

                # Store into the global cache
                signups_cache[raid_id] = cache
                logger.info(f"Preloaded signups cache for raid {raid_id}")

            except Exception as e:
                logger.warning(f"Could not preload signups cache for raid {raid_id}: {e}")
            ping_time_utc = datetime.fromtimestamp(ping_timestamp, tz=pytz.utc)
            delay = (ping_time_utc - current_time).total_seconds()
            
            if delay > 0:
                ping_task = asyncio.create_task(self.schedule_ping(delay, channel, raid_id))
                active_raids[raid_id]["ping_task"] = ping_task
                logger.info(f"Rescheduled ping for raid {raid_id} '{raid_name}' in {delay} seconds.")
            else:
                logger.info(f"Ping time for raid {raid_id} '{raid_name}' has passed; removing record.")
                await db.execute("DELETE FROM active_raids WHERE raid_id = ?", (raid_id,))

    async def schedule_ping(self, delay: float, channel: discord.TextChannel, raid_id: int):
        try:
            # Wait until the 30‑minute warning is due
            await asyncio.sleep(delay)

            # Send the reminder
            if channel.id == TEST_CHANNEL_ID:
                await channel.send("TEST MODE: reminder ping successfully simulated!")
            else:
                await channel.send(
                    f"{GUILD_MEMBER_PING} Raid starts in 30 minutes! Please join the raid VC, head to the guild house, and submit your deck to your team lead.")

            # Purge in‑memory signups cache
            signups_cache.pop(raid_id, None)

            # Delete from the database
            await db.execute("DELETE FROM active_raids WHERE raid_id = ?", (raid_id,))

            # Remove from the in‑memory active_raids map
            if raid_id in active_raids:
                del active_raids[raid_id]

        except asyncio.CancelledError:
            logger.info(f"Scheduled ping for raid {raid_id} was cancelled.")

        except Exception as e:
            logger.error(f"Error in schedule_ping for raid {raid_id}: {e}", exc_info=True)

            # Ensure cache is also purged on errors
            signups_cache.pop(raid_id, None)

            # Cleanup DB and in‑memory state on failure
            if raid_id in active_raids:
                del active_raids[raid_id]
            await db.execute("DELETE FROM active_raids WHERE raid_id = ?", (raid_id,))

    async def close(self):
        logger.info("Performing cleanup before shutdown...")
        for raid_id in list(active_raids.keys()):
            task = active_raids[raid_id]["ping_task"]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        await db.close()
        await super().close()

bot = RaidBot()

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="Gatekeeper of the Apocalypse"))

@bot.event
async def on_raw_reaction_add(payload):
    # Quick exit if we don’t care about this message or if it’s from a bot
    raid = active_raids.get(payload.message_id)
    if not raid or (payload.member and payload.member.bot):
        return
    
    # Skip bot reactions
    if payload.member and payload.member.bot:
        return

    emoji = str(payload.emoji)
    allowed = set(RAID_REACTIONS[raid["raid_type"]])

    if emoji not in allowed:
        # Dispatch a non-blocking prune task and return immediately
        asyncio.create_task(_prune_reaction(
            channel_id=payload.channel_id,
            message_id=payload.message_id,
            emoji=emoji,
            user_id=payload.user_id
        ))
        return

    # Record valid reaction in cache
    cache = signups_cache.setdefault(payload.message_id, {})
    cache.setdefault(emoji, set()).add(payload.user_id)


async def _prune_reaction(channel_id: int, message_id: int, emoji: str, user_id: int):
    """Background task to remove one unauthorized reaction as fast as possible."""
    raid = active_raids.get(message_id)
    # Use cached Message if available
    msg = raid.get("message") if raid else None
    if not msg:
        channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
        msg = await channel.fetch_message(message_id)
        if raid:
            raid["message"] = msg

    try:
        # Remove only that single emoji instance from the offending user
        await msg.remove_reaction(emoji, discord.Object(id=user_id))
    except Exception as e:
        logger.warning(f"Could not prune reaction {emoji} on {message_id}: {e}")

@bot.event
async def on_raw_reaction_remove(payload):
    try:
        # Keep cache in-sync on un-react
        if payload.message_id in active_raids:
            cache = signups_cache.get(payload.message_id, {})
            cache.setdefault(str(payload.emoji), set()).discard(payload.user_id)
    except Exception:
        logger.exception("Error in on_raw_reaction_remove")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    logger.error(f"Error in `{interaction.command}` by {interaction.user}", exc_info=error)
    if not interaction.response.is_done():
        await interaction.response.send_message(
            "Sorry, something went wrong. Please try again later.",
            ephemeral=True
        )

class RaidSelect(Select):
    def __init__(self, raids: List[Tuple[int, str]], placeholder: str = "Select raid…"):
        options = [
            discord.SelectOption(label=name, value=str(r_id))
            for r_id, name in raids
        ]
        super().__init__(placeholder=placeholder, options=options)
        self.selected_raid: int = None

    async def callback(self, interaction: Interaction):
        self.selected_raid = int(self.values[0])
        await interaction.response.defer(ephemeral=True)

        # Strip the view to disable further interactions after success
        await interaction.edit_original_response(view=None)
        self.view.stop()

# /createraid command
@permission_check
@bot.tree.command(name="createraid", description="Create a new raid")
async def create_raid(interaction: Interaction, raid_name: str):

    # Initialize the flow state and view
    flow = CreateRaidFlow(raid_name=raid_name)
    view = CreateRaidView(flow)

    # Prompt the user with the configuration UI
    await interaction.response.send_message(
        "**Raid Configuration**\n",
        view=view,
        ephemeral=True
    )

    # Wait for the user to complete or timeout
    await view.wait()
    if not view.submitted:
        # User did not finish; abort without side-effects
        return
    
    # Strip the view to disable further interactions after success
    await interaction.edit_original_response(view=None)

    channel = interaction.channel



    # Build the timestamp tag for Discord
    ts_tag = f"<t:{flow._start_ts}:F>"

    # Render the announcement content from the template
    content = RAID_TEMPLATES[flow.raid_type].format(
        name=flow.raid_name,
        timestamp=ts_tag,
        duration=flow.duration,
        GUILD_MEMBER_PING=get_ping_mention(interaction.channel.id)
    )

    # Send the signup announcement
    signup_msg = await channel.send(content)

    # Start tracking this raid
    signups_cache[signup_msg.id] = {}
    active_raids[signup_msg.id] = {
        "ping_task": None,
        "name": flow.raid_name,
        "raid_type": flow.raid_type,
        "channel_id": channel.id,
        "message": signup_msg
    }

    # Add reactions sequentially while handling Discord's 20-reaction limit
    allowed = set(RAID_REACTIONS[flow.raid_type])

    cache = signups_cache.get(signup_msg.id, {})

    for emoji in RAID_REACTIONS[flow.raid_type]:
        # Remove any user reaction so bot’s is first
        if cache.get(emoji):
            await signup_msg.clear_reaction(emoji)

        try:
            await signup_msg.add_reaction(emoji)
        except discord.Forbidden:
            logger.warning("Max unique reactions reached; pruning unauthorized emojis")
            # Fetch fresh message state
            message = await signup_msg.channel.fetch_message(signup_msg.id)
            # Remove each reaction not in our allowed set
            for reaction in message.reactions:
                if str(reaction.emoji) not in allowed:
                    await signup_msg.clear_reaction(reaction.emoji)
            # Retry adding only this emoji
            await signup_msg.add_reaction(emoji)

    # Persist the new raid into the database for scheduling and recovery
    await db.execute(
        """
        INSERT INTO active_raids
          (raid_id, raid_name, channel_id, raid_type, start_timestamp,
           ping_timestamp, duration, tz)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            signup_msg.id,
            flow.raid_name,
            channel.id,
            flow.raid_type,
            flow._start_ts,
            flow._ping_ts,
            flow.duration,
            flow.tz
        )
    )

    # Schedule the 30-minute reminder task
    delay = flow._ping_ts - int(datetime.now(pytz.utc).timestamp())
    ping_task = asyncio.create_task(bot.schedule_ping(delay, channel, signup_msg.id))
    # Track the task in memory for possible cancellation
    active_raids[signup_msg.id]["ping_task"] = ping_task

# /updateraid command
@permission_check
@bot.tree.command(name="updateraid", description="Update or reschedule an active raid")
async def update_raid(interaction: Interaction):
    await interaction.response.defer(ephemeral=True)

    # Build choices from the in-memory cache
    raids = [(raid_id, info["name"]) for raid_id, info in active_raids.items()]
    if not raids:
        return await interaction.followup.send("There are no active raids.", ephemeral=True)

    # Prompt user to select which raid to update
    selector_view = View(timeout=60)
    selector_view.add_item(RaidSelect(raids=raids, placeholder="Select raid to update…"))
    await interaction.followup.send("Choose a raid to update:", view=selector_view, ephemeral=True)
    await selector_view.wait()

    raid_id = selector_view.children[0].selected_raid
    if raid_id is None:
        return  # user timed out or cancelled

    # Fetch full raid details in one DB call
    row = await db.fetchone(
        "SELECT raid_id, raid_name, channel_id, raid_type, start_timestamp, duration, tz "
        "FROM active_raids WHERE raid_id = ?",
        (raid_id,)
    )
    if not row:
        return await interaction.followup.send("Raid not found in database.", ephemeral=True)

    raid_id, raid_name, channel_id, raid_type, start_ts, duration, tz_code = row

    # Convert stored UTC timestamp into user's local time
    user_tz = pytz.timezone(TIMEZONE_MAPPING[tz_code])
    local_dt = datetime.fromtimestamp(start_ts, pytz.utc).astimezone(user_tz)

    # Prepare the flow with existing values
    flow = CreateRaidFlow(raid_name=raid_name)
    flow.raid_type      = raid_type
    flow.duration       = duration
    flow.date           = local_dt.strftime("%Y-%m-%d")
    flow.tz             = tz_code
    flow.start_time_str = local_dt.strftime("%I:%M%p")

    # Show the pre-filled update form
    update_view = UpdateRaidView(flow)
    update_msg = await interaction.followup.send("**Update raid details**", view=update_view, ephemeral=True)
    await update_view.wait()
    if not update_view.submitted:
        return  # User canceled

    await update_msg.edit(view=None)

    # Parse the new date/time into a UTC timestamp
    new_time = await validate_time_input(flow.start_time_str)
    new_date = datetime.strptime(flow.date, "%Y-%m-%d").date()
    combined = datetime.combine(new_date, new_time)
    localized = user_tz.localize(combined, is_dst=None)
    new_utc   = localized.astimezone(pytz.utc)
    new_start = int(new_utc.timestamp())
    new_ping  = new_start - 30 * 60  # 30 minutes before start

    # Attempt to update the sign-up post
    signup_post = await fetch_signup_post(bot, channel_id, raid_id)
    if signup_post:
        ts_tag = f"<t:{new_start}:F>"
        new_content = RAID_TEMPLATES[flow.raid_type].format(
            name=raid_name,
            timestamp=ts_tag,
            duration=flow.duration,
            GUILD_MEMBER_PING=get_ping_mention(channel_id)
        )
        await edit_signup_post(signup_post, new_content, interaction)

    # Persist the updated schedule
    await db.execute(
        "UPDATE active_raids "
        "SET start_timestamp = ?, ping_timestamp = ?, duration = ?, tz = ? "
        "WHERE raid_id = ?",
        (new_start, new_ping, flow.duration, flow.tz, raid_id)
    )

    # Cancel the old ping and reschedule
    old = active_raids.pop(raid_id, None)
    if old and old.get("ping_task"):
        old["ping_task"].cancel()

    channel = signup_post.channel if signup_post else (
        bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
    )
    delay = (datetime.fromtimestamp(new_ping, pytz.utc) - datetime.now(pytz.utc)).total_seconds()
    if delay > 0:
        task = asyncio.create_task(bot.schedule_ping(delay, channel, raid_id))
        active_raids[raid_id] = {
            "ping_task": task,
            "name":      raid_name,
            "raid_type": flow.raid_type,
            "channel_id": channel_id,
            "message":   old.get("message")
        }
    else:
        await db.execute("DELETE FROM active_raids WHERE raid_id = ?", (raid_id,))

    await interaction.followup.send("Raid updated successfully.", ephemeral=True)

# /cancelraid command
@permission_check
@bot.tree.command(name="cancelraid", description="Cancel an active raid")
async def cancel_raid(interaction: Interaction):
    await interaction.response.defer(ephemeral=True)

    # Load active raids
    raids = await db.fetchall("""
        SELECT raid_id, raid_name
        FROM active_raids
        ORDER BY raid_id DESC
    """)
    if not raids:
        return await interaction.followup.send("There are no active raids.", ephemeral=True)

    # Show dropdown
    view = View(timeout=60)
    view.add_item(RaidSelect(raids, placeholder="Select raid to cancel…"))
    await interaction.followup.send("Select a raid to cancel:", view=view, ephemeral=True)
    await view.wait()

    # Which one did they pick?
    selector: RaidSelect = view.children[0]
    raid_id = selector.selected_raid
    if raid_id is None:
        return

    # Get channel_id before deleting from DB
    row = await db.fetchone(
        "SELECT channel_id FROM active_raids WHERE raid_id = ?",
        (raid_id,)
    )
    channel_id = int(row[0]) if row else None

    # Cancel in‐memory task & caches
    info = active_raids.pop(raid_id, None)
    if info and info.get("ping_task"):
        info["ping_task"].cancel()
        try:
            await info["ping_task"]
        except asyncio.CancelledError:
            pass
    signups_cache.pop(raid_id, None)

    # Delete from database
    await db.execute("DELETE FROM active_raids WHERE raid_id = ?", (raid_id,))

    # Try to delete the original announcement
    if channel_id:
        try:
            channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
            msg = await channel.fetch_message(raid_id)
            await msg.delete()
        except discord.NotFound:
            logger.warning(f"Message {raid_id} already deleted")
        except Exception as e:
            logger.error(f"Error deleting message: {e}")

    await interaction.followup.send("Raid successfully canceled.", ephemeral=True)

# /showsignups command
@permission_check
@bot.tree.command(name="showsignups", description="Show sign-ups for an active raid")
async def showsignups(interaction: Interaction):
    await interaction.response.defer(ephemeral=True)
    logger.info(f"Sign-ups requested by {interaction.user.display_name}")

    # Fetch active raids from the database
    raids = await db.fetchall(
        "SELECT raid_id, raid_name, channel_id, raid_type FROM active_raids ORDER BY raid_id DESC"
    )
    if not raids:
        await interaction.followup.send("There are no active raids.", ephemeral=True)
        return

    # Present a dropdown for the user to select a raid
    options = [(r_id, name) for r_id, name, _, _ in raids]
    selector = RaidSelect(options, placeholder="Select raid to view sign-ups…")
    view = View(timeout=30)
    view.add_item(selector)
    await interaction.followup.send("Select a raid to view sign-ups:", view=view, ephemeral=True)
    await view.wait()

    # Abort if the user did not select anything
    raid_id = selector.selected_raid
    if raid_id is None:
        return

    # Load raid metadata and in-memory cache
    _, raid_name, _, raid_type = next(r for r in raids if r[0] == raid_id)
    mapping = SIGNUP_MAPPINGS[raid_type]
    cache = signups_cache.get(raid_id, {})
    guild = interaction.guild or await bot.fetch_guild(interaction.guild_id)

    # Build blocks so each section stays intact.
    blocks: List[str] = []

    # Title section
    blocks.append(f"**{raid_name}**")

    # Roles section (merge into one block so no empty lines between; insert blank line before the backups entry)
    role_lines = ["__**Roles**__"]
    for emoji, role_desc in mapping["roles"].items():
        if emoji == "↪️":
            role_lines.append("")
        members = get_sorted_display_names(cache.get(emoji, set()), guild) or ["None"]
        role_lines.append(f"{emoji} {role_desc}\n {', '.join(members)}")
    blocks.append("\n".join(role_lines))

    # Full roster section
    all_members = get_sorted_display_names(set().union(*cache.values()), guild) or ["None"]
    blocks.append(f"__**Full Roster**__\n{', '.join(all_members)}")

    # Total count section
    blocks.append(f"**Number of Sign-ups:** {len(all_members)}")

    # Send blocks in chunks under the 2000-character limit
    MAX_MESSAGE_LENGTH = 2000
    buffer = ""
    for block in blocks:
        # Add a single newline after each block
        prefix = "\n" if buffer else ""
        # Prepend a blank line before all but the first block
        chunk = prefix + block + "\n"

        # Flush the buffer if this block would exceed the limit
        if len(buffer) + len(chunk) > MAX_MESSAGE_LENGTH:
            await interaction.followup.send(
                buffer.rstrip(),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none()
            )
            buffer = ""

        # Append the block to the buffer
        buffer += chunk

    # Send any remaining content
    if buffer:
        await interaction.followup.send(
            buffer.rstrip(),
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none()
        )

if __name__ == "__main__":
    bot.run(TOKEN)