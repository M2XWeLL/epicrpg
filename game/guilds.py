import json
import config
from sqlalchemy import select


async def create_guild(owner_id: int, name: str) -> dict:
    from database.engine import async_session
    from database.models import Guild, GuildMember, User

    async with async_session() as s:
        user = await s.get(User, owner_id)
        if not user:
            return {"success": False, "message": "Игрок не найден."}
        if user.coins < config.GUILD_CREATE_COST:
            return {"success": False, "message": f"❌ Нужно {config.GUILD_CREATE_COST} монет."}

        # Check if already in guild
        existing = await s.execute(select(GuildMember).where(GuildMember.user_id == owner_id))
        if existing.scalar_one_or_none():
            return {"success": False, "message": "❌ Вы уже в гильдии."}

        # Check name taken
        name_exists = await s.execute(select(Guild).where(Guild.name == name))
        if name_exists.scalar_one_or_none():
            return {"success": False, "message": "❌ Гильдия с таким именем уже существует."}

        user.coins -= config.GUILD_CREATE_COST
        guild = Guild(name=name, owner_id=owner_id)
        s.add(guild)
        await s.flush()
        member = GuildMember(user_id=owner_id, guild_id=guild.guild_id, rank="leader")
        s.add(member)
        await s.commit()

        return {"success": True, "message": f"🏰 Гильдия «{name}» создана!"}


async def join_guild(user_id: int, guild_name: str) -> dict:
    from database.engine import async_session
    from database.models import Guild, GuildMember, User

    async with async_session() as s:
        existing = await s.execute(select(GuildMember).where(GuildMember.user_id == user_id))
        if existing.scalar_one_or_none():
            return {"success": False, "message": "❌ Вы уже в гильдии."}

        result = await s.execute(select(Guild).where(Guild.name == guild_name))
        guild = result.scalar_one_or_none()
        if not guild:
            return {"success": False, "message": "❌ Гильдия не найдена."}

        # Check member count
        member_count = await s.execute(
            select(GuildMember).where(GuildMember.guild_id == guild.guild_id)
        )
        count = len(member_count.scalars().all())
        if count >= config.GUILD_MAX_MEMBERS:
            return {"success": False, "message": "❌ Гильдия полная."}

        member = GuildMember(user_id=user_id, guild_id=guild.guild_id)
        s.add(member)
        guild_xp = guild.xp
        await s.commit()

        return {"success": True, "message": f"🏰 Вы вступили в «{guild_name}»!"}


async def deposit_to_guild(user_id: int, material: str, amount: int) -> dict:
    from database.engine import async_session
    from database.models import Guild, GuildMember, Inventory
    from database.crud import remove_materials

    async with async_session() as s:
        member_result = await s.execute(select(GuildMember).where(GuildMember.user_id == user_id))
        member = member_result.scalar_one_or_none()
        if not member:
            return {"success": False, "message": "❌ Вы не в гильдии."}

        guild = await s.get(Guild, member.guild_id)

        # Check player has materials
        inv = await s.get(Inventory, user_id)
        if inv:
            mats = json.loads(inv.materials)
            if mats.get(material, 0) < amount:
                return {"success": False, "message": f"❌ Недостаточно {material}."}

            mats[material] -= amount
            inv.materials = json.dumps(mats)

            # Add to guild
            gm = json.loads(guild.materials)
            gm[material] = gm.get(material, 0) + amount
            guild.materials = json.dumps(gm)

            # Guild XP
            guild.xp += amount * 10

            await s.commit()

        return {"success": True, "message": f"📦 Сдано {amount}x {material} в хранилище гильдии."}


async def get_guild_info(user_id: int) -> dict:
    from database.engine import async_session
    from database.models import Guild, GuildMember, User
    from sqlalchemy import func

    async with async_session() as s:
        member_result = await s.execute(select(GuildMember).where(GuildMember.user_id == user_id))
        member = member_result.scalar_one_or_none()
        if not member:
            return {"success": False, "message": "❌ Вы не в гильдии."}

        guild = await s.get(Guild, member.guild_id)
        owner = await s.get(User, guild.owner_id)

        member_count_result = await s.execute(
            select(func.count()).select_from(GuildMember).where(GuildMember.guild_id == guild.guild_id)
        )
        member_count = member_count_result.scalar()

        return {
            "success": True,
            "name": guild.name,
            "level": guild.level,
            "xp": guild.xp,
            "owner": owner.username if owner else "Unknown",
            "members": member_count,
            "materials": json.loads(guild.materials),
            "rank": member.rank,
        }


async def leave_guild(user_id: int) -> dict:
    from database.engine import async_session
    from database.models import GuildMember, Guild

    async with async_session() as s:
        member = (await s.execute(
            select(GuildMember).where(GuildMember.user_id == user_id)
        )).scalar_one_or_none()
        if not member:
            return {"success": False, "message": "❌ Вы не в гильдии."}
        if member.rank == "leader":
            return {"success": False, "message": "❌ Лидер не может покинуть гильдию. Передайте лидерство или распустите."}
        await s.delete(member)
        await s.commit()
        return {"success": True, "message": "👋 Вы покинули гильдию."}
