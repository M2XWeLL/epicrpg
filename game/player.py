import math
import json
import config
from database.crud import get_user, get_inventory, get_equipment


def calc_atk(level: int, weapon_tier: int, enchant_pct: int = 0) -> int:
    """ATK = (base + weapon) * (1 + enchant_pct/100)"""
    base = math.floor(5 * level ** 1.1)
    weapon = config.ATK_WEAPON_TIER.get(weapon_tier, 0)
    total = base + weapon
    if enchant_pct:
        total = math.floor(total * (1 + enchant_pct / 100))
    return total


def calc_def(level: int, armor_tier: int, enchant_pct: int = 0) -> int:
    """DEF = (base + armor) * (1 + enchant_pct/100)"""
    base = math.floor(3 * level ** 1.05)
    armor_stat = config.ARMOR_DEF_TIER.get(armor_tier, 0)
    total = base + armor_stat
    if enchant_pct:
        total = math.floor(total * (1 + enchant_pct / 100))
    return total


def calc_xp_for_level(level: int) -> int:
    """XP required = floor(100 * L^2.2 + 500 * L)"""
    return math.floor(config.XP_BASE * level ** config.XP_EXP + config.XP_FLAT * level)


def get_tt_xp_bonus(tt_count: int) -> float:
    """Wiki: % extra EXP = (99 + x) * x / 2 — returns as decimal multiplier."""
    return ((99 + tt_count) * tt_count / 2) / 100


def get_tt_duel_xp_bonus(tt_count: int) -> float:
    """Wiki: % extra EXP in duels = (99 + x) * x / 4 — returns as decimal multiplier."""
    return ((99 + tt_count) * tt_count / 4) / 100


def get_tt_drop_bonus(tt_count: int) -> float:
    """Wiki: % extra chance for monster drops = (49 + x) * x / 2 — returns as decimal multiplier."""
    return ((49 + tt_count) * tt_count / 2) / 100


def get_tt_items_bonus(tt_count: int) -> float:
    """Wiki: % extra items in working commands = (49 + x) * x / 2 — returns as decimal multiplier."""
    return ((49 + tt_count) * tt_count / 2) / 100


def get_tt_bonus(tt_count: int) -> float:
    """Legacy XP bonus — returns as decimal multiplier (compatible with 1+ callers)."""
    return get_tt_xp_bonus(tt_count)


def get_tt_bonus_pct(tt_count: int) -> float:
    """XP bonus as raw percentage for display (e.g. 545 at TT10)."""
    return (99 + tt_count) * tt_count / 2


def calc_tt_cooldown_mult(tt_count: int) -> float:
    reduction = tt_count * config.TT_CD_REDUCTION
    return min(reduction, config.TT_CD_MAX)


async def get_player_stats(user_id: int) -> dict:
    user = await get_user(user_id)
    if not user:
        return {}
    eq = await get_equipment(user_id)
    inv = await get_inventory(user_id)

    level = user.level
    weapon_tier = eq.get("weapon_tier", 1)
    armor_tier = eq.get("armor_tier", 1)

    return {
        "user_id": user.user_id,
        "username": user.username,
        "level": level,
        "xp": user.xp,
        "xp_needed": calc_xp_for_level(level),
        "coins": user.coins,
        "area": user.area,
        "tt_count": user.tt_count,
        "atk": calc_atk(level, weapon_tier),
        "def": calc_def(level, armor_tier),
        "weapon_tier": weapon_tier,
        "armor_tier": armor_tier,
        "materials": inv,
        "tt_bonus": get_tt_bonus(user.tt_count),
        "weapon_enchant": eq.get("sword_enchant", {}),
        "armor_enchant": eq.get("armor_enchant", {}),
    }


async def add_xp(user_id: int, amount: int) -> dict:
    """Add XP and check for level up."""
    from database.engine import async_session
    from database.models import User

    result = {"leveled_up": False, "new_level": 0, "coins_bonus": 0}
    async with async_session() as s:
        user = await s.get(User, user_id)
        if not user:
            return result

        tt_mult = 1 + get_tt_bonus(user.tt_count)
        actual_xp = int(amount * tt_mult)
        user.xp += actual_xp

        levels_gained = 0
        while user.level < config.MAX_LEVEL:
            needed = calc_xp_for_level(user.level)
            if user.xp >= needed:
                user.xp -= needed
                user.level += 1
                levels_gained += 1
            else:
                break

        if levels_gained > 0:
            result["leveled_up"] = True
            result["new_level"] = user.level
            result["coins_bonus"] = levels_gained * 10

        user.coins += result["coins_bonus"]
        await s.commit()

    return result


async def add_coins(user_id: int, amount: int):
    from database.engine import async_session
    from database.models import User
    async with async_session() as s:
        user = await s.get(User, user_id)
        if user:
            tt_mult = 1 + get_tt_bonus(user.tt_count)
            user.coins += int(amount * tt_mult)
            await s.commit()


async def remove_coins(user_id: int, amount: int) -> bool:
    from database.engine import async_session
    from database.models import User
    async with async_session() as s:
        user = await s.get(User, user_id)
        if not user or user.coins < amount:
            return False
        user.coins -= amount
        await s.commit()
        return True


async def get_pet_bonuses(user_id: int) -> dict:
    """Get active pet bonuses for a player based on skills and ranks."""
    from database.engine import async_session
    from database.models import Pet
    from sqlalchemy import select
    bonuses = {"hunt_cd": 0.0, "adventure_cd": 0.0, "gather_cd": 0.0, "coins": 0.0, "drop": 0.0, "xp": 0.0}

    async with async_session() as s:
        pets = (await s.execute(
            select(Pet).where(Pet.user_id == user_id)
        )).scalars().all()

        for pet in pets:
            rank_mult = config.PET_RANK_MULT.get(pet.skill_rank, 1)

            if pet.skill == "fast":
                bonuses["adventure_cd"] += rank_mult * 0.01
                bonuses["hunt_cd"] += rank_mult * 0.005
                bonuses["gather_cd"] += rank_mult * 0.005
            elif pet.skill == "digger":
                bonuses["coins"] += rank_mult * 0.005
            elif pet.skill == "lucky":
                bonuses["drop"] += rank_mult * 0.005
            elif pet.skill == "clever":
                bonuses["xp"] += rank_mult * 0.003
            elif pet.skill == "epic":
                bonuses["coins"] += 0.01
                bonuses["xp"] += 0.01
            elif pet.skill == "ascended":
                bonuses["drop"] += 0.02
                bonuses["coins"] += 0.01
            elif pet.skill == "fighter":
                bonuses["xp"] += 0.01

    return bonuses
