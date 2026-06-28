"""
Gathering logic: chop (logs), pickup (fruits), mine (ruby + coins).
Each action gives main resources based on area + tool tier.
Probabilities and amounts per wiki.
Worker XP per wiki: Chop 4, Axe 8, Bowsaw 12, Chainsaw 16,
Fish 4, Net 9, Boat 13, Bigboat 18,
Pickup 4, Ladder 8, Tractor 12, Greenhouse 17,
Mine 4, Pickaxe 8, Drill 12, Dynamite 17.
"""
import random
import json
import config
from database.crud import add_materials, get_user, get_tools, add_profession_xp
from game.player import add_coins

# Worker XP per command (wiki)
WORKER_XP = {
    "chop": 4, "axe": 8, "bowsaw": 12, "chainsaw": 16,
    "fish": 4, "net": 9, "boat": 13, "bigboat": 18,
    "pickup": 4, "ladder": 8, "tractor": 12, "greenhouse": 17,
    "mine": 4, "pickaxe": 8, "drill": 12, "dynamite": 17,
}


async def chop(user_id: int, cmd: str = "chop") -> dict:
    """Chop wood. Gives logs based on area, axe gives more."""
    user = await get_user(user_id)
    if not user:
        return {"message": "Игрок не найден.", "success": False}

    tools = await get_tools(user_id)
    axe_level = tools.get("axe", 1)

    results = {}

    # Wooden logs: always available, 70% base chance
    if random.random() < 0.70:
        amt = _roll_chop_amount("wooden_log", axe_level)
        results["wooden_log"] = results.get("wooden_log", 0) + amt

    # Epic log: area 1+ (30% area 1, 22% area 2+)
    epic_chance = 0.30 if user.area == 1 else 0.22
    if random.random() < epic_chance:
        amt = _roll_chop_amount("epic_log", axe_level)
        results["epic_log"] = results.get("epic_log", 0) + amt

    # Super log: area 2+ (8% area 2-3, 7% area 4+)
    if user.area >= 2:
        super_chance = 0.08 if user.area <= 3 else 0.07
        if random.random() < super_chance:
            amt = _roll_chop_amount("super_log", axe_level)
            results["super_log"] = results.get("super_log", 0) + amt

    # Mega log: area 4+ (1% area 4-5, 0.7% area 6+)
    if user.area >= 4:
        mega_chance = 0.01 if user.area <= 5 else 0.007
        if random.random() < mega_chance:
            results["mega_log"] = results.get("mega_log", 0) + 1

    # Hyper log: area 6+ (0.3% area 6-8, 0.26% area 9+)
    if user.area >= 6:
        hyper_chance = 0.003 if user.area <= 8 else 0.0026
        if random.random() < hyper_chance:
            results["hyper_log"] = results.get("hyper_log", 0) + 1

    # Ultra log: area 9+ (0.04%)
    if user.area >= 9 and random.random() < 0.0004:
        results["ultra_log"] = results.get("ultra_log", 0) + 1

    # Ultimate log: area 9+ (very rare)
    if user.area >= 9 and random.random() < 0.0001:
        results["ultimate_log"] = results.get("ultimate_log", 0) + 1

    if not results:
        # Guarantee at least wooden log
        results["wooden_log"] = 1

    for mat, amt in results.items():
        await add_materials(user_id, mat, amt)

    names = {
        "wooden_log": "Wooden log", "epic_log": "EPIC log", "super_log": "SUPER log",
        "mega_log": "MEGA log", "hyper_log": "HYPER log", "ultra_log": "ULTRA log",
        "ultimate_log": "ULTIMATE log",
    }
    emojis = {
        "wooden_log": "🪵", "epic_log": "🪵", "super_log": "🪵",
        "mega_log": "🪵", "hyper_log": "🪵", "ultra_log": "🪵",
        "ultimate_log": "🪵",
    }
    msg = "\n".join(f"{emojis.get(m, '🪵')} +{amt} {names.get(m, m)}" for m, amt in results.items())

    # Smol coin drops during Returning Event
    from database.crud import has_active_returning_event
    if await has_active_returning_event(user_id):
        smol_lo, smol_hi = config.RETURNING_SMOL_PER_ACTION
        smol = random.randint(smol_lo, smol_hi)
        await add_materials(user_id, "smol_coin", smol)
        from game.returning import track_smol_coins
        await track_smol_coins(user_id, smol)
        msg += f"\n🪙 +{smol} smol coins"

    from database.crud import add_profession_xp
    await add_profession_xp(user_id, "worker", WORKER_XP.get(cmd, 4))
    return {"message": msg, "success": True}


def _roll_chop_amount(log_tier: str, axe_level: int) -> int:
    """Roll chop amount per wiki base amounts + tool bonus."""
    base = {
        "wooden_log": (1, 2),
        "epic_log": (1, 2),
        "super_log": (1, 1),
        "mega_log": (1, 1),
        "hyper_log": (1, 1),
        "ultra_log": (1, 1),
        "ultimate_log": (1, 1),
    }
    mn, mx = base.get(log_tier, (1, 1))
    # Higher axe tiers: 3→6 (chop), 6→10 (bowsaw), 8→15 (chainsaw)
    # Simplified: +1 per axe level above 1
    bonus = max(0, axe_level - 1)
    return random.randint(mn, mx) + bonus


async def pickup(user_id: int, cmd: str = "pickup") -> dict:
    """Pickup fruits: apple, banana, Watermelon. Requires Area 3+."""
    user = await get_user(user_id)
    if not user:
        return {"message": "Игрок не найден.", "success": False}
    if user.area < 3:
        return {"message": "❌ Pickup доступен с Area 3.", "success": False}

    tools = await get_tools(user_id)
    ladder_level = tools.get("ladder", 1)

    results = {}

    # Apple: 75% base chance
    if random.random() < 0.75:
        amt = _roll_pickup_amount("apple", ladder_level)
        results["apple"] = results.get("apple", 0) + amt

    # Banana: 25% base chance (from area 3+, better areas have more)
    banana_chance = 0.25
    if random.random() < banana_chance:
        amt = _roll_pickup_amount("banana", ladder_level)
        results["banana"] = results.get("banana", 0) + amt

    # Watermelon: very rare, area 7+
    if user.area >= 7 and random.random() < 0.03:
        amt = _roll_pickup_amount("Watermelon", ladder_level)
        results["Watermelon"] = results.get("Watermelon", 0) + amt

    if not results:
        results["apple"] = 1

    for mat, amt in results.items():
        await add_materials(user_id, mat, amt)

    names = {"apple": "Apple", "banana": "Banana", "Watermelon": "Watermelon"}
    emojis = {"apple": "🍎", "banana": "🍌", "Watermelon": "🍉"}
    msg = "\n".join(f"{emojis.get(m, '🍎')} +{amt} {names.get(m, m)}" for m, amt in results.items())

    # Smol coin drops during Returning Event
    from database.crud import has_active_returning_event
    if await has_active_returning_event(user_id):
        smol_lo, smol_hi = config.RETURNING_SMOL_PER_ACTION
        smol = random.randint(smol_lo, smol_hi)
        await add_materials(user_id, "smol_coin", smol)
        from game.returning import track_smol_coins
        await track_smol_coins(user_id, smol)
        msg += f"\n🪙 +{smol} smol coins"

    from database.crud import add_profession_xp
    await add_profession_xp(user_id, "worker", WORKER_XP.get(cmd, 4))
    return {"message": msg, "success": True}


def _roll_pickup_amount(fruit: str, ladder_level: int) -> int:
    """Roll pickup amount per wiki base amounts + tool bonus."""
    base = {"apple": (1, 2), "banana": (1, 1), "Watermelon": (1, 1)}
    mn, mx = base.get(fruit, (1, 1))
    bonus = max(0, ladder_level - 1)
    return random.randint(mn, mx) + bonus


async def fish(user_id: int, cmd: str = "fish") -> dict:
    """Fish for fish. Gives normie/golden/epic/super fish based on area."""
    user = await get_user(user_id)
    if not user:
        return {"message": "Игрок не найден.", "success": False}

    tools = await get_tools(user_id)
    rod_level = tools.get("rod", 1)

    results = {}

    # Normie fish: 72% always
    if random.random() < 0.72:
        amt = _roll_fish_amount("normie_fish", rod_level)
        results["normie_fish"] = results.get("normie_fish", 0) + amt

    # Golden fish: area 1 (28%), area 2+ (27.7% base, slightly lower with higher tools)
    if user.area == 1:
        golden_chance = 0.28
    else:
        golden_chance = max(0.268, 0.277 - rod_level * 0.003)
    if random.random() < golden_chance:
        amt = _roll_fish_amount("golden_fish", rod_level)
        results["golden_fish"] = results.get("golden_fish", 0) + amt

    # Epic fish: area 2+ (0.3% fish, 0.6% net, 0.9% boat, 1.2% bigboat)
    epic_chances = {1: 0.003, 2: 0.003, 3: 0.006, 4: 0.009}
    epic_chance = epic_chances.get(min(rod_level, 4), 0.012)
    if user.area >= 2 and random.random() < epic_chance:
        results["epic_fish"] = results.get("epic_fish", 0) + 1

    # Super fish: area 2+ (very rare)
    if user.area >= 2 and random.random() < 0.001:
        results["super_fish"] = results.get("super_fish", 0) + 1

    if not results:
        results["normie_fish"] = 1

    for mat, amt in results.items():
        await add_materials(user_id, mat, amt)

    names = {
        "normie_fish": "Normie Fish", "golden_fish": "Golden Fish",
        "epic_fish": "EPIC Fish", "super_fish": "SUPER Fish",
    }
    msg = "\n".join(f"🐟 +{amt} {names.get(m, m)}" for m, amt in results.items())

    # Smol coin drops during Returning Event
    from database.crud import has_active_returning_event
    if await has_active_returning_event(user_id):
        smol_lo, smol_hi = config.RETURNING_SMOL_PER_ACTION
        smol = random.randint(smol_lo, smol_hi)
        await add_materials(user_id, "smol_coin", smol)
        from game.returning import track_smol_coins
        await track_smol_coins(user_id, smol)
        msg += f"\n🪙 +{smol} smol coins"

    from database.crud import add_profession_xp
    await add_profession_xp(user_id, "worker", WORKER_XP.get(cmd, 4))
    return {"message": msg, "success": True}


def _roll_fish_amount(fish_tier: str, rod_level: int) -> int:
    """Roll fish amount per wiki base amounts + tool bonus."""
    base = {
        "normie_fish": (1, 3),
        "golden_fish": (1, 2),
        "epic_fish": (1, 1),
        "super_fish": (1, 1),
    }
    mn, mx = base.get(fish_tier, (1, 1))
    bonus = max(0, rod_level - 1)
    return random.randint(mn, mx) + bonus


async def mine(user_id: int, cmd: str = "mine") -> dict:
    """Mine ruby + coins. Requires Area 5+."""
    user = await get_user(user_id)
    if not user:
        return {"message": "Игрок не найден.", "success": False}
    if user.area < 5:
        return {"message": "❌ Mine доступен с Area 5.", "success": False}

    tools = await get_tools(user_id)
    pickaxe_level = tools.get("pickaxe", 1)

    # Coin base amounts per tool tier (wiki)
    coin_bases = {1: 1000, 2: 5000, 3: 7500, 4: 10000}
    ruby_chances = {1: 0.0667, 2: 0.1333, 3: 0.2667, 4: 0.40}

    coin_base = coin_bases.get(pickaxe_level, 1000)
    ruby_chance = ruby_chances.get(pickaxe_level, 0.0667)

    # Coins: 70%-130% range of base * max_area
    coin_amount = int(coin_base * user.area * random.uniform(0.70, 1.30))

    roll = random.random()
    if roll < (1 - ruby_chance):
        await add_coins(user_id, coin_amount)
        msg = f"⛏️ +{coin_amount:,} coins"
    elif roll < 1.0:
        await add_materials(user_id, "ruby", 1)
        await add_coins(user_id, coin_amount)
        msg = f"⛏️ +{coin_amount:,} coins\n💎 +1 ruby"

    # Smol coin drops during Returning Event
    from database.crud import has_active_returning_event
    if await has_active_returning_event(user_id):
        smol_lo, smol_hi = config.RETURNING_SMOL_PER_ACTION
        smol = random.randint(smol_lo, smol_hi)
        await add_materials(user_id, "smol_coin", smol)
        from game.returning import track_smol_coins
        await track_smol_coins(user_id, smol)
        msg += f"\n🪙 +{smol} smol coins"

    from database.crud import add_profession_xp
    await add_profession_xp(user_id, "worker", WORKER_XP.get(cmd, 4))
    return {"message": msg, "success": True}
