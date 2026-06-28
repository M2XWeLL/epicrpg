import math
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user, get_equipment
from game.player import calc_atk, calc_def, calc_xp_for_level, get_tt_bonus
from game.areas import get_area, load_areas
from utils.formatters import format_profile, _calc_rank

router = Router()


@router.message(F.text == "/profile")
@router.message(F.text == "/stats")
async def cmd_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    eq = await get_equipment(message.from_user.id)
    level = user.level
    weapon_tier = eq.get("weapon_tier", 1)
    armor_tier = eq.get("armor_tier", 1)

    # Max area unlocked
    areas = load_areas()
    max_area = 1
    for area_num in sorted(areas.keys(), key=int):
        area_data = areas[area_num]
        if level >= area_data.get("min_level", 1):
            max_area = int(area_num)

    hp = 100 + level * 5

    # Get horse info
    from database.engine import async_session
    from database.models import Horse
    horse_tier = 1
    horse_type = "normal"
    async with async_session() as s:
        horse = await s.get(Horse, message.from_user.id)
        if horse:
            horse_tier = horse.tier
            horse_type = horse.horse_type

    # Horse bonus to HP
    if horse_type == "tank":
        hp = int(hp * (1 + horse_tier * 0.05))

    profile_data = {
        "username": user.username or message.from_user.first_name,
        "level": level,
        "xp": user.xp,
        "xp_needed": calc_xp_for_level(level),
        "coins": user.coins,
        "epic_coins": user.epic_coins,
        "bank": user.bank,
        "area": user.area,
        "max_area": max_area,
        "tt_count": user.tt_count,
        "atk": calc_atk(level, weapon_tier),
        "def": calc_def(level, armor_tier),
        "weapon_tier": weapon_tier,
        "armor_tier": armor_tier,
        "hp": hp,
        "max_hp": hp,
        "coolness": user.coolness,
        "horse_tier": horse_tier,
        "horse_type": horse_type,
        "title": user.title or "",
        "rank": _calc_rank(level, user.tt_count),
    }

    text = format_profile(profile_data, user.lang or "en")
    await message.answer(text, parse_mode="HTML")
