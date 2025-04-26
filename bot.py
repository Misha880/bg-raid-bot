import asyncio, logging, os
from datetime import datetime
from typing import Dict, List, Set, Tuple

import discord
from discord import Interaction
from discord.ext import commands
from discord.ui import Select, View
from discord.utils import escape_markdown
import pytz

from config import GUILD_MEMBER_PING, RAID_REACTIONS, RAID_TEMPLATES, SIGNUP_MAPPINGS, TIMEZONE_MAPPING
from database import db
from utils import permission_check, validate_time_input, fetch_signup_post, edit_signup_post
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

            # Pre-populate the in-memory sign-ups cache for this raid_id
            try:
                raid_message = await channel.fetch_message(raid_id)
                cache: Dict[str, Set[str]] = {}
                for reaction in raid_message.reactions:
                    emoji = str(reaction.emoji)
                    uid_set: Set[int] = set()
                    async for user in reaction.users():
                        if user.bot:
                            continue
                        uid_set.add(user.id)
                    cache[emoji] = uid_set
                signups_cache[raid_id] = cache
                logger.info(f"Preloaded signups cache for raid {raid_id}")
            except Exception as e:
                logger.warning(f"Could not preload signups cache for raid {raid_id}: {e}")

            ping_time_utc = datetime.fromtimestamp(ping_timestamp, tz=pytz.utc)
            delay = (ping_time_utc - current_time).total_seconds()
            
            if delay > 0:
                ping_task = asyncio.create_task(self.schedule_ping(delay, channel, raid_id))
                active_raids[raid_id] = {
                    "ping_task": ping_task, 
                    "name": raid_name, 
                    "raid_type": raid_type,
                    "channel_id": channel_id
                }
                logger.info(f"Rescheduled ping for raid {raid_id} '{raid_name}' in {delay} seconds.")
            else:
                logger.info(f"Ping time for raid {raid_id} '{raid_name}' has passed; removing record.")
                await db.execute("DELETE FROM active_raids WHERE raid_id = ?", (raid_id,))

    async def schedule_ping(self, delay: float, channel: discord.TextChannel, raid_id: int):
        try:
            # Wait until the 30‑minute warning is due
            await asyncio.sleep(delay)

            # Send the reminder
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

            # ensure cache is also purged on errors
            signups_cache.pop(raid_id, None)

            # cleanup DB and in‑memory state on failure
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
    try:
        # Look up raid in memory
        raid_info = active_raids.get(payload.message_id)
        if not raid_info:
            return

        guild = bot.get_guild(payload.guild_id) or await bot.fetch_guild(payload.guild_id)
        member = payload.member or guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
        if member.bot:
            return

        emoji = str(payload.emoji)
        raid_type = raid_info["raid_type"]

        # Build allowed reactions set
        allowed = set(RAID_REACTIONS.get(raid_type, []))
        allowed.add(SIGNUP_MAPPINGS[raid_type]["backup"])

        # Strip any unauthorized emoji
        if emoji not in allowed:
            channel = bot.get_channel(payload.channel_id) or await bot.fetch_channel(payload.channel_id)
            msg = await channel.fetch_message(payload.message_id)
            await msg.remove_reaction(payload.emoji, member)
            return

        # Store user ID in cache
        cache = signups_cache.setdefault(payload.message_id, {})
        cache.setdefault(emoji, set()).add(payload.user_id)

    except Exception:
        logger.exception("Error in on_raw_reaction_add")

@bot.event
async def on_raw_reaction_remove(payload):
    try:
        # Keep cache in-sync on un-react
        if payload.message_id in active_raids:
            cache = signups_cache.get(payload.message_id, {})
            cache.get(str(payload.emoji), set()).discard(payload.user_id)
    except Exception:
        logger.exception("Error in on_raw_reaction_remove")

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
        await interaction.edit_original_response(view=None)
        self.view.stop()

# /createraid command
@permission_check
@bot.tree.command(name="createraid", description="Create a new raid")
async def create_raid(
    interaction: Interaction,
    raid_name: str
):
    # Initialize creation flow
    flow = CreateRaidFlow(raid_name=raid_name)
    view = CreateRaidView(flow)

    # Send initial configuration message
    await interaction.response.send_message(
        "**Raid Configuration**\n",
        view=view,
        ephemeral=True
    )

# /updateraid command
@permission_check
@bot.tree.command(name="updateraid", description="Update or reschedule an active raid")
async def update_raid(interaction: Interaction):
    await interaction.response.defer(ephemeral=True)

    # Fetch all active raids
    rows = await db.fetchall(
        "SELECT raid_id, raid_name, channel_id, raid_type, start_timestamp, duration, tz "
        "FROM active_raids"
    )
    if not rows:
        return await interaction.followup.send("There are no active raids.", ephemeral=True)

    # Prompt user to select which raid to update
    selector_view = View(timeout=60)
    selector_view.add_item(RaidSelect(
        raids=[(r[0], r[1]) for r in rows],
        placeholder="Select raid to update…"
    ))
    await interaction.followup.send("Choose a raid to update:", view=selector_view, ephemeral=True)
    await selector_view.wait()

    raid_id = selector_view.children[0].selected_raid
    if raid_id is None:
        return  # user timed out or cancelled

    # Load selected raid's settings
    (_, raid_name, channel_id, raid_type, start_ts, duration, tz_code) = \
        next(r for r in rows if r[0] == raid_id)

    # Convert stored UTC timestamp into user's local time
    user_tz = pytz.timezone(TIMEZONE_MAPPING[tz_code])
    local_dt = datetime.fromtimestamp(start_ts, pytz.utc).astimezone(user_tz)

    # Prepare flow with existing values
    flow = CreateRaidFlow(raid_name=raid_name)
    flow.raid_type      = raid_type
    flow.duration       = duration
    flow.date           = local_dt.strftime("%Y-%m-%d")
    flow.tz             = tz_code
    flow.start_time_str = local_dt.strftime("%I:%M%p")

    # Display pre-filled update form
    update_view = UpdateRaidView(flow)
    await interaction.followup.send("**Update raid details**", view=update_view, ephemeral=True)
    await update_view.wait()
    if not update_view.submitted:
        return  # user closed without submitting

    # Parse new date/time into a UTC timestamp
    new_time = await validate_time_input(flow.start_time_str)
    new_date = datetime.strptime(flow.date, "%Y-%m-%d").date()
    combined = datetime.combine(new_date, new_time)
    localized = user_tz.localize(combined, is_dst=None)
    new_utc   = localized.astimezone(pytz.utc)
    new_start = int(new_utc.timestamp())
    new_ping  = new_start - 30 * 60  # thirty minutes before start

    # Attempt to fetch and edit the original sign-up post
    signup_post = await fetch_signup_post(channel_id, raid_id)
    if signup_post:
        ts_tag = f"<t:{new_start}:F>"
        new_content = RAID_TEMPLATES[flow.raid_type].format(
            name=raid_name,
            duration=flow.duration,
            timestamp=ts_tag,
            GUILD_MEMBER_PING=GUILD_MEMBER_PING
        )
        await edit_signup_post(signup_post, new_content, raid_id)

    # Persist updated schedule to the database
    await db.execute(
        "UPDATE active_raids "
        "SET start_timestamp = ?, ping_timestamp = ?, duration = ?, tz = ? "
        "WHERE raid_id = ?",
        (new_start, new_ping, flow.duration, flow.tz, raid_id)
    )

    # Cancel existing reminder and schedule a new one
    old = active_raids.pop(raid_id, None)
    if old and old.get("ping_task"):
        old["ping_task"].cancel()

    # Ensure we have a channel object for scheduling
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
            "channel_id": channel_id
        }
    else:
        # If the warning window has already passed, remove its record
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
    selector: RaidSelect = view.children[0]  # our single item
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
    logger.info(f"Sign-ups check by {interaction.user.display_name}")

    # Load active raids
    raids = await db.fetchall("""
        SELECT raid_id, raid_name, channel_id, raid_type
        FROM active_raids
        ORDER BY raid_id DESC
    """)
    if not raids:
        return await interaction.followup.send("There are no active raids.", ephemeral=True)

    # Show dropdown
    options = [(r_id, name) for r_id, name, _, _ in raids]
    view = View(timeout=30)
    view.add_item(RaidSelect(options, placeholder="Select raid to view sign-ups…"))
    await interaction.followup.send("Select a raid to view sign-ups:", view=view, ephemeral=True)
    await view.wait()

    selector: RaidSelect = view.children[0]
    raid_id = selector.selected_raid
    if raid_id is None:
        return

    # Extract chosen raid metadata
    _, raid_name, _, raid_type = next(r for r in raids if r[0] == raid_id)
    mapping = SIGNUP_MAPPINGS[raid_type]

    # Build sign-up cache
    cache = signups_cache.get(raid_id, {})
    guild = interaction.guild or await bot.fetch_guild(interaction.guild_id)

    # Per-role lists
    role_signups = {
        mapping["roles"][emoji]: cache.get(emoji, set())
        for emoji in mapping["roles"]
    }
    backup_ids = cache.get(mapping["backup"], set())
    all_ids = set().union(*role_signups.values(), backup_ids)

    # Assemble output
    lines: List[str] = [f"**{raid_name}**\n\n__**Roles**__"]
    for emoji in RAID_REACTIONS[raid_type]:
        if emoji in mapping["roles"]:
            role_desc = mapping["roles"][emoji]
            names = sorted(
                (
                    escape_markdown(member.display_name)
                    for uid in role_signups[role_desc]
                    if (member := guild.get_member(uid))
                ),
                key=str.lower
            )
            lines.append(f"{emoji} {role_desc}:** {', '.join(names) or 'None'}")

    lines.append("\n__**Backups**__")
    backup_names = sorted(
        (
            escape_markdown(member.display_name)
            for uid in backup_ids
            if (member := guild.get_member(uid))
        ),
        key=str.lower
    )
    lines.append(f"{mapping['backup']} {', '.join(backup_names) or 'None'}")
    lines.append(f"\n**Number of Sign-ups:** {len(all_ids)}")

    await interaction.followup.send("\n".join(lines), ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)