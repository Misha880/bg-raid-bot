import aiosqlite

# Database manager using aiosqlite
class DBManager:
    EXPECTED_COLUMNS = {
        "raid_id":         "INTEGER PRIMARY KEY",
        "raid_name":       "TEXT",
        "channel_id":      "INTEGER",
        "raid_type":       "TEXT",
        "start_timestamp": "INTEGER",
        "ping_timestamp":  "INTEGER",
        "duration":        "TEXT",
        "tz":              "TEXT",
    }

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    async def initialize(self):
        self.conn = await aiosqlite.connect(self.db_path)
        cols = ",\n    ".join(f"{n} {d}" for n, d in self.EXPECTED_COLUMNS.items())
        await self.conn.execute(f"""
        CREATE TABLE IF NOT EXISTS active_raids (
            {cols}
        );
        """)
        cursor = await self.conn.execute("PRAGMA table_info(active_raids)")
        existing = {row[1] for row in await cursor.fetchall()}
        for col, col_def in self.EXPECTED_COLUMNS.items():
            if col not in existing:
                await self.conn.execute(f"ALTER TABLE active_raids ADD COLUMN {col} {col_def}")
        await self.conn.commit()

    async def fetchall(self, query: str, params: tuple = ()):
        async with self.conn.execute(query, params) as c:
            return await c.fetchall()

    async def fetchone(self, query: str, params: tuple = ()):
        async with self.conn.execute(query, params) as c:
            return await c.fetchone()

    async def execute(self, query: str, params: tuple = ()):
        await self.conn.execute(query, params)
        await self.conn.commit()

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None

# Create a single shared instance
db = DBManager("/data/active_raids.db")