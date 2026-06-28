"""
Enchant system — enchant weapons and armor for percentage stat boosts.
Original EPIC RPG enchant table. Requires Area 2+.

Wiki formulas:
- Cost = max_area * command_multiplier * tt_enchant_multiplier
- TT enchant multiplier = 1 + tt_count * 0.2 (per config.TT_ENCHANT_BONUS_PER_TT)
- Horse tier 8+ = better enchant chances
- Enchanter 101+: 2% + log10(level-100)*2% chance to get coins back
- Master key part C drop chance (higher with better commands and TT)
"""
import random
import math
from database.crud import get_user, get_equipment, set_equipment, add_profession_xp, get_profession_bonus, add_materials
from game.player import remove_coins, add_coins
import config


# Enchant tiers with unlock requirements
ENCHANT_TABLE = [
    {"name": "NORMIE",      "bonus_pct": 5,    "tt_req": 0},
    {"name": "GOOD",        "bonus_pct": 15,   "tt_req": 0},
    {"name": "GREAT",       "bonus_pct": 25,   "tt_req": 0},
    {"name": "MEGA",        "bonus_pct": 40,   "tt_req": 0},
    {"name": "EPIC",        "bonus_pct": 60,   "tt_req": 0},
    {"name": "HYPER",       "bonus_pct": 70,   "tt_req": 0},
    {"name": "ULTIMATE",    "bonus_pct": 80,   "tt_req": 0},
    {"name": "PERFECT",     "bonus_pct": 90,   "tt_req": 0},
    {"name": "EDGY",        "bonus_pct": 95,   "tt_req": 0},
    {"name": "ULTRA-EDGY",  "bonus_pct": 100,  "tt_req": 0},
    {"name": "OMEGA",       "bonus_pct": 125,  "tt_req": 1},
    {"name": "ULTRA-OMEGA", "bonus_pct": 150,  "tt_req": 3},
    {"name": "GODLY",       "bonus_pct": 200,  "tt_req": 5},
    {"name": "VOID",        "bonus_pct": 300,  "tt_req": 15},
    {"name": "ETERNAL",     "bonus_pct": 305,  "tt_req": 150},
]

# Chances for each enchant tier (before modifiers)
ENCHANT_CHANCES = [
    0.25,  # NORMIE
    0.20,  # GOOD
    0.17,  # GREAT
    0.13,  # MEGA
    0.10,  # EPIC
    0.06,  # HYPER
    0.04,  # ULTIMATE
    0.025, # PERFECT
    0.012, # EDGY
    0.005, # ULTRA-EDGY
    0.003, # OMEGA
    0.0015,# ULTRA-OMEGA
    0.0008,# GODLY
    0.0004,# VOID
    0.0001,# ETERNAL
]

ENCHANT_COST = 500

# Enchanter XP per enchant level (wiki)
ENCHANTER_XP = {
    "NORMIE": 0, "GOOD": 1, "GREAT": 2, "MEGA": 3, "EPIC": 4,
    "HYPER": 5, "ULTIMATE": 6, "PERFECT": 7, "EDGY": 8, "ULTRA-EDGY": 9,
    "OMEGA": 10, "ULTRA-OMEGA": 11, "GODLY": 12, "VOID": 13, "ETERNAL": 14,
}

# Command cost/XP multipliers (wiki)
ENCHANT_CMD_MULTIPLIER = {
    "enchant": 1,
    "refine": 10,
    "transmute": 100,
    "transcend": 1000,
}


def get_available_enchants(tt_count: int) -> list:
    """Return enchants available for this player's TT count."""
    return [e for e in ENCHANT_TABLE if tt_count >= e["tt_req"]]


def roll_enchant(tt_count: int, enchanter_level: int = 1, horse_tier: int = 0) -> dict:
    """Roll an enchantment based on available pool, enchanter bonus, and TT/horse boost."""
    available = get_available_enchants(tt_count)
    available_count = len(available)

    # Take chances only for available enchants
    chances = list(ENCHANT_CHANCES[:available_count])

    # TT enchant chance boost: +20% per TT shifts probability upward
    tt_boost = tt_count * 0.02  # 2% per TT
    if available_count > 1:
        # Shift from worst to best proportionally
        shift = min(tt_boost, chances[0] * 0.9)
        chances[0] -= shift
        chances[-1] += shift

    # Horse tier 8+ = better enchant chances (wiki)
    if horse_tier >= 8:
        horse_boost = 0.05 if horse_tier >= 10 else 0.03 if horse_tier >= 9 else 0.02
        if available_count > 1:
            shift = min(horse_boost, chances[0] * 0.9)
            chances[0] -= shift
            chances[-1] += shift

    # Enchanter profession bonus: shift 1% from worst to best per 10 levels
    bonus_per = min(enchanter_level // 10, 5) * 0.01
    if available_count > 1 and bonus_per > 0:
        chances[0] = max(chances[0] - bonus_per, 0.01)
        chances[-1] += bonus_per

    # Normalize
    total = sum(chances)
    chances = [c / total for c in chances]

    roll = random.random()
    cumulative = 0
    for i, ench in enumerate(available):
        cumulative += chances[i]
        if roll < cumulative:
            return ench

    return available[0]  # fallback


async def enchant(user_id: int, slot: str) -> dict:
    """Enchant weapon or armor. slot = 'sword' or 'armor'."""
    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    if user.area < 2:
        return {"success": False, "message": "❌ Enchant доступен с Area 2."}

    if slot not in ("sword", "armor"):
        return {"success": False, "message": "❌ Используй: enchant sword или enchant armor"}

    # Wiki: cost = max_area * command_multiplier * tt_enchant_mult
    # For basic enchant, command_multiplier = 1
    tt_enchant_mult = 1 + user.tt_count * config.TT_ENCHANT_BONUS_PER_TT
    cost = int(user.area * 1 * tt_enchant_mult)

    if user.coins < cost:
        return {"success": False, "message": f"❌ Нужно {cost:,} монет. У тебя {user.coins:,}."}

    await remove_coins(user_id, cost)

    # Get enchanter bonus and horse tier
    prof_bonus = await get_profession_bonus(user_id, "enchanter")
    enchanter_level = prof_bonus.get("level", 1)
    from game.horses import _get_horse_tier
    horse_tier = await _get_horse_tier(user_id)

    ench = roll_enchant(user.tt_count, enchanter_level, horse_tier)

    eq = await get_equipment(user_id)
    enchant_key = f"{slot}_enchant"
    new_enchant = {"name": ench["name"], "bonus_pct": ench["bonus_pct"]}
    eq[enchant_key] = new_enchant
    await set_equipment(user_id, eq)

    ench_xp = ENCHANTER_XP.get(ench["name"], 0)
    await add_profession_xp(user_id, "enchanter", ench_xp)

    # Master key part C drop chance
    master_key_mult = 1 + user.tt_count * 0.1  # +10% per TT
    if random.random() < 0.001 * master_key_mult:
        await add_materials(user_id, "master_key_c", 1)
        msg_append = "\n🔑 Вы нашли Master Key Part C!"
    else:
        msg_append = ""

    # Level 101+ enchanter: chance to get coins back (wiki: 2% base + log10(level-100)*2%)
    coins_refund = 0
    if enchanter_level > 100:
        refund_chance = 0.02 + math.log10(enchanter_level - 100) * 0.02
        refund_chance = min(refund_chance, 0.10)  # cap at 10%
        if random.random() < refund_chance:
            coins_refund = cost
            await add_coins(user_id, coins_refund)

    stat = "AT" if slot == "sword" else "DEF"
    slot_name = "sword" if slot == "sword" else "armor"
    msg = (
        f"✨ <b>Enchant</b>\n\n"
        f"Your {slot_name} has been enchanted!\n"
        f"You got: <b>{ench['name']}</b>\n"
        f"+{ench['bonus_pct']}% {stat}\n"
        f"(-{cost:,} coins)"
    )

    if coins_refund > 0:
        msg += f"\n\n💰 Enchanter level 100 bonus! Refunded {coins_refund:,} coins"
    msg += msg_append

    return {"success": True, "message": msg}


async def refine(user_id: int, slot: str) -> dict:
    """Refine — better chances but x10 cost. Unlocked in Area 7."""
    return await _enhanced_enchant(user_id, slot, cost_mult=10, min_area=7, name="Refine")


async def transmute(user_id: int, slot: str) -> dict:
    """Transmute — better chances but x100 cost. Unlocked in Area 13."""
    return await _enhanced_enchant(user_id, slot, cost_mult=100, min_area=13, name="Transmute")


async def transcend(user_id: int, slot: str) -> dict:
    """Transcend — better chances but x1000 cost. Unlocked in Area 15."""
    return await _enhanced_enchant(user_id, slot, cost_mult=1000, min_area=15, name="Transcend")


async def _enhanced_enchant(user_id: int, slot: str, cost_mult: int, min_area: int, name: str) -> dict:
    """Enhanced enchant with better odds but higher cost."""
    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    # Ascended players can use higher tier enchanting commands
    if not getattr(user, 'ascended', False) and user.area < min_area:
        return {"success": False, "message": f"❌ {name} доступен с Area {min_area}."}

    if slot not in ("sword", "armor"):
        return {"success": False, "message": f"❌ Используй: {name.lower()} sword или {name.lower()} armor"}

    # Wiki: cost = max_area * command_multiplier * tt_enchant_mult
    tt_enchant_mult = 1 + user.tt_count * config.TT_ENCHANT_BONUS_PER_TT
    cost = int(user.area * cost_mult * tt_enchant_mult)

    if user.coins < cost:
        return {"success": False, "message": f"❌ Нужно {cost:,} монет. У тебя {user.coins:,}."}

    await remove_coins(user_id, cost)

    prof_bonus = await get_profession_bonus(user_id, "enchanter")
    enchanter_level = prof_bonus.get("level", 1)

    from game.horses import _get_horse_tier
    horse_tier = await _get_horse_tier(user_id)

    # Enhanced roll: remove NORMIE and GOOD from pool, boost higher tiers
    available = get_available_enchants(user.tt_count)
    # Remove the two worst enchants for enhanced methods
    if cost_mult >= 100:
        available = available[2:]  # Remove NORMIE, GOOD
    elif cost_mult >= 10:
        available = available[1:]  # Remove NORMIE

    if not available:
        available = get_available_enchants(user.tt_count)

    # Take corresponding chances
    start_idx = len(ENCHANT_TABLE) - len(available)
    chances = list(ENCHANT_CHANCES[start_idx:start_idx + len(available)])

    # TT enchant chance boost
    tt_boost = user.tt_count * 0.02
    if len(chances) > 1:
        shift = min(tt_boost, chances[0] * 0.9)
        chances[0] -= shift
        chances[-1] += shift

    # Horse tier 8+ = better enchant chances
    if horse_tier >= 8:
        horse_boost = 0.05 if horse_tier >= 10 else 0.03 if horse_tier >= 9 else 0.02
        if len(chances) > 1:
            shift = min(horse_boost, chances[0] * 0.9)
            chances[0] -= shift
            chances[-1] += shift

    # Enchanter bonus
    bonus_per = min(enchanter_level // 10, 5) * 0.01
    if len(chances) > 1 and bonus_per > 0:
        chances[0] = max(chances[0] - bonus_per, 0.01)
        chances[-1] += bonus_per

    total = sum(chances)
    chances = [c / total for c in chances]

    roll = random.random()
    cumulative = 0
    ench = available[0]
    for i, e in enumerate(available):
        cumulative += chances[i]
        if roll < cumulative:
            ench = e
            break

    eq = await get_equipment(user_id)
    enchant_key = f"{slot}_enchant"
    eq[enchant_key] = {"name": ench["name"], "bonus_pct": ench["bonus_pct"]}
    await set_equipment(user_id, eq)

    # Enchanter XP: base XP * command multiplier (wiki)
    ench_xp = ENCHANTER_XP.get(ench["name"], 0) * cost_mult
    await add_profession_xp(user_id, "enchanter", ench_xp)

    # Master key part C drop chance
    master_key_mult = 1 + user.tt_count * 0.1
    if random.random() < 0.001 * master_key_mult * cost_mult:
        await add_materials(user_id, "master_key_c", 1)
        msg_append = "\n🔑 Вы нашли Master Key Part C!"
    else:
        msg_append = ""

    # Level 101+ enchanter: chance to get coins back
    coins_refund = 0
    if enchanter_level > 100:
        refund_chance = 0.02 + math.log10(enchanter_level - 100) * 0.02
        refund_chance = min(refund_chance, 0.10)
        if random.random() < refund_chance:
            coins_refund = cost
            await add_coins(user_id, coins_refund)

    stat = "AT" if slot == "sword" else "DEF"
    slot_name = "sword" if slot == "sword" else "armor"
    msg = (
        f"✨ <b>{name}</b>\n\n"
        f"Your {slot_name} has been enchanted!\n"
        f"You got: <b>{ench['name']}</b>\n"
        f"+{ench['bonus_pct']}% {stat}\n"
        f"(-{cost:,} coins)"
    )

    if coins_refund > 0:
        msg += f"\n\n💰 Enchanter level 100 bonus! Refunded {coins_refund:,} coins"
    msg += msg_append

    return {"success": True, "message": msg}
