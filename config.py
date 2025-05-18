GUILD_LEADER_ROLE_ID = 1064772891180290080
RAID_CAPTAIN_ROLE_ID = 1227986507260891216
GUILD_MEMBER_PING = f"<@&1058291622439292958>"
TEST_CHANNEL_ID = 1366161275297464410

TIMEZONE_MAPPING = {
    "AT": "America/Anchorage",
    "PT": "America/Los_Angeles",
    "MT": "America/Denver",
    "CT": "America/Chicago",
    "ET": "America/New_York",
    "UTC": "UTC"
}

RAID_TEMPLATES = {
    "Cabal's Revenge": """**{name}**

**Date & Time:** {timestamp}
**Duration:** {duration}

❤️ **NORTHWEST | RED BANNER** ❤️
❄️ **Personal Daemon -yth/Fire/Storm 2:** 1️⃣
🧠 **Oblongata -yth 1:** 2️⃣
<:lightblueneonheart:1110338103496933497> **West Cannon Mob Puller:** 3️⃣

💚 **NORTHEAST | GREEN BANNER** 💚
❄️ **Divine Cabalist Support 1 (Taweret/Anubis):** 4️⃣
🧠 **Oblongata -yth 2:** 5️⃣
<:lightblueneonheart:1110338103496933497> **East Cannon Mob Puller:** 6️⃣

💙 **SOUTHWEST | BLUE BANNER** 💙
❄️ **Divine Cabalist Storm 2:** 7️⃣
☃️ **Poison Oak 1:** 8️⃣
<:lightblueneonheart:1110338103496933497> **West Cannon Shooter 1:** 9️⃣

💜 **SOUTHEAST | PURPLE BANNER** 💜
❄️ **Personal Daemon -yth/Support 1:** 🇦
☃️ **Poison Oak 2:** 🇧
<:lightblueneonheart:1110338103496933497> **West Cannon Shooter 2:** 🇨

↪️ **Backups:**

{GUILD_MEMBER_PING}

**Cabal's Revenge Raid Guide:**
https://docs.google.com/presentation/d/1ZrL9kliok42Qf_A7fHBUrIUpLKSSWFeYkNYXQGH0-ww/edit""",

    "Crying Sky (Gatekeeper of the Apocalypse)": """**{name}**

**Date & Time:** {timestamp}
**Duration:** {duration}

⛈️ **IXTA & AUTLOC TEAM** ⏳
<:global:1218332456348946543><:global:1218332456348946543> **Support 1:** 1️⃣
<:Balance:1059511860539433012><:Balance:1059511860539433012> **Balance 2:** 2️⃣
<:Storm:1059511770785534062><:Storm:1059511770785534062> **Storm 3** 3️⃣
<:global:1218332456348946543><:Storm:1059511770785534062> **Storm/Form/Morm 4:** 4️⃣

🔥 **YETAXA TEAM** 🔥
<:global:1218332456348946543><:Fire:1059511748199186482> **Fire/Lire 1:** 5️⃣
<:Fire:1059511748199186482><:Fire:1059511748199186482> **Fire 2:**6️⃣
<:global:1218332456348946543><:Fire:1059511748199186482> **Fire/Mire 3:** 7️⃣
<:Fire:1059511748199186482><:Fire:1059511748199186482> **Fire 4:** 8️⃣

🧊 **CAMECA TEAM** 🧊
<:Ice:1059511756256456734><:Myth:1059512670824439819> **-yth 1 (Preferably Ice):** 🇦
<:Death:1059512679494066216><:Myth:1059512670824439819> **-yth 2 (Preferably Death):** 🇧 
<:global:1218332456348946543><:Myth:1059512670824439819> **Fyth/Styth 3:** 🇨
<:global:1218332456348946543><:Myth:1059512670824439819> **Fyth/Styth 4:** 🇩

↪️ **Backups:**

{GUILD_MEMBER_PING}

**Gatekeeper of the Apocalypse Guide:**
https://docs.google.com/presentation/d/1mI9ZRba7RDaV1Bl7VRiPw-9ojzPsuuPiTGX_iwPbgKA/edit""",

    "Crying Sky": """**{name}**

**Date & Time:** {timestamp}
**Duration:** {duration}

⛈️ **IXTA & AUTLOC TEAM** ⏳
<:global:1218332456348946543><:global:1218332456348946543> **Support 1:** 1️⃣
<:global:1218332456348946543><:global:1218332456348946543> **Support 2:** 2️⃣
<:Storm:1059511770785534062><:Storm:1059511770785534062> **Storm 3:** 3️⃣
<:global:1218332456348946543><:Storm:1059511770785534062> **Storm/Form/Morm 4:** 4️⃣

🔥 **YETAXA TEAM** 🔥
<:global:1218332456348946543><:Fire:1059511748199186482> **Fire/Lire 1:** 5️⃣
<:Fire:1059511748199186482><:Fire:1059511748199186482> **Fire 2:** 6️⃣
<:global:1218332456348946543><:Fire:1059511748199186482> **-ire 3:** 7️⃣
<:Fire:1059511748199186482><:Fire:1059511748199186482> **Fire 4:** 8️⃣

🧊 **CAMECA TEAM** 🧊
<:global:1218332456348946543><:Myth:1059512670824439819> **-yth 1:** 🇦
<:global:1218332456348946543><:Myth:1059512670824439819> **-yth 2:** 🇧
<:global:1218332456348946543><:Myth:1059512670824439819> **Fyth/Styth 3:** 🇨
<:global:1218332456348946543><:Myth:1059512670824439819> **Fyth/Styth 4:** 🇩

↪️ **Backups:**

{GUILD_MEMBER_PING}

**Crying Sky Raid Guide:**
https://docs.google.com/presentation/d/1ehNKtXakwFsyHIe-JIOjAPwP4Juk5gZchjVKX9hhlBU/edit#slide=id.p""",

    "Voracious Void": """**{name}**

**Date & Time:** {timestamp}
**Duration:** {duration}

💫  **VANGUARD** 💫
<:orangestar:1366184421283336272> **Fire/Myth/Storm 1:** 1️⃣
<:pinkstar:1366184847663693974> **Fire/Myth/Storm 2:** 2️⃣
<:purplestar:1366182697235513436> **Storm 3:** 3️⃣
<:greenstar:1366184888268492881> **Jade:** 4️⃣

☄️ **OUTSIDE COMBAT** ☄️
🧡 **Surge/Milli Support:** 5️⃣
🩷 **Surge/Mob Pull:** 6️⃣
💜 **Elf/Milli Support:** 7️⃣
💚 **Off-School Elf/Milli Hitter:** 8️⃣

🎶 **DRUMS & PET TOKEN** 🎶
<:orangegem:1366197104296591530> **Close/Lead:** 🇦
<:pinkgem:1366197146616860764> **Mid:** 🇧
<:purplegem:1366197183778656327> **Far:** 🇨
<:greengem:1366197071526367404> **Pet Token/Mob Pull:** 🇩

↪️ **Backups:**

{GUILD_MEMBER_PING}

**Voracious Void Raid Guides:**
https://docs.google.com/presentation/d/1bOqmLvcGoA2KAn2FHLOQMf2OC8mv4GA1YbwPWv72gNQ/edit#slide=id.p
https://docs.google.com/presentation/d/1Cv5XJbE5zLG2BRnKPZoSqSbQSesvfDyZyzJSvHBqY0I/edit#slide=id.g27c7916204b_0_0
https://docs.google.com/presentation/d/12wEhwmgSJHe_0sWQ0hG6mEorJ_X0T65j-cLuJkgHgfY/edit?slide=id.p#slide=id.p
https://docs.google.com/presentation/d/1GnesDgI4h6uo6GgG0WjJfT_LjRlPWKNBJVETPsFsGCg/edit""",

    "Poison Oak Only": """**{name}**

**Date & Time:** {timestamp}
**Duration:** {duration}

❤️ **NORTHWEST | RED BANNER** ❤️
🌟 **Poison Oak Support 1 (Must have a Storm Attenuate):** 1️⃣
☀️ **Ice Tree Support:** 2️⃣
🌛 **Ice Tree Hitter:** 3️⃣

💚 **NORTHEAST | GREEN BANNER** 💚
🌟 **Poison Oak Support 2:** 4️⃣
☀️ **Death Tree Support:** 5️⃣
🌛 **Death Tree Hitter:** 6️⃣

💙 **SOUTHWEST | BLUE BANNER** 💙
🌟 **Poison Oak Support 3 (Preferably Storm/Life/Death):** 7️⃣
☀️ **Fire Tree Support:** 8️⃣
🌛 **Fire Tree Hitter:** 9️⃣

💜 **SOUTHEAST | PURPLE BANNER** 💜
🌟 **Poison Oak Storm Hitter 4:** 🇦
☀️ **Life Tree Support:** 🇧
🌛 **Life Tree Hitter:** 🇨

↪️ Backups:

<:yellowstar:1366156843134746704> **REMINDERS:** <:yellowstar:1366156843134746704>
<:Fire:1059511748199186482> & <:Death:1059512679494066216> 🌲 can chromatic weakness
<:Ice:1059511756256456734> & <:Life:1059512659436900432> 🌲 can chromatic shield

<:Fire:1059511748199186482> & <:Life:1059512659436900432> 🌲 = no traps
<:Ice:1059511756256456734> & <:Death:1059512679494066216> 🌲 = no blades or auras

{GUILD_MEMBER_PING}"""
}

RAID_REACTIONS = {  
    "Cabal's Revenge": ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🇦", "🇧", "🇨", "↪️"],
    "Crying Sky (Gatekeeper of the Apocalypse)": ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "🇦", "🇧", "🇨", "🇩", "↪️", "<:Fire:1059511748199186482>", "<:Ice:1059511756256456734>", "<:Storm:1059511770785534062>", "<:Myth:1059512670824439819>", "<:Life:1059512659436900432>", "<:Death:1059512679494066216>", "<:Balance:1059511860539433012>"],
    "Crying Sky": ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "🇦", "🇧", "🇨", "🇩", "↪️"],
    "Voracious Void": ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "🇦", "🇧", "🇨", "🇩", "↪️"],
    "Poison Oak Only": ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🇦", "🇧", "🇨", "↪️"]
}

SIGNUP_MAPPINGS = {  
    "Cabal's Revenge": {
        "roles": {
            "1️⃣": "**Northwest: Personal Daemon -yth/Fire/Storm 2**",
            "2️⃣": "**Northwest: Oblongata -yth 1**",
            "3️⃣": "**Northwest: West Cannon Mob Puller**",
            "4️⃣": "**Northeast: Divine Cabalist Support 1**",
            "5️⃣": "**Northeast: Oblongata -yth 2**",
            "6️⃣": "**Northeast: East Cannon Mob Puller**",
            "7️⃣": "**Southwest: Divine Cabalist Storm 2**",
            "8️⃣": "**Southwest: Poison Oak 1**",
            "9️⃣": "**Southwest: West Cannon Shooter 1**",
            "🇦": "**Southeast: Personal Daemon -yth/Support 1**",
            "🇧": "**Southeast: Poison Oak 2**",
            "🇨": "**Southeast: West Cannon Shooter 2**",
            "↪️": "**Backups**"
        }
    },
    "Crying Sky (Gatekeeper of the Apocalypse)": {
        "roles": {
            "1️⃣": "**Ixta & Autloc Team: Support 1**",
            "2️⃣": "**Ixta & Autloc Team: Balance 2**",
            "3️⃣": "**Ixta & Autloc Team: Storm 3**",
            "4️⃣": "**Ixta & Autloc Team: Storm/Form/Morm 4**",
            "5️⃣": "**Yetaxa Team: Fire/Lire 1**",
            "6️⃣": "**Yetaxa Team: Fire 2**",
            "7️⃣": "**Yetaxa Team: Fire/Mire 3**",
            "8️⃣": "**Yetaxa Team: Fire 4**",
            "🇦": "**Cameca Team: -yth 1 (Preferably Ice)**",
            "🇧": "**Cameca Team: -yth 2 (Preferably Death)**",
            "🇨": "**Cameca Team: Fyth/Styth 3**",
            "🇩": "**Cameca Team: Fyth/Styth 4**",
            "↪️": "**Backups**"
        },
    },
    "Crying Sky": {
        "roles": {
            "1️⃣": "**Ixta & Autloc Team: Support 1**",
            "2️⃣": "**Ixta & Autloc Team: Support 2**",
            "3️⃣": "**Ixta & Autloc Team: Storm 3**",
            "4️⃣": "**Ixta & Autloc Team: -orm 4**",
            "5️⃣": "**Yetaxa Team: Fire/Lire 1**",
            "6️⃣": "**Yetaxa Team: Fire 2**",
            "7️⃣": "**Yetaxa Team: -ire 3**",
            "8️⃣": "**Yetaxa Team: Fire 4**",
            "🇦": "**Cameca Team: -yth 1**",
            "🇧": "**Cameca Team: -yth 2**",
            "🇨": "**Cameca Team: Fyth/Styth 3**",
            "🇩": "**Cameca Team: Fyth/Styth 4**",
            "↪️": "**Backups**"
        }
    },
    "Voracious Void": {
        "roles": {
            "1️⃣": "**Vanguard: Fire/Myth/Storm 1**",
            "2️⃣": "**Vanguard: Fire/Myth/Storm 2**",
            "3️⃣": "**Vanguard: Storm 3**",
            "4️⃣": "**Vanguard: Jade**",
            "5️⃣": "**Outside Combat: Surge/Milli Support**",
            "6️⃣": "**Outside Combat: Surge/Mob Pull**",
            "7️⃣": "**Outside Combat: Elf/Milli Support**",
            "8️⃣": "**Outside Combat: Off-School Elf/Milli Hitter**",
            "🇦": "**Drums: Close/Lead**",
            "🇧": "**Drums: Mid**",
            "🇨": "**Drums: Far**",
            "🇩": "**Pet Token/Mob Pull**",
            "↪️": "**Backups**"
        }
    },
    "Poison Oak Only": {
        "roles": {
            "1️⃣": "**Northwest: Poison Oak Support 1**",
            "2️⃣": "**Northwest: Ice Tree Support**",
            "3️⃣": "**Northwest: Ice Tree Hitter**",
            "4️⃣": "**Northeast: Poison Oak Support 2**",
            "5️⃣": "**Northeast: Death Tree Support**",
            "6️⃣": "**Northeast: Death Tree Hitter**",
            "7️⃣": "**Southwest: Poison Oak Support 3**",
            "8️⃣": "**Southwest: Fire Tree Support**",
            "9️⃣": "**Southwest: Fire Tree Hitter**",
            "🇦": "**Southeast: Poison Oak Storm Hitter 4**",
            "🇧": "**Southeast: Life Tree Support**",
            "🇨": "**Southeast: Life Tree Hitter**",
            "↪️": "**Backups**"
        }
    }
}