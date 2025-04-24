import discord
from discord import Interaction
from discord.ui import Select, View, Button, Modal, TextInput
from discord.ext import commands
from discord.utils import escape_markdown
import pytz
from datetime import datetime, timedelta
import re
import os
import asyncio
import logging
import aiosqlite
from typing import Dict, Set

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants and configuration
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_LEADER_ROLE_ID = 1064772891180290080
RAID_CAPTAIN_ROLE_ID = 1227986507260891216
GUILD_MEMBER_PING = f"<@&1058291622439292958>"

TIMEZONE_MAPPING = {
    "AT": "America/Anchorage",
    "PT": "America/Los_Angeles",
    "MT": "America/Denver",
    "CT": "America/Chicago",
    "ET": "America/New_York",
    "UTC": "UTC"
}

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

# Database manager using aiosqlite
class DBManager:
    EXPECTED_COLUMNS = {
        "raid_id": "INTEGER PRIMARY KEY",
        "raid_name": "TEXT",
        "channel_id": "INTEGER",
        "raid_type": "TEXT",
        "ping_timestamp": "INTEGER",
    }

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    async def initialize(self):
        self.conn = await aiosqlite.connect(self.db_path)
        
        # Create table with latest schema, one column per line with trailing commas
        cols = ",\n    ".join(f"{n} {d}" for n, d in self.EXPECTED_COLUMNS.items())
        await self.conn.execute(f"""
        CREATE TABLE IF NOT EXISTS active_raids (
            {cols}
        );
        """)
        
        # Check for missing columns
        cursor = await self.conn.execute("PRAGMA table_info(active_raids)")
        existing_columns = {row[1] for row in await cursor.fetchall()}
        
        # Add any missing columns
        for col_name, col_def in self.EXPECTED_COLUMNS.items():
            if col_name not in existing_columns:
                await self.conn.execute(f"""
                    ALTER TABLE active_raids 
                    ADD COLUMN {col_name} {col_def}
                """)
        await self.conn.commit()

    async def fetchall(self, query: str, params: tuple = ()):
        async with self.conn.execute(query, params) as cursor:
            return await cursor.fetchall()

    async def fetchone(self, query: str, params: tuple = ()):
        async with self.conn.execute(query, params) as cursor:
            return await cursor.fetchone()

    async def execute(self, query: str, params: tuple = ()):
        await self.conn.execute(query, params)
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None

db = DBManager("/data/active_raids.db")  # Database instance
active_raids = {}  # In-memory storage for active raids

# In-memory cache for reactions by message
signups_cache: Dict[int, Dict[str, Set[int]]] = {}

# Raid templates and reaction mapping
RAID_TEMPLATES = {
    "Cabal's Revenge Raid": """**{name}**

**Date & Time:** {timestamp}
**Duration:** {duration}

⭐  = Vanguard Team
🌞  = Outside Combat Team
🌕  = Mob Pulling/Cannon Team

🔴 **NORTH-WEST | RED BANNER** 🔴
⭐  Daemon Vanguard: **-yth/Fire/Storm 2** -- 1️⃣
🌞  OS Combat Team 1: **-yth 1 Oblongata** -- 2️⃣
🌕  West Cannon Mob Puller: **Any School Hitter** -- 3️⃣

🟢 **NORTH-EAST | GREEN BANNER** 🟢
⭐  Cabalist Vanguard: **Support 1 (No Zap/ No Monu)** -- 4️⃣
🌞  OS Combat Team 1: **-yth 2 Oblongata** -- 5️⃣
🌕  East Cannon Mob Puller: **Any School Hitter** -- 6️⃣

🔵 **SOUTH-WEST | BLUE BANNER** 🔵
⭐  Cabalist Vanguard: **Storm 2 (No Zap/No Monu)** -- 7️⃣
🌞  OS Combat Team 2: **Poison Oak 1** -- 8️⃣
🌕  West Cannon Shooter: **Any School** -- 9️⃣

🟣 **SOUTH-EAST | PURPLE BANNER** 🟣
⭐  Daemon Vanguard: **-yth /Support 1** -- 🇦
🌞  OS Combat Team 2: **Poison Oak 2** -- 🇧
🌕  West Cannon Shooter: **Any School** -- 🇨

↪️ **Backups:**

{GUILD_MEMBER_PING}

**Cabal's Revenge Raid Guide:**
https://docs.google.com/presentation/d/1ZrL9kliok42Qf_A7fHBUrIUpLKSSWFeYkNYXQGH0-ww/edit""",
    "Crying Sky Raid (Gatekeeper of the Apocalypse)": """**{name}**

**Date & Time:** {timestamp}
**Duration:** {duration}

Ixta & Autloc Team
<:global:1218332456348946543><:global:1218332456348946543> Support 1 -- 1️⃣
<:Balance:1059511860539433012><:Balance:1059511860539433012> Balance 2 -- 2️⃣
<:Storm:1059511770785534062><:Storm:1059511770785534062> Storm 3 -- 3️⃣
<:global:1218332456348946543><:Storm:1059511770785534062> Storm/Form/Morm 4 -- 4️⃣

Yetaxa Team
<:global:1218332456348946543><:Fire:1059511748199186482> Fire / Lire 1 -- 5️⃣
<:Fire:1059511748199186482><:Fire:1059511748199186482> Fire 2 -- 6️⃣
<:global:1218332456348946543><:Fire:1059511748199186482> Fire / Mire 3 -- 7️⃣
<:Fire:1059511748199186482><:Fire:1059511748199186482> Fire 4 -- 8️⃣

Cameca Team
<:Ice:1059511756256456734><:Myth:1059512670824439819> -yth 1 -- 🇦 (Preferably Ice)
<:Death:1059512679494066216><:Myth:1059512670824439819> -yth 2 -- 🇧 (Preferably Death)
<:global:1218332456348946543><:Myth:1059512670824439819> Fyth/Styth 3 -- 🇨
<:global:1218332456348946543><:Myth:1059512670824439819> Fyth/Styth 4 -- 🇩

↪️ **Backup:**

{GUILD_MEMBER_PING}

**Gatekeeper of the Apocalypse Guide:**
https://docs.google.com/presentation/d/1mI9ZRba7RDaV1Bl7VRiPw-9ojzPsuuPiTGX_iwPbgKA/edit""",
    "Crying Sky Raid": """**{name}**

**Date & Time:** {timestamp}
**Duration:** {duration}

Ixta & Autloc Team
<:global:1218332456348946543><:global:1218332456348946543> Support 1 -- 1️⃣
<:global:1218332456348946543><:global:1218332456348946543> Support 2  -- 2️⃣
<:Storm:1059511770785534062><:Storm:1059511770785534062> Storm 3 -- 3️⃣
<:global:1218332456348946543><:Storm:1059511770785534062> -orm 4 -- 4️⃣

Yetaxa Team
<:global:1218332456348946543><:Fire:1059511748199186482> Fire/Lire 1 -- 5️⃣
<:Fire:1059511748199186482><:Fire:1059511748199186482> Fire 2 -- 6️⃣
<:global:1218332456348946543><:Fire:1059511748199186482> -ire 3 -- 7️⃣
<:Fire:1059511748199186482><:Fire:1059511748199186482> Fire 4 -- 8️⃣

Cameca Team
<:global:1218332456348946543><:Myth:1059512670824439819> -yth 1 -- 🇦
<:global:1218332456348946543><:Myth:1059512670824439819> -yth 2 -- 🇧
<:global:1218332456348946543><:Myth:1059512670824439819> Fyth/Styth 3 -- 🇨
<:global:1218332456348946543><:Myth:1059512670824439819> Fyth/Styth 4 -- 🇩

↪️ **Backup:**

{GUILD_MEMBER_PING}

**Crying Sky Raid Guide:**
https://docs.google.com/presentation/d/1ehNKtXakwFsyHIe-JIOjAPwP4Juk5gZchjVKX9hhlBU/edit#slide=id.p""",
    "Voracious Void Raid": """**{name}**

**Date & Time:** {timestamp}
**Duration:** {duration}

**__Vanguard__**
1️⃣ **Fire/Myth 1**:
2️⃣ **Fire/Myth 2**:
3️⃣ **Storm**:
4️⃣ **Jade**:

**__Outside Combat__**
5️⃣ Ser or Brim/**Surge/Milli Supp**:
6️⃣ Ser or Brim/**Surge/Mob Pull**:
7️⃣ Ser or Brim/**Elf Jade/Milli Supp**:
8️⃣ Ser or Brim/**Elf Hitter/Milli Hitter** (off school hitter please):

**__Drums__**
🇦 **Close/Lead**:
🇧 **Mid**:
🇨 **Far**:
🇩 **Token/Mob Pull**:

↪️ **Backups**:

For fire/myth vanguard roles, please react with the school(s) you have available

{GUILD_MEMBER_PING}

**Voracious Void Raid Guides:**
https://docs.google.com/presentation/d/1Cv5XJbE5zLG2BRnKPZoSqSbQSesvfDyZyzJSvHBqY0I/edit#slide=id.g27c7916204b_0_0
https://docs.google.com/presentation/d/1bOqmLvcGoA2KAn2FHLOQMf2OC8mv4GA1YbwPWv72gNQ/edit#slide=id.p
https://docs.google.com/presentation/d/1GnesDgI4h6uo6GgG0WjJfT_LjRlPWKNBJVETPsFsGCg/edit"""
}

# Bot templates and reaction mappings
RAID_REACTIONS = {  
    "Cabal's Revenge Raid": ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🇦", "🇧", "🇨", "↪️"],
    "Crying Sky Raid (Gatekeeper of the Apocalypse)": ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "🇦", "🇧", "🇨", "🇩", "↪️", "<:Fire:1059511748199186482>", "<:Ice:1059511756256456734>", "<:Storm:1059511770785534062>", "<:Myth:1059512670824439819>", "<:Life:1059512659436900432>", "<:Death:1059512679494066216>", "<:Balance:1059511860539433012>"],
    "Crying Sky Raid": ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "🇦", "🇧", "🇨", "🇩", "↪️"],
    "Voracious Void Raid": ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "🇦", "🇧", "🇨", "🇩", "↪️", "<:Fire:1059511748199186482>", "<:Myth:1059512670824439819>"]
}

SIGNUP_MAPPINGS = {  
    "Cabal's Revenge Raid": {
        "roles": {
            "1️⃣": "Daemon Vanguard (-yth/Fire/Storm 2)",
            "2️⃣": "OS Combat Team 1 (-yth 1 Oblongata)",
            "3️⃣": "West Cannon Mob Puller (Any School Hitter)",
            "4️⃣": "Cabalist Vanguard (Support 1)",
            "5️⃣": "OS Combat Team 1 (-yth 2 Oblongata)",
            "6️⃣": "East Cannon Mob Puller (Any School Hitter)",
            "7️⃣": "Cabalist Vanguard (Storm 2)",
            "8️⃣": "OS Combat Team 2 (Poison Oak 1)",
            "9️⃣": "West Cannon Shooter (Any School)",
            "🇦": "Daemon Vanguard (-yth/Support 1)",
            "🇧": "OS Combat Team 2 (Poison Oak 2)",
            "🇨": "West Cannon Shooter (Any School)"
        },
        "backup": "↪️"
    },
    "Crying Sky Raid (Gatekeeper of the Apocalypse)": {
        "roles": {
            "1️⃣": "Ixta & Autloc Team: Support 1",
            "2️⃣": "Ixta & Autloc Team: Balance 2",
            "3️⃣": "Ixta & Autloc Team: Storm 3",
            "4️⃣": "Ixta & Autloc Team: Storm/Form/Morm 4",
            "5️⃣": "Yetaxa Team: Fire / Lire 1",
            "6️⃣": "Yetaxa Team: Fire 2",
            "7️⃣": "Yetaxa Team: Fire / Mire 3",
            "8️⃣": "Yetaxa Team: Fire 4",
            "🇦": "Cameca Team: -yth 1 (Preferably Ice)",
            "🇧": "Cameca Team: -yth 2 (Preferably Death)",
            "🇨": "Cameca Team: Fyth/Styth 3",
            "🇩": "Cameca Team: Fyth/Styth 4"
        },
        "backup": "↪️"
    },
    "Crying Sky Raid": {
        "roles": {
            "1️⃣": "Ixta & Autloc Team: Support 1",
            "2️⃣": "Ixta & Autloc Team: Support 2",
            "3️⃣": "Ixta & Autloc Team: Storm 3",
            "4️⃣": "Ixta & Autloc Team: -orm 4",
            "5️⃣": "Yetaxa Team: Fire/Lire 1",
            "6️⃣": "Yetaxa Team: Fire 2",
            "7️⃣": "Yetaxa Team: -ire 3",
            "8️⃣": "Yetaxa Team: Fire 4",
            "🇦": "Cameca Team: -yth 1",
            "🇧": "Cameca Team: -yth 2",
            "🇨": "Cameca Team: Fyth/Styth 3",
            "🇩": "Cameca Team: Fyth/Styth 4"
        },
        "backup": "↪️"
    },
    "Voracious Void Raid": {
        "roles": {
            "1️⃣": "Vanguard: Fire/Myth 1",
            "2️⃣": "Vanguard: Fire/Myth 2",
            "3️⃣": "Vanguard: Storm",
            "4️⃣": "Vanguard: Jade",
            "5️⃣": "Outside Combat: Ser or Brim/Surge/Milli Supp",
            "6️⃣": "Outside Combat: Ser or Brim/Surge/Mob Pull",
            "7️⃣": "Outside Combat: Ser or Brim/Elf Jade/Milli Supp",
            "8️⃣": "Outside Combat: Ser or Brim/Elf Hitter/Milli Hitter",
            "🇦": "Drums: Close/Lead",
            "🇧": "Drums: Mid",
            "🇨": "Drums: Far",
            "🇩": "Drums: Token/Mob Pull"
        },
        "backup": "↪️"
    }
}

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
                f"{GUILD_MEMBER_PING} Raid starts in 30 minutes! Please join the raid VC, "
                "head to the guild house, and submit your deck to your team lead."
            )

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

# Time input validation function
async def validate_time_input(time_str: str) -> datetime.time:
    s = time_str.upper().replace(" ", "")
    for regex, formatter in _TIME_PATTERNS:
        m = regex.fullmatch(s)
        if not m:
            continue
        formatted = formatter(m.groups())
        try:
            if formatted[-2:].upper() in ("AM","PM"):
                return datetime.strptime(formatted, "%I:%M%p").time()
            return datetime.strptime(formatted, "%H:%M").time()
        except ValueError:
            continue
    raise ValueError("Invalid time format, please try again.")

@bot.event
async def on_raw_reaction_add(payload):
    # Look up raid in memory
    raid_info = active_raids.get(payload.message_id)
    if not raid_info:
        return

    guild = bot.get_guild(payload.guild_id) or await bot.fetch_guild(payload.guild_id)
    member = payload.member or guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)
    if member.bot:
        return

    emoji = str(payload.emoji)

    # Pull raid_type from memory
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

@bot.event
async def on_raw_reaction_remove(payload):
    # keep cache in-sync on un‑react
    if payload.message_id in active_raids:
        cache = signups_cache.get(payload.message_id, {})
        # Discard by user_id
        cache.get(str(payload.emoji), set()).discard(payload.user_id)

class CreateRaidFlow:
    def __init__(self, raid_name: str = None):
        self.raid_name: str = raid_name
        self.start_time_str: str = None
        self.raid_type: str = None
        self.duration: str = None
        self.date: str = None
        self.tz: str = None

class TimeModal(Modal, title="Enter Raid Time"):
    def __init__(self, flow: CreateRaidFlow):
        super().__init__()
        self.flow = flow
        self.start_time = TextInput(
            label="Start Time",
            placeholder="Use format 6:30PM or 18:30"
        )
        self.add_item(self.start_time)

    async def on_submit(self, interaction: Interaction):
        self.flow.start_time_str = self.start_time.value
        await interaction.response.defer()
        self.stop()

class TimeButton(Button):
    def __init__(self, row: int):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="Enter Time & Create",
            row=row,
            disabled=True
        )

    async def callback(self, interaction: Interaction):
        # Final validation before proceeding
        if not self.view.all_required_filled():
            await interaction.response.send_message(
                "Please complete all dropdown selections first.",
                ephemeral=True
            )
            return

        # Open time entry modal
        modal = TimeModal(self.view.flow)
        await interaction.response.send_modal(modal)
        await modal.wait()

        try:
            # Validate time input
            time_obj = await validate_time_input(self.view.flow.start_time_str)
            date_obj = datetime.strptime(self.view.flow.date, "%Y-%m-%d").date()
            naive_dt = datetime.combine(date_obj, time_obj)
            
            # Convert to UTC
            user_tz = pytz.timezone(TIMEZONE_MAPPING[self.view.flow.tz])
            localized_dt = user_tz.localize(naive_dt, is_dst=None)
            utc_dt = localized_dt.astimezone(pytz.utc)

            if utc_dt <= datetime.now(pytz.utc):
                return await interaction.followup.send("Cannot schedule a raid in the past!",ephemeral=True)

            # Create raid name if not provided
            raid_name = self.view.flow.raid_name

            # Post raid announcement
            template = RAID_TEMPLATES[self.view.flow.raid_type]
            ts = f"<t:{int(utc_dt.timestamp())}:F>"
            post = await interaction.channel.send(
                template.format(
                    name=raid_name,
                    duration=self.view.flow.duration,
                    timestamp=ts,
                    GUILD_MEMBER_PING=GUILD_MEMBER_PING
                )
            )

            # Schedule reminder ping
            ping_time = utc_dt - timedelta(minutes=30)
            delay = (ping_time - datetime.now(pytz.utc)).total_seconds()
            
            if delay > 0:
                task = asyncio.create_task(
                    bot.schedule_ping(delay, interaction.channel, post.id)
                )
                active_raids[post.id] = {
                    "ping_task": task,
                    "name": raid_name,
                    "raid_type": self.view.flow.raid_type,
                    "channel_id": interaction.channel.id
                }
                await db.execute(
                    "INSERT INTO active_raids (raid_id, raid_name, channel_id, raid_type, ping_timestamp) VALUES (?, ?, ?, ?, ?)",
                    (post.id, raid_name, interaction.channel.id, self.view.flow.raid_type, int(ping_time.timestamp()))
                )

            # Disable view after successful raid creation
            await interaction.edit_original_response(view=None)
            self.view.stop()

            # Add reactions concurrently
            tasks = [post.add_reaction(emoji) for emoji in RAID_REACTIONS[self.view.flow.raid_type]]
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Raid creation error: {e}", exc_info=True)
            await interaction.followup.send(str(e), ephemeral=True)

class CreateRaidView(View):
    def __init__(self, flow: CreateRaidFlow):
        super().__init__(timeout=300)
        self.flow = flow
        
        # Add dropdown components
        self.add_item(RaidTypeSelect(row=0))
        self.add_item(DurationSelect(row=1))
        self.add_item(DateSelect(row=2))
        self.add_item(TimezoneSelect(row=3))
        
        # Add time button (initially disabled)
        self.time_button = TimeButton(row=4)
        self.add_item(self.time_button)

    def all_required_filled(self):
        return all([
            self.flow.raid_type,
            self.flow.duration,
            self.flow.date,
            self.flow.tz
        ])

    async def update_view(self, interaction: Interaction):
        """Update button state and refresh view"""
        self.time_button.disabled = not self.all_required_filled()
        await interaction.response.edit_message(view=self)

class RaidTypeSelect(Select):
    def __init__(self, row: int):
        options = [
            discord.SelectOption(label=name, value=name)
            for name in RAID_TEMPLATES
        ]
        super().__init__(placeholder="Select Raid Type…", row=row, options=options)

    async def callback(self, interaction: Interaction):
        choice = self.values[0]
        self.view.flow.raid_type = choice

        # mark the chosen option
        for opt in self.options:
            opt.default = (opt.value == choice)

        # enable/disable the Time button
        self.view.time_button.disabled = not self.view.all_required_filled()

        # re‑send the updated view so the selection sticks
        await interaction.response.edit_message(view=self.view)

class DurationSelect(Select):
    def __init__(self, row: int):
        durations = ["3 hours", "1.5 hours"]
        options = [
            discord.SelectOption(label=d, value=d)
            for d in durations
        ]
        super().__init__(placeholder="Select Duration…", row=row, options=options)

    async def callback(self, interaction: Interaction):
        choice = self.values[0]
        self.view.flow.duration = choice

        for opt in self.options:
            opt.default = (opt.value == choice)

        self.view.time_button.disabled = not self.view.all_required_filled()
        await interaction.response.edit_message(view=self.view)

class DateSelect(Select):
    def __init__(self, row: int):
        today = datetime.now()
        options = []
        for i in range(14):
            day = today + timedelta(days=i)
            label = day.strftime("%A, %B %d")
            value = day.strftime("%Y-%m-%d")
            options.append(discord.SelectOption(label=label, value=value))
        super().__init__(placeholder="Select Date…", row=row, options=options)

    async def callback(self, interaction: Interaction):
        choice = self.values[0]
        self.view.flow.date = choice

        for opt in self.options:
            opt.default = (opt.value == choice)

        self.view.time_button.disabled = not self.view.all_required_filled()
        await interaction.response.edit_message(view=self.view)

class TimezoneSelect(Select):
    def __init__(self, row: int):
        now_utc = datetime.now(pytz.utc)
        options = []
        for code, zone in TIMEZONE_MAPPING.items():
            if zone == "UTC":
                abbr = "UTC"
            else:
                tz = pytz.timezone(zone)
                local = now_utc.astimezone(tz)
                is_dst = bool(local.dst() and local.dst() != timedelta(0))
                abbr = {
                    "PT": "PDT" if is_dst else "PST",
                    "MT": "MDT" if is_dst else "MST",
                    "CT": "CDT" if is_dst else "CST",
                    "ET": "EDT" if is_dst else "EST",
                    "AT": "AKDT" if is_dst else "AKST",
                }[code]
            options.append(discord.SelectOption(label=abbr, value=code))
        super().__init__(placeholder="Select Timezone…", row=row, options=options)

    async def callback(self, interaction: Interaction):
        choice = self.values[0]
        self.view.flow.tz = choice

        for opt in self.options:
            opt.default = (opt.value == choice)

        self.view.time_button.disabled = not self.view.all_required_filled()
        await interaction.response.edit_message(view=self.view)

# /createraid command
@bot.tree.command(name="createraid", description="Create a new raid")
async def create_raid(
    interaction: Interaction,
    raid_name: str
):
    # Permission check
    if not any(r.id in (GUILD_LEADER_ROLE_ID, RAID_CAPTAIN_ROLE_ID) 
               for r in interaction.user.roles):
        return await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True
        )

    # Initialize creation flow
    flow = CreateRaidFlow(raid_name=raid_name)
    view = CreateRaidView(flow)

    # Send initial configuration message
    await interaction.response.send_message(
        "**Raid Configuration**\n",
        view=view,
        ephemeral=True
    )

# /cancelraid command
@bot.tree.command(name="cancelraid", description="Cancel an active raid")
async def cancel_raid(interaction: discord.Interaction):
    if not any(role.id in [GUILD_LEADER_ROLE_ID, RAID_CAPTAIN_ROLE_ID] for role in interaction.user.roles):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)

    raids = await db.fetchall("""
        SELECT raid_id, raid_name
        FROM active_raids
        ORDER BY raid_id DESC
    """)
    if not raids:
        await interaction.followup.send("There are no active raids.", ephemeral=True)
        return

    class CancelSelect(Select):
        def __init__(self):
            options = [
                discord.SelectOption(label=name, value=str(r_id))
                for r_id, name in raids
        ]
            super().__init__(placeholder="Select raid to cancel...", options=options)
        async def callback(self, interaction: discord.Interaction):
            self.view.selected_raid = int(self.values[0])
            await interaction.response.defer()
            await interaction.edit_original_response(view=None)
            self.view.stop()

    view = View(timeout=60)
    view.add_item(CancelSelect())
    view.selected_raid = None
    await interaction.followup.send("Select a raid to cancel:", view=view, ephemeral=True)
    await view.wait()
    if not view.selected_raid:
        return

    raid_id = view.selected_raid
    result = await db.fetchone("SELECT channel_id FROM active_raids WHERE raid_id = ?", (raid_id,))
    channel_id = int(result[0]) if result else None

    try:
        # Cancel scheduled ping task if present
        raid_info = active_raids.get(raid_id)
        if raid_info and raid_info.get("ping_task"):
            raid_info["ping_task"].cancel()

        # Remove from our in-memory caches
        signups_cache.pop(raid_id, None)
        active_raids.pop(raid_id, None)

        # Delete from database
        await db.execute("DELETE FROM active_raids WHERE raid_id = ?", (raid_id,))

        # Delete the original message
        if channel_id:
            channel = bot.get_channel(channel_id)
            if channel:
                try:
                    msg = await channel.fetch_message(raid_id)
                    await msg.delete()
                except discord.NotFound:
                    logger.warning(f"Message {raid_id} already deleted")
                except Exception as e:
                    logger.error(f"Error deleting message: {e}")

        await interaction.followup.send("Raid successfully canceled.", ephemeral=True)
    except Exception as e:
        logger.error(f"Error cancelling raid: {e}")
        await interaction.followup.send("Failed to cancel raid.", ephemeral=True)

# /showsignups command
@bot.tree.command(name="showsignups", description="Show sign-ups for an active raid")
async def showsignups(interaction: discord.Interaction):
    if not any(role.id in [GUILD_LEADER_ROLE_ID, RAID_CAPTAIN_ROLE_ID]
               for role in interaction.user.roles):
        await interaction.response.send_message(
            "You do not have permission to use this command.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    logger.info(f"Signups check by {interaction.user.display_name}")

    try:
        # Load active raids
        raids = await db.fetchall("""
            SELECT raid_id, raid_name, channel_id, raid_type
            FROM active_raids
            ORDER BY raid_id DESC
        """)
        if not raids:
            await interaction.followup.send("No active raids", ephemeral=True)
            return

        # Raid selection
        class RaidSelect(Select):
            def __init__(self):
                options = [
                    discord.SelectOption(label=name, value=str(r_id))
                    for r_id, name, _, _ in raids
                ]
                super().__init__(
                    placeholder="Select raid to view sign-ups...",
                    options=options
                )

            async def callback(self, interaction: discord.Interaction):
                self.view.selected_raid = int(self.values[0])
                await interaction.response.defer(ephemeral=True)
                await interaction.edit_original_response(view=None)
                self.view.stop()

        view = View(timeout=30)
        view.add_item(RaidSelect())
        await interaction.followup.send(
            "Select a raid to view sign-ups:",
            view=view,
            ephemeral=True
        )
        await view.wait()
        if not getattr(view, "selected_raid", None):
            return

        # Extract raid details
        raid_id, raid_name, _,raid_type = next(
            r for r in raids if r[0] == view.selected_raid
        )
        mapping = SIGNUP_MAPPINGS[raid_type]

        # Build cache and localize guild
        cache = signups_cache.get(raid_id, {})
        guild = interaction.guild or await bot.fetch_guild(interaction.guild_id)

        # Build per-role lists
        role_signups = {
            role_desc: cache.get(emoji, set())
            for emoji, role_desc in mapping["roles"].items()
        }

        # Backups (IDs)
        backup_ids = cache.get(mapping["backup"], set())

        # Unique Sign‑ups
        all_ids = set().union(*role_signups.values(), backup_ids)

        # Format output, resolving IDs → display_name
        output = [f"**{raid_name}**\n\n__**Roles**__"]
        for emoji in RAID_REACTIONS[raid_type]:
            if emoji in mapping["roles"]:
                role = mapping["roles"][emoji]
                names = sorted(
                    [
                        escape_markdown(member.display_name)
                        for uid in role_signups.get(role, ())
                        if (member := guild.get_member(uid)) is not None
                    ],
                    key=str.lower
                )
                output.append(f"{emoji} {role}: {', '.join(names) or 'None'}")

        output.append("\n__**Backups**__")
        backup_names = sorted(
            [
                escape_markdown(member.display_name)
                for uid in backup_ids
                if (member := guild.get_member(uid)) is not None
            ],
            key=str.lower
        )
        output.append(f"{mapping['backup']} {', '.join(backup_names) or 'None'}")
        output.append(f"\n**Number of Sign‑ups:** {len(all_ids)}")

        await interaction.followup.send("\n".join(output), ephemeral=True)

    except Exception as e:
        logger.error("Sign‑ups error:", exc_info=True)
        await interaction.followup.send(
            "Error generating sign‑ups list",
            ephemeral=True
        )

if __name__ == "__main__":
    bot.run(TOKEN)