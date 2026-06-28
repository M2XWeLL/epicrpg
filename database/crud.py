import json
from datetime import datetime
from sqlalchemy import select
from database.engine import async_session
from database.models import User, Inventory, Cooldown


async def get_or_create_user(user_id: int, username: str = "") -> User:
    async with async_session() as s:
        user = await s.get(User, user_id)
        if not user:
            user = User(user_id=user_id, username=username)
            inv = Inventory(user_id=user_id)
            cd = Cooldown(user_id=user_id)
            s.add_all([user, inv, cd])
            await s.commit()
        elif username and user.username != username:
            user.username = username
            await s.commit()
        return user


async def get_user(user_id: int) -> User | None:
    async with async_session() as s:
        return await s.get(User, user_id)


async def get_inventory(user_id: int) -> dict:
    async with async_session() as s:
        inv = await s.get(Inventory, user_id)
        if not inv:
            from config import DEFAULT_MATERIALS
            return dict(DEFAULT_MATERIALS)
        return json.loads(inv.materials)


async def set_inventory(user_id: int, materials: dict):
    async with async_session() as s:
        inv = await s.get(Inventory, user_id)
        if inv:
            inv.materials = json.dumps(materials)
            await s.commit()


async def get_equipment(user_id: int) -> dict:
    async with async_session() as s:
        inv = await s.get(Inventory, user_id)
        if not inv:
            return {"weapon_tier": 1, "armor_tier": 1}
        return json.loads(inv.equipment)


async def set_equipment(user_id: int, equipment: dict):
    async with async_session() as s:
        inv = await s.get(Inventory, user_id)
        if inv:
            inv.equipment = json.dumps(equipment)
            await s.commit()


async def get_tools(user_id: int) -> dict:
    async with async_session() as s:
        inv = await s.get(Inventory, user_id)
        if not inv:
            return {"axe": 1, "pickaxe": 1, "rod": 1}
        return json.loads(inv.tools)


async def set_tools(user_id: int, tools: dict):
    async with async_session() as s:
        inv = await s.get(Inventory, user_id)
        if inv:
            inv.tools = json.dumps(tools)
            await s.commit()


async def add_materials(user_id: int, material: str, amount: int):
    async with async_session() as s:
        inv = await s.get(Inventory, user_id)
        if inv:
            mats = json.loads(inv.materials)
            mats[material] = mats.get(material, 0) + amount
            inv.materials = json.dumps(mats)
            await s.commit()


async def remove_materials(user_id: int, material: str, amount: int) -> bool:
    async with async_session() as s:
        inv = await s.get(Inventory, user_id)
        if not inv:
            return False
        mats = json.loads(inv.materials)
        if mats.get(material, 0) < amount:
            return False
        mats[material] -= amount
        inv.materials = json.dumps(mats)
        await s.commit()
        return True


async def has_materials(user_id: int, costs: dict) -> bool:
    mats = await get_inventory(user_id)
    for mat, amt in costs.items():
        if mats.get(mat, 0) < amt:
            return False
    return True


async def update_cooldown(user_id: int, action: str) -> tuple[bool, int]:
    """Atomic: try to set cooldown. Returns (allowed, remaining_seconds)."""
    from config import COOLDOWNS
    from datetime import timedelta
    cd_seconds = COOLDOWNS.get(action, 60)
    # Returning event: 33% cooldown reduction
    if await has_active_returning_event(user_id):
        cd_seconds = int(cd_seconds * (1 - config.RETURNING_CD_REDUCTION))
    now = datetime.utcnow()
    cutoff = now - timedelta(seconds=cd_seconds)

    col_name = f"{action}_last"
    async with async_session() as s:
        cd = await s.get(Cooldown, user_id)
        if not cd:
            cd = Cooldown(user_id=user_id)
            s.add(cd)
            await s.commit()

        last_time = getattr(cd, col_name, None)
        if last_time and last_time.tzinfo is not None:
            last_time = last_time.replace(tzinfo=None)
        if last_time and last_time > cutoff:
            remaining = int((last_time - cutoff).total_seconds())
            return False, remaining

        setattr(cd, col_name, now)
        await s.commit()
        return True, 0


async def get_cooldowns(user_id: int) -> Cooldown:
    async with async_session() as s:
        cd = await s.get(Cooldown, user_id)
        if not cd:
            cd = Cooldown(user_id=user_id)
            s.add(cd)
            await s.commit()
        return cd


async def update_coolness(user_id: int):
    """Recalculate coolness = tt_count * 10 + level * 2 + area * 5."""
    from database.engine import async_session as sess
    from database.models import User
    async with sess() as s:
        user = await s.get(User, user_id)
        if user:
            user.coolness = user.tt_count * 10 + user.level * 2 + user.area * 5
            await s.commit()


async def get_profession(user_id: int) -> dict | None:
    from database.models import Profession
    async with async_session() as s:
        p = await s.get(Profession, user_id)
        if not p:
            return None
        return {
            "worker_level": p.worker_level, "worker_xp": p.worker_xp,
            "crafter_level": p.crafter_level, "crafter_xp": p.crafter_xp,
            "lootboxer_level": p.lootboxer_level, "lootboxer_xp": p.lootboxer_xp,
            "merchant_level": p.merchant_level, "merchant_xp": p.merchant_xp,
            "enchanter_level": p.enchanter_level, "enchanter_xp": p.enchanter_xp,
        }


async def add_profession_xp(user_id: int, profession: str, xp: int):
    """Add XP to a profession and auto-level up."""
    from database.models import Profession

    async with async_session() as s:
        p = await s.get(Profession, user_id)
        if not p:
            p = Profession(user_id=user_id)
            s.add(p)
            await s.commit()
            p = await s.get(Profession, user_id)

        level_col = f"{profession}_level"
        xp_col = f"{profession}_xp"

        current_level = getattr(p, level_col)
        current_xp = getattr(p, xp_col)
        current_xp += xp

        # XP needed per level grows exponentially
        while True:
            xp_needed = int(100 * (1.5 ** (current_level - 1)))
            if current_xp < xp_needed:
                break
            current_xp -= xp_needed
            current_level += 1

        setattr(p, level_col, current_level)
        setattr(p, xp_col, current_xp)
        await s.commit()


async def get_profession_bonus(user_id: int, profession: str) -> dict:
    """Get the bonus from a profession level."""
    p = await get_profession(user_id)
    if not p:
        return {"level": 1}

    level = p.get(f"{profession}_level", 1)
    bonuses = {
        "worker": {"chance_better_item": min(level * 0.005, 0.50)},
        "crafter": {"save_recipe_chance": min(level * 0.003, 0.30)},
        "lootboxer": {"bank_bonus": level * 0.002, "horse_discount": min(level * 0.001, 0.10)},
        "merchant": {"sell_price_bonus": min(level * 0.003, 0.30)},
        "enchanter": {"better_enchant_chance": min(level * 0.005, 0.50)},
    }
    bonus = bonuses.get(profession, {})
    bonus["level"] = level
    return bonus


async def convert_materials(user_id: int, from_mat: str, to_mat: str, from_amount: int) -> dict:
    from config import CONVERSION_RATE
    async with async_session() as s:
        inv = await s.get(Inventory, user_id)
        if not inv:
            return {"success": False, "message": "Инвентарь не найден."}
        mats = json.loads(inv.materials)
        if mats.get(from_mat, 0) < from_amount:
            return {"success": False, "message": f"Недостаточно {from_mat}."}
        if from_amount % CONVERSION_RATE != 0:
            return {"success": False, "message": f"Количество должно быть кратно {CONVERSION_RATE}."}
        converted = from_amount // CONVERSION_RATE
        mats[from_mat] -= from_amount
        mats[to_mat] = mats.get(to_mat, 0) + converted
        inv.materials = json.dumps(mats)
        await s.commit()
        return {"success": True, "converted": converted}


# ---------------------------------------------------------------------------
# Returning Event
# ---------------------------------------------------------------------------

async def update_last_active(user_id: int):
    """Update user's last_active timestamp to now."""
    from database.models import User
    async with async_session() as s:
        user = await s.get(User, user_id)
        if user:
            user.last_active = datetime.utcnow()
            await s.commit()


async def check_returning_player(user_id: int) -> bool:
    """Return True if user is a returning player (inactive 7+ days)."""
    from database.models import User
    from datetime import timedelta
    async with async_session() as s:
        user = await s.get(User, user_id)
        if not user:
            return False
        if user.last_active is None:
            return True
        last = user.last_active
        if last.tzinfo is not None:
            last = last.replace(tzinfo=None)
        return (datetime.utcnow() - last) >= timedelta(days=7)


async def get_returning_event(user_id: int):
    """Get the user's active returning event, or None."""
    from database.models import ReturningEvent
    async with async_session() as s:
        re = await s.get(ReturningEvent, user_id)
        if not re:
            return None
        # Check if event expired (7 days)
        from datetime import timedelta
        started = re.started_at
        if started and started.tzinfo is not None:
            started = started.replace(tzinfo=None)
        if started and (datetime.utcnow() - started) >= timedelta(days=7):
            await s.delete(re)
            await s.commit()
            return None
        return re


async def create_returning_event(user_id: int):
    """Create a new returning event for the user."""
    from database.models import ReturningEvent
    async with async_session() as s:
        re = ReturningEvent(user_id=user_id, started_at=datetime.utcnow())
        s.add(re)
        await s.commit()
        return re


async def has_active_returning_event(user_id: int) -> bool:
    """Check if user has an active (non-expired) returning event."""
    re = await get_returning_event(user_id)
    return re is not None
