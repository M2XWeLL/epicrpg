"""
Professions system — Worker, Crafter, Lootboxer, Merchant, Enchanter.
XP earned from respective activities. Level 5/25/50/100 = milestone rewards.
"""
import json
from database.crud import get_profession, add_profession_xp, get_profession_bonus

# XP thresholds (same as real Epic RPG)
# XP needed for level N = 100 * 1.5^(N-1)

PROFESSIONS = {
    "worker": {
        "name": "Worker",
        "emoji": "🪵",
        "desc": "Получай XP за работу (chop, fish, pickup, mine)",
        "effect": "Увеличивает шанс на лучший предмет при работе",
        "sources": ["chop", "axe", "bowsaw", "chainsaw", "fish", "net", "boat", "bigboat",
                     "pickup", "ladder", "tractor", "greenhouse", "mine", "pickaxe", "drill", "dynamite"],
    },
    "crafter": {
        "name": "Crafter",
        "emoji": "🔧",
        "desc": "Получай XP за крафт и разбор (craft, dismantle)",
        "effect": "Шанс сохранить часть рецепта при крафте",
        "sources": ["craft", "dismantle"],
    },
    "lootboxer": {
        "name": "Lootboxer",
        "emoji": "📦",
        "desc": "Получай XP за открытие лутбоксов",
        "effect": "Увеличивает бонус банка и снижает стоимость прокачки лошади",
        "sources": ["open"],
    },
    "merchant": {
        "name": "Merchant",
        "emoji": "💰",
        "desc": "Получай XP за продажу и покупку (не ключи, снаряжение, зелья)",
        "effect": "Увеличивает цену продажи предметов",
        "sources": ["sell", "buy"],
    },
    "enchanter": {
        "name": "Enchanter",
        "emoji": "✨",
        "desc": "Получай XP за зачарование (enchant)",
        "effect": "Увеличивает шанс на лучшее зачарование",
        "sources": ["enchant"],
    },
}

# Milestone rewards
MILESTONES = {
    5: {
        "desc": "3 uncommon_lootbox, 2 edgy_lootbox, 5 EPIC coins",
        "rewards": {"uncommon_lootbox": 3, "edgy_lootbox": 2, "epic_coins": 5},
    },
    25: {
        "desc": "4 rare_lootbox, 3 edgy_lootbox, 10 EPIC coins",
        "rewards": {"rare_lootbox": 4, "edgy_lootbox": 3, "epic_coins": 10},
    },
    50: {
        "desc": "5 epic_lootbox, 4 edgy_lootbox, 15 EPIC coins",
        "rewards": {"epic_lootbox": 5, "edgy_lootbox": 4, "epic_coins": 15},
    },
    100: {
        "desc": "1 random pet, 1 OMEGA lootbox, 20 EPIC coins",
        "rewards": {"random_pet": 1, "omega_lootbox": 1, "epic_coins": 20},
    },
}


def format_professions(prof_data: dict) -> str:
    """Format all professions for display."""
    claimed = prof_data.get("claimed", "{}")
    if isinstance(claimed, str):
        import json
        try:
            claimed = json.loads(claimed)
        except (json.JSONDecodeError, TypeError):
            claimed = {}

    text = "📋 <b>Профессии</b>\n\n"

    for key, info in PROFESSIONS.items():
        level = prof_data.get(f"{key}_level", 1)
        xp = prof_data.get(f"{key}_xp", 0)
        xp_needed = int(100 * (1.5 ** (level - 1)))
        pct = (xp / xp_needed * 100) if xp_needed > 0 else 0

        # Milestone markers
        markers = ""
        for ms in [5, 25, 50, 100]:
            is_claimed = claimed.get(f"{key}_{ms}", False)
            markers += "✅" if level >= ms and is_claimed else ("⬜" if level >= ms else "▪️")

        text += (
            f"{info['emoji']} <b>{info['name']}</b> — Lv {level} ({pct:.1f}%)\n"
            f"  XP: {xp:,}/{xp_needed:,}\n"
            f"  Милестионы: {markers}\n"
        )

    # Check for unclaimed rewards
    unclaimed = []
    for key in PROFESSIONS:
        level = prof_data.get(f"{key}_level", 1)
        for ms in [5, 25, 50, 100]:
            if level >= ms and not claimed.get(f"{key}_{ms}", False):
                unclaimed.append(f"{key} Lv{ms}")

    if unclaimed:
        text += f"\n🎁 <b>Незабранные награды:</b> {', '.join(unclaimed)}\n"
        text += "Забрать: /profession claim"

    text += "\n\nПодробнее: /profession [worker/crafter/lootboxer/merchant/enchanter]"
    return text


def format_profession_detail(key: str, prof_data: dict) -> str:
    """Format detailed info about a single profession."""
    info = PROFESSIONS.get(key)
    if not info:
        return "❌ Профессия не найдена."

    level = prof_data.get(f"{key}_level", 1)
    xp = prof_data.get(f"{key}_xp", 0)
    xp_needed = int(100 * (1.5 ** (level - 1)))
    pct = (xp / xp_needed * 100) if xp_needed > 0 else 0

    text = (
        f"{info['emoji']} <b>{info['name']}</b>\n"
        f"Уровень: {level} ({pct:.1f}%)\n"
        f"XP: {xp:,}/{xp_needed:,}\n\n"
        f"<b>О профессии:</b>\n{info['desc']}\n\n"
        f"<b>Эффект:</b>\n{info['effect']}\n\n"
        f"<b>Источники XP:</b>\n"
    )
    for src in info["sources"]:
        text += f"  /{src}\n"

    # Level 100+ bonus
    if level >= 100:
        bonus = get_profession_bonus_sync(level, key)
        text += f"\n<b>Бонус за {level}+ уровень:</b>\n{bonus}\n"

    # Milestones
    text += "\n<b>Милестионы:</b>\n"
    for ms, reward in sorted(MILESTONES.items()):
        status = "✅" if level >= ms else "⬜"
        text += f"  {status} Lv {ms}: {reward['desc']}\n"

    return text


def get_profession_bonus_sync(level: int, profession: str) -> str:
    """Get text description of level 100+ bonus."""
    bonuses = {
        "worker": "Шанс находить другие предметы при работе",
        "crafter": "Увеличивает % возвращаемых предметов из рецепта",
        "lootboxer": "Увеличивает максимальный уровень лошади",
        "merchant": "Шанс получить dragon scale при продаже monster drops",
        "enchanter": "Шанс получить монеты при зачаровании вместо потери",
    }
    return bonuses.get(profession, "")


def xp_for_level(level: int) -> int:
    """XP needed for a given level."""
    return int(100 * (1.5 ** (level - 1)))


async def claim_profession_reward(user_id: int, profession: str) -> dict:
    """Claim a profession milestone reward."""
    from database.crud import get_profession, add_materials, add_coins
    from database.engine import async_session
    from database.models import Profession
    import json

    prof_data = await get_profession(user_id)
    if not prof_data:
        return {"success": False, "message": "❌ Профессия не найдена."}

    level = prof_data.get(f"{profession}_level", 1)
    claimed = prof_data.get("claimed", "{}")
    if isinstance(claimed, str):
        try:
            claimed = json.loads(claimed)
        except (json.JSONDecodeError, TypeError):
            claimed = {}

    # Find highest unclaimed milestone
    best_ms = None
    for ms in [100, 50, 25, 5]:
        if level >= ms and not claimed.get(f"{profession}_{ms}", False):
            best_ms = ms
            break

    if not best_ms:
        return {"success": False, "message": "❌ Все награды уже забраны!"}

    rewards = MILESTONES[best_ms]["rewards"]

    # Give rewards
    msg_parts = []
    for item, amount in rewards.items():
        if item == "epic_coins":
            from database.engine import async_session as sess
            from database.models import User
            async with sess() as s:
                u = await s.get(User, user_id)
                if u:
                    u.epic_coins += amount
                    await s.commit()
            msg_parts.append(f"💎 +{amount} EPIC coins")
        elif item == "random_pet":
            from game.pets import catch_pet
            # Get user's area for rarity roll
            from database.crud import get_user
            user = await get_user(user_id)
            area = user.area if user else 1
            result = await catch_pet(user_id, area)
            if result.get("caught"):
                msg_parts.append(f"🐾 {result['emoji']} {result['name']} (Tier {result['pet_tier']})")
            else:
                msg_parts.append("🐾 Питомец не пойман (попробуй снова)")
        else:
            await add_materials(user_id, item, amount)
            names = {
                "uncommon_lootbox": "uncommon lootbox", "rare_lootbox": "rare lootbox",
                "epic_lootbox": "EPIC lootbox", "edgy_lootbox": "EDGY lootbox",
                "omega_lootbox": "OMEGA lootbox",
            }
            msg_parts.append(f"📦 +{amount} {names.get(item, item)}")

    # Mark as claimed
    claimed[f"{profession}_{best_ms}"] = True
    async with async_session() as s:
        p = await s.get(Profession, user_id)
        if p:
            p.claimed = json.dumps(claimed)
            await s.commit()

    info = PROFESSIONS[profession]
    text = (
        f"{info['emoji']} <b>{info['name']} — Награда Lv {best_ms}</b>\n\n"
        + "\n".join(msg_parts)
    )
    return {"success": True, "message": text}


async def claim_all_rewards(user_id: int) -> str:
    """Claim all available profession rewards."""
    from database.crud import get_profession

    prof_data = await get_profession(user_id)
    if not prof_data:
        return "❌ Профессия не найдена."

    results = []
    for prof_key in PROFESSIONS:
        result = await claim_profession_reward(user_id, prof_key)
        if result["success"]:
            results.append(result["message"])

    if not results:
        return "❌ Нет незабранных наград."

    return "\n\n---\n\n".join(results)


async def ascend(user_id: int) -> dict:
    """Ascend — requires all 5 professions at level 100+. Unlocks all area commands."""
    from database.crud import get_profession
    from database.engine import async_session
    from database.models import User

    prof_data = await get_profession(user_id)
    if not prof_data:
        return {"success": False, "message": "❌ Профессия не найдена."}

    # Check all 5 at 100+
    all_100 = True
    for key in PROFESSIONS:
        if prof_data.get(f"{key}_level", 1) < 100:
            all_100 = False
            break

    if not all_100:
        missing = [key for key in PROFESSIONS if prof_data.get(f"{key}_level", 1) < 100]
        names = [PROFESSIONS[k]["name"] for k in missing]
        return {"success": False, "message": f"❌ Все 5 профессий должны быть 100+ уровень.\nНе хватает: {', '.join(names)}"}

    async with async_session() as s:
        u = await s.get(User, user_id)
        if u:
            if u.ascended:
                return {"success": False, "message": "❌ Вы уже вознесены."}
            u.ascended = True
            await s.commit()

    return {
        "success": True,
        "message": (
            "🌟 <b>ВОЗНЕСЕНИЕ!</b>\n\n"
            "Все 5 профессий достигли уровня 100+!\n"
            "Теперь вы можете использовать любые команды,\n"
            "которые были открыты в прошлых прохождениях,\n"
            "в любой Area (например, /bigboat в Area 1)."
        ),
    }
