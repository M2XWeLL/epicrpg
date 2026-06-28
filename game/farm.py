"""
Farm system — wiki-accurate.
Plant seeds to grow crops. Specific seeds guarantee their crop type.
Normal seed: 2-3 random crops, 4% chance 4-5 seeds back.
Specific seeds: 5-7 of that crop, 75% chance 1-2 seeds back.
Max 10,000 seeds. Unlocked at Area 4.
"""
import random
from datetime import datetime, timedelta
from game.player import add_xp
from database.crud import add_materials, remove_materials, get_user, get_inventory
from database.engine import async_session
from database.models import Cooldown

SEED_TYPES = ("seed", "potato_seed", "carrot_seed", "bread_seed")
SEED_EMOJIS = {
    "seed": "🌱", "potato_seed": "🥔", "carrot_seed": "🥕", "bread_seed": "🍞",
}
CROP_EMOJIS = {
    "potato": "🥔", "carrot": "🥕", "bread": "🍞",
    "apple": "🍎", "banana": "🍌",
}
MAX_SEEDS = 10000


async def farm(user_id: int, seed_type: str = "") -> dict:
    """Farm crops. Requires 1 seed. 10 min cooldown."""
    user = await get_user(user_id)
    if not user:
        return {"message": "Игрок не найден.", "success": False}

    if user.area < 4:
        return {"message": "❌ Farm доступен с Area 4.", "success": False}

    # Determine seed type
    if not seed_type or seed_type == "seed":
        seed_key = "seed"
    elif seed_type in ("potato", "potato_seed"):
        seed_key = "potato_seed"
    elif seed_type in ("carrot", "carrot_seed"):
        seed_key = "carrot_seed"
    elif seed_type in ("bread", "bread_seed"):
        seed_key = "bread_seed"
    else:
        return {
            "message": "❌ Неизвестный тип семян. Доступные: seed, potato_seed, carrot_seed, bread_seed",
            "success": False,
        }

    # Check seeds
    inv = await get_inventory(user_id)
    if inv.get(seed_key, 0) < 1:
        seed_name = seed_key.replace("_", " ")
        return {"message": f"❌ У вас нет {seed_name}. Купить: /buy {seed_key}", "success": False}

    # Check max seeds (10k limit)
    total_seeds = sum(inv.get(s, 0) for s in SEED_TYPES)
    if total_seeds >= MAX_SEEDS:
        return {"message": f"❌ Максимум семян: {MAX_SEEDS}. Используйте /farm.", "success": False}

    # Cooldown check
    now = datetime.utcnow()
    async with async_session() as s:
        cd = await s.get(Cooldown, user_id)
        if not cd:
            cd = Cooldown(user_id=user_id)
            s.add(cd)
            await s.commit()

        if cd.last_farm and cd.last_farm > now - timedelta(minutes=10):
            remaining = int((cd.last_farm + timedelta(minutes=10) - now).total_seconds())
            m, sec = divmod(remaining, 60)
            return {"message": f"⏳ Farm будет доступен через {m}м {sec}с.", "success": False}

        cd.last_farm = now
        await s.commit()

    # Consume seed
    await remove_materials(user_id, seed_key, 1)

    msg = "🌾 <b>Ферма</b>\n\n"
    crops_gained = {}
    seeds_gained = {}

    if seed_key == "seed":
        # Normal seed: 2-3 random crops from available pool
        crop_pool = _crops_for_area(user.area)
        num_crops = random.randint(2, 3)
        for _ in range(num_crops):
            crop = random.choice(crop_pool)
            crops_gained[crop] = crops_gained.get(crop, 0) + 1

        # 4% chance to get 4-5 seeds back
        if random.random() < 0.04:
            seed_back = random.randint(4, 5)
            seeds_gained[seed_key] = seed_back
    else:
        # Specific seed: 5-7 of that crop
        crop_map = {
            "potato_seed": "potato",
            "carrot_seed": "carrot",
            "bread_seed": "bread",
        }
        crop = crop_map[seed_key]
        amt = random.randint(5, 7)
        crops_gained[crop] = amt

        # 75% chance to get 1-2 seeds back
        if random.random() < 0.75:
            seed_back = random.randint(1, 2)
            seeds_gained[seed_key] = seed_back

    # Give crops
    for crop, amt in crops_gained.items():
        await add_materials(user_id, crop, amt)
        emoji = CROP_EMOJIS.get(crop, "•")
        msg += f"  {emoji} +{amt} {crop}\n"

    # Give seeds back
    for seed, amt in seeds_gained.items():
        await add_materials(user_id, seed, amt)
        emoji = SEED_EMOJIS.get(seed, "🌱")
        msg += f"  {emoji} +{amt} {seed.replace('_', ' ')}\n"

    # XP reward
    xp = random.randint(10 * user.area, 20 * user.area)
    xp_result = await add_xp(user_id, xp)

    msg += f"\n  ⚔️ +{xp} XP"
    if xp_result.get("leveled_up"):
        msg += f"\n\n🎉 Level up! Level {xp_result['new_level']}"

    total_items = sum(crops_gained.values()) + sum(seeds_gained.values())
    msg += f"\n\nВсего: {total_items} предметов"

    return {"message": msg, "success": True, "xp": xp}


def _crops_for_area(area: int) -> list:
    """Return list of crop types available at given area."""
    crops = ["potato", "apple"]
    if area >= 3:
        crops.append("banana")
    if area >= 5:
        crops.append("carrot")
    if area >= 7:
        crops.append("bread")
    return crops
