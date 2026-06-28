"""
Leaderboard system — wiki-accurate /top command with 18 categories and pagination.
"""
import math
import json
from sqlalchemy import select, func, desc
from database.engine import async_session
from database.models import User, Guild, GuildMember, Pet, Profession, Inventory, Horse


PAGE_SIZE = 75
PETS_PAGE_SIZE = 50

# Leaderboard type definitions
LEADERBOARD_TYPES = {
    "level":         {"name": "Top Level",         "alias": ["lvl"], "scope": "server", "page_size": PAGE_SIZE},
    "coins":         {"name": "Top Coins",         "alias": ["coin"], "scope": "server", "page_size": PAGE_SIZE},
    "globallevel":   {"name": "Top Global Level",  "alias": ["global", "globallvl", "glevel", "glvl"], "scope": "global", "page_size": PAGE_SIZE},
    "globalcoins":   {"name": "Top Global Coins",  "alias": ["globalcoin", "gcoins", "gcoin"], "scope": "global", "page_size": PAGE_SIZE},
    "timetravel":    {"name": "Top Time Travel",   "alias": ["tt"], "scope": "global", "page_size": PAGE_SIZE},
    "guilds":        {"name": "Top Guilds",        "alias": ["guild"], "scope": "global", "page_size": PAGE_SIZE},
    "cookies":       {"name": "Top Cookies",       "alias": ["cookie"], "scope": "global", "page_size": PAGE_SIZE},
    "worker":        {"name": "Top Worker",        "alias": [], "scope": "global", "page_size": PAGE_SIZE},
    "crafter":       {"name": "Top Crafter",       "alias": [], "scope": "global", "page_size": PAGE_SIZE},
    "lootboxer":     {"name": "Top Lootboxer",     "alias": [], "scope": "global", "page_size": PAGE_SIZE},
    "merchant":      {"name": "Top Merchant",       "alias": [], "scope": "global", "page_size": PAGE_SIZE},
    "enchanter":     {"name": "Top Enchanter",      "alias": [], "scope": "global", "page_size": PAGE_SIZE},
    "pets":          {"name": "Top Pets",           "alias": ["pet"], "scope": "global", "page_size": PETS_PAGE_SIZE},
    "coolness":      {"name": "Top Coolness",       "alias": [], "scope": "global", "page_size": PAGE_SIZE},
    "achievements":  {"name": "Top Achievements",   "alias": ["ach", "achievement"], "scope": "global", "page_size": PAGE_SIZE},
    "petascends":    {"name": "Top Pet Ascends",    "alias": [], "scope": "global", "page_size": PAGE_SIZE},
    "horsefails":    {"name": "Top Horse Fails",    "alias": [], "scope": "global", "page_size": PAGE_SIZE},
    "epicness":      {"name": "Top Epicness",       "alias": [], "scope": "global", "page_size": PAGE_SIZE},
}

# Build reverse alias map
_ALIAS_MAP = {}
for lt, info in LEADERBOARD_TYPES.items():
    for alias in info["alias"]:
        _ALIAS_MAP[alias] = lt

# Russian aliases for top types
_RU_TOP_ALIASES = {
    "уровень": "level", "лвл": "level",
    "монеты": "coins",
    "глобальный": "globallevel", "глобал": "globallevel",
    "глобальные_монеты": "globalcoins",
    "путешествие": "timetravel", "тт": "timetravel",
    "гильдии": "guilds", "гильдия": "guilds",
    "печенье": "cookies",
    "worker": "worker", "воркер": "worker",
    "crafter": "crafter", "крафтер": "crafter",
    "lootboxer": "lootboxer", "лутбоксер": "lootboxer",
    "merchant": "merchant", "мерчант": "merchant",
    "enchanter": "enchanter", "заинт": "enchanter",
    "питомцы": "pets", "питомец": "pets",
    "крутость": "coolness",
    "ачивки": "achievements", "достижения": "achievements",
    "асценды": "petascends", "подъёмы": "petascends",
    "лошадь_фейлы": "horsefails",
    "эпичность": "epicness",
}
_ALIAS_MAP.update(_RU_TOP_ALIASES)


def resolve_type(type_str: str) -> str | None:
    """Resolve a type string or alias to canonical type name."""
    if type_str in LEADERBOARD_TYPES:
        return type_str
    return _ALIAS_MAP.get(type_str.lower())


def _count_achievements(user) -> int:
    """Count achievements a user has earned (computed on-the-fly)."""
    count = 0
    # Level milestones
    for threshold in [10, 25, 50, 75, 100, 150, 200]:
        if user.level >= threshold:
            count += 1
    # Area milestones
    for threshold in [5, 10, 15]:
        if user.max_area >= threshold:
            count += 1
    # TT milestones
    for threshold in [1, 5, 10, 25, 50, 75]:
        if user.tt_count >= threshold:
            count += 1
    # Coins milestones
    for threshold in [100000, 1000000, 10000000, 100000000]:
        if user.coins >= threshold:
            count += 1
    # Coolness milestones
    for threshold in [100, 500, 1000]:
        if user.coolness >= threshold:
            count += 1
    return count


async def get_leaderboard(leaderboard_type: str, page: int = 1) -> dict:
    """Query the appropriate leaderboard. Returns entries, pagination info."""
    info = LEADERBOARD_TYPES.get(leaderboard_type)
    if not info:
        return {"error": f"Unknown leaderboard type: {leaderboard_type}"}

    page_size = info["page_size"]
    offset = (page - 1) * page_size

    async with async_session() as s:
        if leaderboard_type in ("guilds",):
            # Guild leaderboard
            result = await s.execute(
                select(Guild).order_by(desc(Guild.xp), desc(Guild.level))
                .offset(offset).limit(page_size)
            )
            guilds = result.scalars().all()

            # Get total count
            count_result = await s.execute(select(func.count(Guild.guild_id)))
            total = count_result.scalar() or 0
            total_pages = max(1, math.ceil(total / page_size))

            entries = []
            for i, g in enumerate(guilds):
                # Count members
                mem_count = await s.execute(
                    select(func.count(GuildMember.user_id))
                    .where(GuildMember.guild_id == g.guild_id)
                )
                member_count = mem_count.scalar() or 0
                entries.append({
                    "name": g.name,
                    "value": f"Lvl. {g.level} | {g.xp:,} XP",
                    "members": member_count,
                })

            return {
                "entries": entries,
                "page": page,
                "total_pages": total_pages,
                "type_name": info["name"],
                "page_size": page_size,
                "guild": True,
            }

        elif leaderboard_type == "pets":
            # Pet score leaderboard (aggregate per user)
            result = await s.execute(
                select(Pet.user_id, func.sum(Pet.pet_score).label("total_score"))
                .group_by(Pet.user_id)
                .order_by(desc("total_score"))
                .offset(offset).limit(page_size)
            )
            rows = result.all()

            count_result = await s.execute(
                select(func.count(func.distinct(Pet.user_id)))
            )
            total = count_result.scalar() or 0
            total_pages = max(1, math.ceil(total / page_size))

            entries = []
            for user_id, total_score in rows:
                user = await s.get(User, user_id)
                entries.append({
                    "name": user.username or str(user_id) if user else str(user_id),
                    "value": f"{total_score or 0} pts",
                })

            return {
                "entries": entries,
                "page": page,
                "total_pages": total_pages,
                "type_name": info["name"],
                "page_size": page_size,
            }

        elif leaderboard_type == "petascends":
            # Pet ascend count leaderboard
            result = await s.execute(
                select(Pet.user_id, func.count(Pet.pet_id).label("ascend_count"))
                .where(Pet.skill == "ascended_skill")
                .group_by(Pet.user_id)
                .order_by(desc("ascend_count"))
                .offset(offset).limit(page_size)
            )
            rows = result.all()

            count_result = await s.execute(
                select(func.count(func.distinct(Pet.user_id)))
                .where(Pet.skill == "ascended_skill")
            )
            total = count_result.scalar() or 0
            total_pages = max(1, math.ceil(total / page_size))

            entries = []
            for user_id, ascend_count in rows:
                user = await s.get(User, user_id)
                entries.append({
                    "name": user.username or str(user_id) if user else str(user_id),
                    "value": f"{ascend_count} ascends",
                })

            return {
                "entries": entries,
                "page": page,
                "total_pages": total_pages,
                "type_name": info["name"],
                "page_size": page_size,
            }

        elif leaderboard_type in ("worker", "crafter", "lootboxer", "merchant", "enchanter"):
            # Profession XP leaderboard
            prof_field = getattr(Profession, f"{leaderboard_type}_xp")
            result = await s.execute(
                select(User, Profession)
                .join(Profession, User.user_id == Profession.user_id)
                .order_by(desc(prof_field))
                .offset(offset).limit(page_size)
            )
            rows = result.all()

            count_result = await s.execute(select(func.count(Profession.user_id)))
            total = count_result.scalar() or 0
            total_pages = max(1, math.ceil(total / page_size))

            entries = []
            for user, prof in rows:
                xp = getattr(prof, f"{leaderboard_type}_xp", 0)
                entries.append({
                    "name": user.username or str(user.user_id),
                    "value": f"{xp:,} XP",
                })

            return {
                "entries": entries,
                "page": page,
                "total_pages": total_pages,
                "type_name": info["name"],
                "page_size": page_size,
            }

        elif leaderboard_type == "cookies":
            # Arena cookies (from inventory JSON)
            result = await s.execute(
                select(User, Inventory)
                .join(Inventory, User.user_id == Inventory.user_id)
            )
            rows = result.all()

            # Parse cookies from materials JSON and sort
            user_cookies = []
            for user, inv in rows:
                mats = json.loads(inv.materials) if inv.materials else {}
                cookies = mats.get("arenacookie", 0)
                if cookies > 0:
                    user_cookies.append((user, cookies))
            user_cookies.sort(key=lambda x: x[1], reverse=True)

            total = len(user_cookies)
            total_pages = max(1, math.ceil(total / page_size))
            page_items = user_cookies[offset:offset + page_size]

            entries = []
            for user, cookies in page_items:
                entries.append({
                    "name": user.username or str(user.user_id),
                    "value": f"{cookies:,} cookies",
                })

            return {
                "entries": entries,
                "page": page,
                "total_pages": total_pages,
                "type_name": info["name"],
                "page_size": page_size,
            }

        elif leaderboard_type == "achievements":
            # Achievements — computed on-the-fly, fetch all users
            result = await s.execute(select(User))
            users = result.scalars().all()

            user_achievements = []
            for u in users:
                count = _count_achievements(u)
                if count > 0:
                    user_achievements.append((u, count))
            user_achievements.sort(key=lambda x: x[1], reverse=True)

            total = len(user_achievements)
            total_pages = max(1, math.ceil(total / page_size))
            page_items = user_achievements[offset:offset + page_size]

            entries = []
            for user, count in page_items:
                entries.append({
                    "name": user.username or str(user.user_id),
                    "value": f"{count} achievements",
                })

            return {
                "entries": entries,
                "page": page,
                "total_pages": total_pages,
                "type_name": info["name"],
                "page_size": page_size,
            }

        elif leaderboard_type == "horsefails":
            # Horse fail count
            result = await s.execute(
                select(User, Horse)
                .join(Horse, User.user_id == Horse.user_id)
                .order_by(desc(Horse.fail_count))
                .offset(offset).limit(page_size)
            )
            rows = result.all()

            count_result = await s.execute(select(func.count(Horse.user_id)))
            total = count_result.scalar() or 0
            total_pages = max(1, math.ceil(total / page_size))

            entries = []
            for user, horse in rows:
                entries.append({
                    "name": user.username or str(user.user_id),
                    "value": f"{horse.fail_count} fails",
                })

            return {
                "entries": entries,
                "page": page,
                "total_pages": total_pages,
                "type_name": info["name"],
                "page_size": page_size,
            }

        elif leaderboard_type == "epicness":
            # Horse epicness
            result = await s.execute(
                select(User, Horse)
                .join(Horse, User.user_id == Horse.user_id)
                .order_by(desc(Horse.epicness))
                .offset(offset).limit(page_size)
            )
            rows = result.all()

            count_result = await s.execute(select(func.count(Horse.user_id)))
            total = count_result.scalar() or 0
            total_pages = max(1, math.ceil(total / page_size))

            entries = []
            for user, horse in rows:
                entries.append({
                    "name": user.username or str(user.user_id),
                    "value": f"{horse.epicness} epicness",
                })

            return {
                "entries": entries,
                "page": page,
                "total_pages": total_pages,
                "type_name": info["name"],
                "page_size": page_size,
            }

        else:
            # Standard user leaderboards: level, coins, globallevel, globalcoins, timetravel, coolness
            sort_fields = {
                "level": (desc(User.level), desc(User.xp)),
                "coins": (desc(User.coins),),
                "globallevel": (desc(User.level), desc(User.xp)),
                "globalcoins": (desc(User.coins),),
                "timetravel": (desc(User.tt_count), desc(User.level)),
                "coolness": (desc(User.coolness), desc(User.level)),
            }
            order = sort_fields.get(leaderboard_type, (desc(User.level), desc(User.xp)))

            result = await s.execute(
                select(User).order_by(*order).offset(offset).limit(page_size)
            )
            users = result.scalars().all()

            count_result = await s.execute(select(func.count(User.user_id)))
            total = count_result.scalar() or 0
            total_pages = max(1, math.ceil(total / page_size))

            value_formats = {
                "level": lambda u: f"Lvl. {u.level} | {u.xp:,} XP",
                "coins": lambda u: f"{u.coins:,} coins",
                "globallevel": lambda u: f"Lvl. {u.level} | {u.xp:,} XP",
                "globalcoins": lambda u: f"{u.coins:,} coins",
                "timetravel": lambda u: f"TT{u.tt_count}",
                "coolness": lambda u: f"{u.coolness} coolness",
            }
            fmt = value_formats.get(leaderboard_type, lambda u: f"Lvl. {u.level}")

            entries = []
            for u in users:
                entries.append({
                    "name": u.username or str(u.user_id),
                    "value": fmt(u),
                })

            return {
                "entries": entries,
                "page": page,
                "total_pages": total_pages,
                "type_name": info["name"],
                "page_size": page_size,
            }


def format_leaderboard(result: dict) -> str:
    """Format leaderboard result into an HTML message."""
    if "error" in result:
        return f"❌ {result['error']}"

    entries = result["entries"]
    page = result["page"]
    total_pages = result["total_pages"]
    type_name = result["type_name"]

    if not entries:
        return f"🏆 <b>{type_name}</b>\n\nПока нет игроков в рейтинге."

    medals = ["🥇", "🥈", "🥉"]
    text = f"🏆 <b>{type_name}</b> (Стр. {page}/{total_pages})\n\n"

    for i, entry in enumerate(entries):
        rank = (page - 1) * result["page_size"] + i + 1
        medal = medals[i] if i < 3 and page == 1 else f"{rank}."
        name = entry["name"]
        value = entry["value"]

        if result.get("guild"):
            members = entry.get("members", 0)
            text += f"{medal} <b>{name}</b> — {value} | {members} members\n"
        else:
            text += f"{medal} <b>{name}</b> — {value}\n"

    if total_pages > 1:
        next_page = page + 1
        text += f"\nСтр. {next_page}: /top {result.get('type_key', 'level')} {next_page}"

    return text
