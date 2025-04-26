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
⭐  Cabalist Vanguard: **Support 1 (No Zap/No Monu)** -- 4️⃣
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

**Ixta & Autloc Team**
<:global:1218332456348946543><:global:1218332456348946543> Support 1 -- 1️⃣
<:Balance:1059511860539433012><:Balance:1059511860539433012> Balance 2 -- 2️⃣
<:Storm:1059511770785534062><:Storm:1059511770785534062> Storm 3 -- 3️⃣
<:global:1218332456348946543><:Storm:1059511770785534062> Storm/Form/Morm 4 -- 4️⃣

**Yetaxa Team**
<:global:1218332456348946543><:Fire:1059511748199186482> Fire / Lire 1 -- 5️⃣
<:Fire:1059511748199186482><:Fire:1059511748199186482> Fire 2 -- 6️⃣
<:global:1218332456348946543><:Fire:1059511748199186482> Fire / Mire 3 -- 7️⃣
<:Fire:1059511748199186482><:Fire:1059511748199186482> Fire 4 -- 8️⃣

**Cameca Team**
<:Ice:1059511756256456734><:Myth:1059512670824439819> -yth 1 -- 🇦 (Preferably Ice)
<:Death:1059512679494066216><:Myth:1059512670824439819> -yth 2 -- 🇧 (Preferably Death)
<:global:1218332456348946543><:Myth:1059512670824439819> Fyth/Styth 3 -- 🇨
<:global:1218332456348946543><:Myth:1059512670824439819> Fyth/Styth 4 -- 🇩

↪️ **Backups:**

{GUILD_MEMBER_PING}

**Gatekeeper of the Apocalypse Guide:**
https://docs.google.com/presentation/d/1mI9ZRba7RDaV1Bl7VRiPw-9ojzPsuuPiTGX_iwPbgKA/edit""",

    "Crying Sky Raid": """**{name}**

**Date & Time:** {timestamp}
**Duration:** {duration}

**Ixta & Autloc Team**
<:global:1218332456348946543><:global:1218332456348946543> Support 1 -- 1️⃣
<:global:1218332456348946543><:global:1218332456348946543> Support 2  -- 2️⃣
<:Storm:1059511770785534062><:Storm:1059511770785534062> Storm 3 -- 3️⃣
<:global:1218332456348946543><:Storm:1059511770785534062> -orm 4 -- 4️⃣

**Yetaxa Team**
<:global:1218332456348946543><:Fire:1059511748199186482> Fire/Lire 1 -- 5️⃣
<:Fire:1059511748199186482><:Fire:1059511748199186482> Fire 2 -- 6️⃣
<:global:1218332456348946543><:Fire:1059511748199186482> -ire 3 -- 7️⃣
<:Fire:1059511748199186482><:Fire:1059511748199186482> Fire 4 -- 8️⃣

**Cameca Team**
<:global:1218332456348946543><:Myth:1059512670824439819> -yth 1 -- 🇦
<:global:1218332456348946543><:Myth:1059512670824439819> -yth 2 -- 🇧
<:global:1218332456348946543><:Myth:1059512670824439819> Fyth/Styth 3 -- 🇨
<:global:1218332456348946543><:Myth:1059512670824439819> Fyth/Styth 4 -- 🇩

↪️ **Backups:**

{GUILD_MEMBER_PING}

**Crying Sky Raid Guide:**
https://docs.google.com/presentation/d/1ehNKtXakwFsyHIe-JIOjAPwP4Juk5gZchjVKX9hhlBU/edit#slide=id.p""",

    "Voracious Void Raid": """**{name}**

**Date & Time:** {timestamp}
**Duration:** {duration}

**__Vanguard__**
1️⃣ **Fire/Storm/Myth 1:**
2️⃣ **Fire/Storm/Myth 2:**
3️⃣ **Storm 3:**
4️⃣ **Jade:**

**__Outside Combat__**
5️⃣ **Surge/Milli Supp:**
6️⃣ **Surge/Mob Pull:**
7️⃣ **Elf Jade/Milli Supp:**
8️⃣ **Elf Hitter/Milli Hitter (Off School Hitter):**

**__Drums__**
🇦 **Close/Lead:**
🇧 **Mid:**
🇨 **Far:**
🇩 **Token/Mob Pull:**

↪️ **Backups:**

For fire/storm/myth vanguard roles, please react with the school(s) you have available

{GUILD_MEMBER_PING}

**Voracious Void Raid Guides:**
https://docs.google.com/presentation/d/1bOqmLvcGoA2KAn2FHLOQMf2OC8mv4GA1YbwPWv72gNQ/edit#slide=id.p
https://docs.google.com/presentation/d/1Cv5XJbE5zLG2BRnKPZoSqSbQSesvfDyZyzJSvHBqY0I/edit#slide=id.g27c7916204b_0_0
https://docs.google.com/presentation/d/12wEhwmgSJHe_0sWQ0hG6mEorJ_X0T65j-cLuJkgHgfY/mobilepresent?slide=id.g2f3e5f33c2b_1_0
https://docs.google.com/presentation/d/1GnesDgI4h6uo6GgG0WjJfT_LjRlPWKNBJVETPsFsGCg/edit"""
}

# Bot templates and reaction mappings
RAID_REACTIONS = {  
    "Cabal's Revenge Raid": ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🇦", "🇧", "🇨", "↪️"],
    "Crying Sky Raid (Gatekeeper of the Apocalypse)": ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "🇦", "🇧", "🇨", "🇩", "↪️", "<:Fire:1059511748199186482>", "<:Ice:1059511756256456734>", "<:Storm:1059511770785534062>", "<:Myth:1059512670824439819>", "<:Life:1059512659436900432>", "<:Death:1059512679494066216>", "<:Balance:1059511860539433012>"],
    "Crying Sky Raid": ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "🇦", "🇧", "🇨", "🇩", "↪️"],
    "Voracious Void Raid": ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "🇦", "🇧", "🇨", "🇩", "↪️", "<:Fire:1059511748199186482>", "<:Storm:1059511770785534062>", "<:Myth:1059512670824439819>"]
}

SIGNUP_MAPPINGS = {  
    "Cabal's Revenge Raid": {
        "roles": {
            "1️⃣": "**Daemon Vanguard: -yth/Fire/Storm 2",
            "2️⃣": "**OS Combat Team 1: -yth 1 Oblongata",
            "3️⃣": "**West Cannon Mob Puller: Any School Hitter",
            "4️⃣": "**Cabalist Vanguard: Support 1",
            "5️⃣": "**OS Combat Team 1: -yth 2 Oblongata",
            "6️⃣": "**East Cannon Mob Puller: Any School Hitter",
            "7️⃣": "**Cabalist Vanguard: Storm 2",
            "8️⃣": "**OS Combat Team 2: Poison Oak 1",
            "9️⃣": "**West Cannon Shooter: Any School",
            "🇦": "**Daemon Vanguard: -yth/Support 1",
            "🇧": "**OS Combat Team 2: Poison Oak 2",
            "🇨": "**West Cannon Shooter: Any School"
        },
        "backup": "↪️"
    },
    "Crying Sky Raid (Gatekeeper of the Apocalypse)": {
        "roles": {
            "1️⃣": "**Ixta & Autloc Team: Support 1",
            "2️⃣": "**Ixta & Autloc Team: Balance 2",
            "3️⃣": "**Ixta & Autloc Team: Storm 3",
            "4️⃣": "**Ixta & Autloc Team: Storm/Form/Morm 4",
            "5️⃣": "**Yetaxa Team: Fire/Lire 1",
            "6️⃣": "**Yetaxa Team: Fire 2",
            "7️⃣": "**Yetaxa Team: Fire/Mire 3",
            "8️⃣": "**Yetaxa Team: Fire 4",
            "🇦": "**Cameca Team:** -yth 1 (Preferably Ice)",
            "🇧": "**Cameca Team:** -yth 2 (Preferably Death)",
            "🇨": "**Cameca Team:** Fyth/Styth 3",
            "🇩": "**Cameca Team:** Fyth/Styth 4"
        },
        "backup": "↪️"
    },
    "Crying Sky Raid": {
        "roles": {
            "1️⃣": "**Ixta & Autloc Team: Support 1",
            "2️⃣": "**Ixta & Autloc Team: Support 2",
            "3️⃣": "**Ixta & Autloc Team: Storm 3",
            "4️⃣": "**Ixta & Autloc Team: -orm 4",
            "5️⃣": "**Yetaxa Team: Fire/Lire 1",
            "6️⃣": "**Yetaxa Team: Fire 2",
            "7️⃣": "**Yetaxa Team: -ire 3",
            "8️⃣": "**Yetaxa Team: Fire 4",
            "🇦": "**Cameca Team: -yth 1",
            "🇧": "**Cameca Team: -yth 2",
            "🇨": "**Cameca Team: Fyth/Styth 3",
            "🇩": "**Cameca Team: Fyth/Styth 4"
        },
        "backup": "↪️"
    },
    "Voracious Void Raid": {
        "roles": {
            "1️⃣": "**Vanguard: Fire/Storm/Myth 1",
            "2️⃣": "**Vanguard: Fire/Storm/Myth 2",
            "3️⃣": "**Vanguard: Storm 3",
            "4️⃣": "**Vanguard: Jade",
            "5️⃣": "**Outside Combat: Ser or Brim/Surge/Milli Supp",
            "6️⃣": "**Outside Combat: Ser or Brim/Surge/Mob Pull",
            "7️⃣": "**Outside Combat: Ser or Brim/Elf Jade/Milli Supp",
            "8️⃣": "**Outside Combat: Ser or Brim/Elf Hitter/Milli Hitter",
            "🇦": "**Drums: Close/Lead",
            "🇧": "**Drums: Mid",
            "🇨": "**Drums: Far",
            "🇩": "**Drums: Token/Mob Pull"
        },
        "backup": "↪️"
    }
}