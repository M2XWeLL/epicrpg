"""
Horse system — types, tiers, levels, breeding, training, races, epicness.
Per wiki: 10 tiers, breeding chances, fail boost mechanics, training cost formula.
"""
import random
import json
import math
from datetime import datetime, timedelta

DATA_DIR = None  # Set at import time


def _init_data_dir():
    global DATA_DIR
    if DATA_DIR is None:
        import config
        DATA_DIR = config.DATA_DIR


def _load() -> dict:
    _init_data_dir()
    with open(DATA_DIR / "horses.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_horse_types() -> dict:
    return _load()["types"]


def get_tier_max_level(tier: int, lootboxer_level: int = 1) -> int:
    """Max level = (tier * 10) + max(0, lootboxer_level - 100)"""
    base = tier * 10
    bonus = max(0, lootboxer_level - 100)
    return base + bonus


def get_training_cost(horse_level: int, lootboxer_level: int = 1) -> int:
    """Training cost formula from wiki:
    round((n^4 * (n^2 + 210*n + 2200) * (500 - l^1.2)) / 100000)
    n = horse level, l = lootboxer profession level
    """
    n = horse_level
    l = lootboxer_level
    cost = (n**4 * (n**2 + 210 * n + 2200) * (500 - l**1.2)) / 100000
    return max(1, round(cost))


def get_breeding_chance(tier: int) -> float:
    """Base chance to tier up per wiki table."""
    data = _load()
    return data.get("tier_breeding_chance", {}).get(str(tier), 0)


def get_breeding_guarantee(tier: int) -> int:
    """Max breed attempts before guaranteed tier up."""
    data = _load()
    return data.get("tier_breeding_guarantee", {}).get(str(tier), 1000)


def calc_breeding_chance(tier: int, fail_count: int, tt_count: int = 0) -> float:
    """Calculate breeding chance with fail boost and TT bonus.

    Fail boost mechanics:
    - 0-25% of max fails: no boost
    - 25-50%: x1.25 (tier 8+)
    - 50-75%: x2 (tier 6+)
    - 75-100%: x5 (tier 4+)
    - 100%: guaranteed
    """
    guarantee = get_breeding_guarantee(tier)
    base = get_breeding_chance(tier)

    if fail_count >= guarantee:
        return 1.0

    fail_pct = fail_count / guarantee if guarantee > 0 else 0
    boost = 1.0

    if fail_pct >= 0.75 and tier >= 4:
        boost = 5.0
    elif fail_pct >= 0.50 and tier >= 6:
        boost = 2.0
    elif fail_pct >= 0.25 and tier >= 8:
        boost = 1.25

    # TT bonus (unknown exact formula, using small %)
    tt_bonus = tt_count * 0.001

    chance = base * boost + tt_bonus
    return min(chance, 1.0)


def calc_horse_boost(horse) -> dict:
    """Calculate all active boosts from horse type, tier, level."""
    data = _load()
    types = data["types"]
    tier_boosts = data["tier_boosts"]

    t = types.get(horse.horse_type, types["normal"])
    tier_data = tier_boosts.get(str(horse.tier), {})

    boosts = {}

    # Type boost: pct_per_level * horse_level
    boost_stat = t.get("boost_stat")
    pct_table = t.get("boost_pct_per_level", {})
    if boost_stat and pct_table:
        pct = pct_table.get(str(horse.tier), 0)
        total_boost = pct * horse.level  # e.g., 0.2% * level = total %
        boosts[boost_stat] = total_boost

    # Tier boosts
    if tier_data.get("daily_weekly"):
        boosts["daily_weekly"] = tier_data["daily_weekly"]
    if tier_data.get("immortality"):
        boosts["immortality"] = True
    if tier_data.get("lootbox"):
        boosts["lootbox_mult"] = tier_data["lootbox"]
    if tier_data.get("no_key"):
        boosts["no_key"] = True
    if tier_data.get("monster_item"):
        boosts["monster_item_mult"] = tier_data["monster_item"]
    if tier_data.get("better_enchant"):
        boosts["better_enchant"] = True
    if tier_data.get("pet_chance"):
        boosts["pet_chance_mult"] = tier_data["pet_chance"]
    if tier_data.get("multi_drop"):
        boosts["multi_drop"] = True
    if tier_data.get("badge_slots"):
        boosts["badge_slots"] = tier_data["badge_slots"]
    if tier_data.get("race"):
        boosts["can_race"] = True

    return boosts


def format_horse_info(horse, lootboxer_level: int = 1) -> str:
    """Format horse info for display."""
    data = _load()
    types = data["types"]
    max_level = get_tier_max_level(horse.tier, lootboxer_level)
    t = types.get(horse.horse_type, types["normal"])
    boosts = calc_horse_boost(horse)

    text = (
        f"{t['emoji']} <b>{horse.name}</b>\n\n"
        f"Тип: {t['name']}\n"
        f"Тир: {_tier_roman(horse.tier)}\n"
        f"Уровень: {horse.level}/{max_level}\n"
        f"EPICness: {horse.epicness}/99\n"
        f"Fail count: {horse.fail_count}\n"
    )

    # Next training cost
    cost = get_training_cost(horse.level, lootboxer_level)
    text += f"\nТренировка: {cost:,} монет\n"

    # Active boosts
    if boosts:
        text += "\n<b>Бусты:</b>\n"
        stat_names = {
            "def": "DEF", "atk": "ATK", "hp": "LIFE", "coins": "COINS",
            "enchant": "ENCHANT", "events": "EVENTS", "quest": "QUEST",
        }
        for stat, val in boosts.items():
            if stat in stat_names:
                text += f"  {stat_names[stat]}: +{val:.1f}%\n"
            elif stat == "daily_weekly":
                text += f"  Daily/Weekly: +{val*100:.0f}%\n"
            elif stat == "immortality":
                text += "  Immortality: ✅\n"
            elif stat == "lootbox_mult":
                text += f"  Lootbox chance: x{val}\n"
            elif stat == "no_key":
                text += "  No dungeon key: ✅\n"
            elif stat == "monster_item_mult":
                text += f"  Monster item: x{val}\n"
            elif stat == "better_enchant":
                text += "  Better enchantments: ✅\n"
            elif stat == "pet_chance_mult":
                text += f"  Pet chance: x{val}\n"
            elif stat == "multi_drop":
                text += "  Multi drop: ✅\n"
            elif stat == "badge_slots":
                text += f"  Extra badge slots: +{val}\n"
            elif stat == "can_race":
                text += "  Horse race: ✅\n"

    text += (
        "\n<b>Команды:</b>\n"
        "  /horse training — Тренировка\n"
        "  /horse breeding @player — Разведение\n"
        "  /horse race — Гонки (тир V+)\n"
        "  /horse feed — Покормить морковью\n"
    )
    return text


def _tier_roman(tier: int) -> str:
    romans = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
              6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X"}
    return romans.get(tier, str(tier))


# Horse type probabilities for breeding (all equal except special/super_special)
BREEDING_TYPES = [
    "normal", "defender", "strong", "tank", "golden", "magic", "festive",
]
SPECIAL_CHANCE = 0.05  # Special has lower chance
SUPER_SPECIAL_REQUIRES_SPECIAL = True  # Must breed two specials


def roll_horse_type(parent1_type: str, parent2_type: str) -> str:
    """Roll new horse type during breeding."""
    # Super Special only from two Special parents
    if parent1_type == "special" and parent2_type == "special":
        if random.random() < 0.10:  # 10% chance
            return "super_special"

    # Special has 5% chance
    if random.random() < SPECIAL_CHANCE:
        return "special"

    return random.choice(BREEDING_TYPES)


async def horse_training(user_id: int) -> dict:
    """Train horse. Uses wiki formula for cost."""
    from database.engine import async_session
    from database.models import Horse, User, Profession
    from database.crud import get_user

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    # Get lootboxer level
    async with async_session() as s:
        prof = await s.get(Profession, user_id)
        lootboxer_level = prof.lootboxer_level if prof else 1

    async with async_session() as s:
        horse = await s.get(Horse, user_id)
        if not horse:
            return {"success": False, "message": "❌ У вас нет лошади. Купить: /horse buy"}

        max_level = get_tier_max_level(horse.tier, lootboxer_level)
        if horse.level >= max_level:
            return {"success": False, "message": f"❌ Лошадь максимального уровня ({max_level}). Разводите для тира выше!"}

        cost = get_training_cost(horse.level, lootboxer_level)
        if user.coins < cost:
            return {"success": False, "message": f"❌ Нужно {cost:,} монет."}

        # Deduct coins
        u = await s.get(User, user_id)
        u.coins -= cost

        # Level up directly (wiki: training increases level, not XP-based)
        horse.level += 1
        await s.commit()

        return {
            "success": True,
            "message": (
                f"🐴 <b>Тренировка</b>\n\n"
                f"{horse.name} повышен до уровня {horse.level}/{max_level}!\n"
                f"(-{cost:,} монет)"
            ),
        }


async def horse_feed(user_id: int) -> dict:
    """Feed horse a carrot to change its name."""
    from database.crud import get_inventory, remove_materials, get_user
    from database.engine import async_session
    from database.models import Horse

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    inv = await get_inventory(user_id)
    if inv.get("carrot", 0) < 1:
        return {"success": False, "message": "❌ Нужна 1 carrot. Добыть: /farm"}

    async with async_session() as s:
        horse = await s.get(Horse, user_id)
        if not horse:
            return {"success": False, "message": "❌ У вас нет лошади."}

        await remove_materials(user_id, "carrot", 1)

        names = [
            "Thunder", "Storm", "Blaze", "Shadow", "Luna", "Star", "Fire",
            "Diamond", "Rex", "Max", "Buddy", "Lucky", "Happy", "Sunny",
            "Rocket", "Prince", "King", "Queen", "Beauty", "Champion",
            "Bolt", "Flash", "Rapid", "Swift", "Arrow", "Scout", "Ranger",
        ]
        new_name = random.choice(names)
        horse.name = new_name
        await s.commit()

    return {
        "success": True,
        "message": f"🥕 Лошадь названа: <b>{new_name}</b>!",
    }


async def horse_breeding(user_id: int, target_id: int) -> dict:
    """Breed two horses. Both must be same tier. Chance for tier up per wiki."""
    from database.engine import async_session
    from database.models import Horse, User
    from database.crud import get_user

    async with async_session() as s:
        horse1 = await s.get(Horse, user_id)
        horse2 = await s.get(Horse, target_id)

        if not horse1:
            return {"success": False, "message": "❌ У вас нет лошади."}
        if not horse2:
            return {"success": False, "message": "❌ У другого игрока нет лошади."}
        if horse1.tier != horse2.tier:
            return {"success": False, "message": "❌ Лошади должны быть одного тира."}
        if horse1.tier >= 10:
            return {"success": False, "message": "❌ Лошадь максимального тира."}

        # Wiki: shared 24h cooldown between breeding and race
        now = datetime.utcnow()
        last = horse1.last_breed_race
        if last and last.tzinfo is not None:
            last = last.replace(tzinfo=None)
        if last and (now - last).total_seconds() < 86400:
            remaining = int(86400 - (now - last).total_seconds())
            hours, rem = divmod(remaining, 3600)
            mins = rem // 60
            return {"success": False, "message": f"⏳ Разведение/гонки будут доступны через {hours}ч {mins}м."}

        user1 = await s.get(User, user_id)
        tt_count = user1.tt_count if user1 else 0

        # Calculate tier up chance with fail boost
        chance = calc_breeding_chance(horse1.tier, horse1.fail_count, tt_count)

        # Roll new horse type (horse_token preserves type)
        from database.crud import get_inventory
        inv = await get_inventory(user_id)
        if inv.get("horse_token", 0) > 0:
            new_type = horse1.horse_type  # Token preserves type
            from database.crud import remove_materials
            await remove_materials(user_id, "horse_token", 1)
        else:
            new_type = roll_horse_type(horse1.horse_type, horse2.horse_type)

        # New level = average of parents
        avg_level = (horse1.level + horse2.level) / 2
        new_level = int(avg_level) if random.random() < 0.5 else int(avg_level) + 1
        new_level = max(1, new_level)

        if random.random() < chance:
            # Success! Tier up
            old_tier = horse1.tier
            horse1.tier += 1
            horse1.level = new_level
            horse1.xp = 0
            horse1.fail_count = 0
            horse1.horse_type = new_type
            horse1.last_breed_race = datetime.utcnow()
            await s.commit()
            return {
                "success": True,
                "tier_up": True,
                "message": (
                    f"🐴 <b>Разведение УСПЕШНО!</b>\n\n"
                    f"{horse1.name} повысил тир: {_tier_roman(old_tier)} → {_tier_roman(horse1.tier)}!\n"
                    f"Тип: {new_type}\n"
                    f"Уровень: {new_level}"
                ),
            }
        else:
            # Fail
            horse1.fail_count += 1
            horse1.horse_type = new_type
            horse1.level = new_level
            horse1.last_breed_race = datetime.utcnow()
            await s.commit()

            guarantee = get_breeding_guarantee(horse1.tier)
            return {
                "success": True,
                "tier_up": False,
                "message": (
                    f"❌ <b>Разведение НЕ удалось</b>\n\n"
                    f"{horse1.name} остался на {_tier_roman(horse1.tier)}.\n"
                    f"Тип: {new_type}\n"
                    f"Уровень: {new_level}\n"
                    f"Fail count: {horse1.fail_count}/{guarantee}"
                ),
            }


async def horse_race(user_id: int) -> dict:
    """Join a horse race (requires tier V+). Race rewards per wiki table."""
    from database.engine import async_session
    from database.models import Horse

    async with async_session() as s:
        horse = await s.get(Horse, user_id)
        if not horse:
            return {"success": False, "message": "❌ У вас нет лошади."}
        if horse.tier < 5:
            return {"success": False, "message": "❌ Нужна лошадь Тир V+ для гонок."}

        # Wiki: shared 24h cooldown between breeding and race
        now = datetime.utcnow()
        last = horse.last_breed_race
        if last and last.tzinfo is not None:
            last = last.replace(tzinfo=None)
        if last and (now - last).total_seconds() < 86400:
            remaining = int(86400 - (now - last).total_seconds())
            hours, rem = divmod(remaining, 3600)
            mins = rem // 60
            return {"success": False, "message": f"⏳ Разведение/гонки будут доступны через {hours}ч {mins}м."}

        # Race: random placement, higher level = better odds
        max_level = get_tier_max_level(horse.tier)
        level_factor = horse.level / max_level if max_level > 0 else 0.5
        opponents = random.randint(3, 8)

        # Score: random + level bonus
        my_score = random.random() + level_factor * 0.3
        scores = [random.random() for _ in range(opponents)]
        scores.append(my_score)
        scores.sort(reverse=True)
        place = scores.index(my_score) + 1

        # Rewards per wiki
        data = _load()
        rewards_data = data.get("race_rewards", {}).get(str(horse.tier), {})
        place_rewards = rewards_data.get(str(min(place, 3)), [])

        reward_text = ""
        if place_rewards:
            # Pick one reward based on chances
            total = sum(r.get("chance", 0) for r in place_rewards)
            roll = random.random() * total
            cumulative = 0
            for r in place_rewards:
                cumulative += r.get("chance", 0)
                if roll < cumulative:
                    reward_text = _format_race_reward(r)
                    break

        text = (
            f"🏁 <b>Конные гонки</b>\n\n"
            f"{horse.name} (Тир {_tier_roman(horse.tier)})\n"
            f"Участников: {opponents + 1}\n"
            f"Место: #{place}\n"
        )
        if reward_text:
            text += f"\n{reward_text}"
        else:
            text += "\nБез награды. Попробуйте снова!"

        # Set shared cooldown
        horse.last_breed_race = datetime.utcnow()
        await s.commit()

        return {"success": True, "message": text}


def _format_race_reward(reward: dict) -> str:
    """Format a race reward."""
    rtype = reward.get("type", "")
    if rtype == "tier_up":
        return "🎉 Повышение тира лошади!"
    elif rtype == "horse_level":
        return "+1 уровень лошади"
    elif rtype == "lootbox":
        item = reward.get("item", "lootbox")
        count = reward.get("count", 1)
        return f"📦 {item.replace('_', ' ').title()} x{count}" if count > 1 else f"📦 {item.replace('_', ' ').title()}"
    elif rtype == "epic_berries":
        amt = reward.get("amount", 1)
        return f"🫐 {amt} Epic Berry"
    elif rtype == "pet":
        tier = reward.get("tier", 1)
        return f"🐾 Tier {tier} Pet"
    return "Награда"


async def horse_epicness(user_id: int) -> dict:
    """Use EPIC berries to increase horse epicness."""
    from database.crud import get_inventory, remove_materials, get_user
    from database.engine import async_session
    from database.models import Horse

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    inv = await get_inventory(user_id)
    berries = inv.get("epic_berries", 0)
    if berries < 1:
        return {"success": False, "message": "❌ Нужны EPIC berries."}

    async with async_session() as s:
        horse = await s.get(Horse, user_id)
        if not horse:
            return {"success": False, "message": "❌ У вас нет лошади."}
        if horse.epicness >= 99:
            return {"success": False, "message": "❌ EPICness максимальный (99)."}

        await remove_materials(user_id, "epic_berries", 1)
        horse.epicness += 1
        await s.commit()

    return {
        "success": True,
        "message": (
            f"✨ EPICness: {horse.epicness}/99\n"
            f"Бусты обновлены!"
        ),
    }
