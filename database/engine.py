from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import DB_URL
from database.base import Base

engine = create_async_engine(DB_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


# --- SQLAlchemy type → SQLite type mapping ---
_SA_TO_SQLITE = {
    "BigInteger": "BIGINT",
    "Integer": "INTEGER",
    "String": None,   # handled specially (needs length)
    "Float": "REAL",
    "DateTime": "DATETIME",
    "Boolean": "BOOLEAN",
    "Text": "TEXT",
}


def _sa_type_to_sqlite(col) -> str:
    """Convert a SQLAlchemy Column type to a SQLite type string."""
    type_name = type(col.type).__name__
    if type_name == "String":
        length = getattr(col.type, "length", None)
        return f"VARCHAR({length})" if length else "VARCHAR(255)"
    result = _SA_TO_SQLITE.get(type_name)
    if result:
        return result
    return "TEXT"  # fallback


def _sa_default_to_sqlite(col):
    """Return (sql_default_clause, needs_default) for ALTER TABLE ADD COLUMN.

    Returns (default_str_or_None, True/False).
    If default_str is None → no DEFAULT clause (column is NULL-able).
    """
    # No default at all
    if col.default is None:
        return None, False

    # Server-side default (literal)
    if col.default.is_clause_element:
        return None, False

    val = col.default.arg
    if callable(val):
        # utcnow, etc. → NULL for DATETIME columns
        name = getattr(val, "__name__", "")
        if name == "utcnow":
            return None, False
        return None, False

    # Boolean → 0/1 in SQLite
    if isinstance(val, bool):
        return str(int(val)), True

    # String defaults
    if isinstance(val, str):
        return f"'{val}'", True

    # Numeric
    if isinstance(val, (int, float)):
        return str(val), True

    return None, False


async def _migrate_columns():
    """Ensure every column in every SQLAlchemy model exists in the DB.

    This runs on every startup and is fully idempotent — it compares
    PRAGMA table_info against model columns and adds any that are missing.
    One-off patches are no longer needed.
    """
    import logging
    import aiosqlite
    from datetime import datetime

    logger = logging.getLogger(__name__)

    db_path = str(DB_URL).replace("sqlite+aiosqlite:///", "")
    async with aiosqlite.connect(db_path) as db:

        async def get_db_columns(table: str) -> set:
            cursor = await db.execute(f"PRAGMA table_info({table})")
            rows = await cursor.fetchall()
            return {row[1] for row in rows}

        async def ensure_table_exists(table_name: str, create_sql: str):
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            if not await cursor.fetchone():
                await db.execute(create_sql)
                logger.info(f"Migration: created {table_name} table")

        # ──────────────────────────────────────────────
        # 1. Create tables that don't exist yet
        # ──────────────────────────────────────────────
        await ensure_table_exists("horses", """
            CREATE TABLE IF NOT EXISTS horses (
                user_id BIGINT PRIMARY KEY,
                name VARCHAR(50) DEFAULT 'Starter Horse',
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                tier INTEGER DEFAULT 1,
                horse_type VARCHAR(20) DEFAULT 'normal',
                epicness INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                coins BIGINT DEFAULT 0,
                last_breed_race DATETIME
            )
        """)
        await ensure_table_exists("lottery", """
            CREATE TABLE IF NOT EXISTS lottery (
                lottery_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT NOT NULL,
                numbers VARCHAR(20) NOT NULL,
                drawn INTEGER DEFAULT 0,
                created_at DATETIME
            )
        """)
        await ensure_table_exists("professions", """
            CREATE TABLE IF NOT EXISTS professions (
                user_id BIGINT PRIMARY KEY,
                worker_level INTEGER DEFAULT 1,
                worker_xp INTEGER DEFAULT 0,
                crafter_level INTEGER DEFAULT 1,
                crafter_xp INTEGER DEFAULT 0,
                lootboxer_level INTEGER DEFAULT 1,
                lootboxer_xp INTEGER DEFAULT 0,
                merchant_level INTEGER DEFAULT 1,
                merchant_xp INTEGER DEFAULT 0,
                enchanter_level INTEGER DEFAULT 1,
                enchanter_xp INTEGER DEFAULT 0,
                claimed TEXT DEFAULT '{}'
            )
        """)
        await ensure_table_exists("marriages", """
            CREATE TABLE IF NOT EXISTS marriages (
                marriage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id BIGINT NOT NULL,
                user2_id BIGINT NOT NULL,
                married_at DATETIME
            )
        """)
        await ensure_table_exists("returning_events", """
            CREATE TABLE IF NOT EXISTS returning_events (
                user_id BIGINT PRIMARY KEY,
                started_at DATETIME,
                superdaily_day INTEGER DEFAULT 0,
                quest_collected_smol INTEGER DEFAULT 0,
                quest_shop_buys INTEGER DEFAULT 0,
                quest_superdaily_claims INTEGER DEFAULT 0,
                shop_purchases TEXT DEFAULT '{}',
                quest_claimed BOOLEAN DEFAULT 0
            )
        """)

        # ──────────────────────────────────────────────
        # 2. Sync every model's columns to its table
        # ──────────────────────────────────────────────
        # Import models so all are registered with Base
        from database import models  # noqa: F401

        for table_name, sa_table in Base.metadata.tables.items():
            db_cols = await get_db_columns(table_name)

            for col in sa_table.columns:
                # Skip primary keys (already in CREATE TABLE)
                if col.primary_key:
                    continue

                col_name = col.name
                if col_name in db_cols:
                    continue

                sqlite_type = _sa_type_to_sqlite(col)
                default_str, has_default = _sa_default_to_sqlite(col)

                if has_default and default_str is not None:
                    ddl = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {sqlite_type} DEFAULT {default_str}"
                elif col.nullable:
                    ddl = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {sqlite_type}"
                else:
                    # NOT NULL without a default — use a safe fallback
                    sqlite_type_upper = sqlite_type.upper()
                    if "INT" in sqlite_type_upper:
                        fallback = "0"
                    elif "VARCHAR" in sqlite_type_upper or "TEXT" in sqlite_type_upper:
                        fallback = "''"
                    elif "BOOL" in sqlite_type_upper:
                        fallback = "0"
                    elif "REAL" in sqlite_type_upper:
                        fallback = "0.0"
                    else:
                        fallback = "''"
                    ddl = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {sqlite_type} DEFAULT {fallback}"

                await db.execute(ddl)
                logger.info(f"Migration: added {table_name}.{col_name}")

        # ──────────────────────────────────────────────
        # 3. Fix DATETIME columns that have '' instead of NULL
        # ──────────────────────────────────────────────
        for table_name in ("users", "cooldowns", "horses", "pets"):
            try:
                cursor = await db.execute(f"PRAGMA table_info({table_name})")
                dt_cols = [
                    row[1] for row in await cursor.fetchall()
                    if row[2] == "DATETIME"
                ]
                for dt_col in dt_cols:
                    await db.execute(
                        f"UPDATE {table_name} SET {dt_col} = NULL WHERE {dt_col} = ''"
                    )
            except Exception:
                pass

        # ──────────────────────────────────────────────
        # 4. Migrate old inventories to new material system
        # ──────────────────────────────────────────────
        import json
        cursor = await db.execute("SELECT user_id, materials FROM inventories")
        rows = await cursor.fetchall()
        new_keys = [
            "wooden_log", "epic_log", "super_log", "mega_log", "hyper_log",
            "ultra_log", "ultimate_log",
            "normie_fish", "golden_fish", "epic_fish", "super_fish", "mega_fish", "hyper_fish",
            "apple", "banana", "potato", "carrot", "bread", "Watermelon",
            "wolfskin", "zombieeye", "unicornhorn", "mermaid_hair",
            "ruby", "chip", "coin", "dragonscale", "lotteryticket",
            "life_potion", "arenacookie",
            "common_lootbox", "uncommon_lootbox", "rare_lootbox",
            "epic_lootbox", "edgy_lootbox", "omega_lootbox",
        ]
        migrated = 0
        for user_id, mat_json in rows:
            try:
                mats = json.loads(mat_json) if mat_json else {}
            except json.JSONDecodeError:
                mats = {}
            if "wooden_log" in mats:
                continue
            new_mats = {k: 0 for k in new_keys}
            await db.execute(
                "UPDATE inventories SET materials = ? WHERE user_id = ?",
                (json.dumps(new_mats), user_id)
            )
            migrated += 1
        if migrated:
            logger.info(f"Migration: reset {migrated} inventories to new material system")

        await db.commit()


async def init_db():
    async with engine.begin() as conn:
        from database import models  # noqa: F401 — register all models
        await conn.run_sync(Base.metadata.create_all)
    await _migrate_columns()
