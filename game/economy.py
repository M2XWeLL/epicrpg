import json
import random
import config
from datetime import datetime, timedelta

# Lootboxer XP per lootbox tier (wiki)
LOOTBOXER_XP = {
    "common": 4, "uncommon": 9, "rare": 17, "epic": 30,
    "edgy": 65, "omega": 800, "godly": 15000,
    "void": -1000, "eternal": 102413,
    "anniversary": 500, "easter": 1,
}

# Merchant XP per item sold (wiki) — per 1 item, floor(total)
# Items with [N] in wiki: XP shown is per N items
MERCHANT_SELL_XP = {
    "wolfskin": 3, "zombieeye": 5, "unicornhorn": 7, "mermaid_hair": 10,
    "chip": 15, "dragonscale": 20, "dark_energy": 100, "ruby": 2,
    "normie_fish": 0.2,  # wiki: [5] = 1 XP per 5 sold
    "golden_fish": 1, "epic_fish": 25, "super_fish": 750,
    "apple": 0.3, "banana": 0.7, "Watermelon": 200,
    "wooden_log": 0.2,  # wiki: [5] = 1 XP per 5 sold
    "epic_log": 2, "super_log": 20, "mega_log": 200,
    "hyper_log": 2000, "ultra_log": 20000, "ultimate_log": 200000,
    "arenacookie": 0.1,  # wiki: [10] = 1 XP per 10 sold
    "bread": 3, "carrot": 3, "potato": 3,
    "seed": 0, "flask": 50,
}

# Merchant XP per item bought (wiki)
MERCHANT_BUY_XP = {
    "common_lootbox": 1, "uncommon_lootbox": 2, "rare_lootbox": 3,
    "epic_lootbox": 4, "edgy_lootbox": 5, "basic_horse": 50,
}


def load_shop() -> dict:
    path = config.DATA_DIR / "items.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("shop", {})


def resolve_item(query: str) -> str:
    """Resolve Russian item names/aliases to English item IDs."""
    from data.ru_aliases import resolve_item as _resolve
    return _resolve(query)


async def buy_item(user_id: int, item_id: str, amount: int = 1) -> dict:
    from database.crud import get_user, add_materials
    from game.player import remove_coins

    item_id = resolve_item(item_id)
    shop = load_shop()
    item = shop.get(item_id)
    if not item:
        return {"success": False, "message": "❌ Предмет не найден в магазине."}

    total_cost = item["buy_price"] * amount
    user = await get_user(user_id)
    if not user or user.coins < total_cost:
        return {"success": False, "message": f"❌ Недостаточно монет. Нужно {total_cost}."}

    await remove_coins(user_id, total_cost)

    mat_map = {
        "basic_bait": "basic_bait",
        "advanced_bait": "advanced_bait",
        "golden_bait": "golden_bait",
        "life_potion": "life_potion",
    }
    mat = mat_map.get(item_id)
    if mat:
        await add_materials(user_id, mat, amount)

    # Merchant XP for buying
    buy_xp = MERCHANT_BUY_XP.get(item_id, 0)
    if buy_xp > 0:
        from database.crud import add_profession_xp
        await add_profession_xp(user_id, "merchant", buy_xp * amount)

    return {
        "success": True,
        "message": f"🛒 Куплено {amount}x {item['name']} за {total_cost} монет."
    }


async def sell_item(user_id: int, material: str, amount: int) -> dict:
    from database.crud import get_inventory, remove_materials
    from game.player import add_coins

    material = resolve_item(material)
    inv = await get_inventory(user_id)
    current = inv.get(material, 0)
    if current < amount:
        return {"success": False, "message": f"❌ У вас только {current}x этого ресурса."}

    sell_prices = {
        # Logs (from /sell in original EPIC RPG)
        "wooden_log": 25, "epic_log": 75, "super_log": 200, "mega_log": 500,
        "hyper_log": 1250, "ultra_log": 2500, "ultimate_log": 5000,
        # Fish
        "normie_fish": 40, "golden_fish": 200, "epic_fish": 75000,
        "super_fish": 750, "mega_fish": 1750, "hyper_fish": 3500,
        # Crops
        "apple": 2000, "banana": 10000, "potato": 10, "carrot": 20, "bread": 30, "Watermelon": 250,
        # Monster drops
        "wolfskin": 500, "zombieeye": 2000, "unicornhorn": 7500, "mermaid_hair": 30000,
        "ruby": 50000, "chip": 100000, "coin": 1, "dragonscale": 250000,
        # Consumables
        "lotteryticket": 500, "life_potion": 10, "arenacookie": 50, "seed": 4000,
        # Returning event items (not sellable)
        "smol_coin": 0, "magic_bed": 0, "omega_horse_token": 0,
        # Regular event items
        "diamond": 100000, "amber": 15000, "emerald": 25000, "sapphire": 50000,
    }
    price_per = sell_prices.get(material, 5)
    total = price_per * amount

    await remove_materials(user_id, material, amount)
    await add_coins(user_id, total)

    from database.crud import add_profession_xp
    # Merchant XP: per-item XP * amount, floored (wiki: never round up)
    xp_per = MERCHANT_SELL_XP.get(material, 1)
    total_merchant_xp = int(xp_per * amount)  # floor naturally via int()
    if total_merchant_xp > 0:
        await add_profession_xp(user_id, "merchant", total_merchant_xp)

    with open(config.DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
        mat_data = json.load(f)
    name = mat_data.get("names", {}).get(material, material)
    return {
        "success": True,
        "message": f"💰 Продано {amount}x {name} за {total} монет."
    }


# --- Daily / Weekly / Vote ---

async def get_daily_reward(user_id: int) -> dict:
    """Wiki-accurate daily: area-based coins + life potions, 23h50m cooldown,
    7+ streak = epic coin + flask. Horse tier affects coins."""
    from database.crud import get_user
    from database.engine import async_session
    from database.models import Cooldown, User, Horse
    from database.crud import add_materials

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    async with async_session() as s:
        cd = await s.get(Cooldown, user_id)
        if not cd:
            from database.models import Cooldown as CD
            cd = CD(user_id=user_id)
            s.add(cd)
            await s.commit()

        now = datetime.utcnow()
        cooldown = timedelta(seconds=config.DAILY_COOLDOWN)
        if cd.last_daily and cd.last_daily > now - cooldown:
            remaining = int((cd.last_daily + cooldown - now).total_seconds())
            h, rem = divmod(remaining, 3600)
            m = rem // 60
            return {"success": False, "message": f"⏳ Ежедневная награда через {h}ч {m}м."}

        # Wiki: coins and potions based on max_area
        area = min(user.max_area, 15)
        life_pot, base_coins = config.DAILY_BY_AREA.get(area, (2, 175))

        # Wiki: horse tier affects coins
        horse = await s.get(Horse, user_id)
        horse_mult = 1.0
        if horse and horse.tier >= 1:
            horse_mult = 1.0 + horse.tier * 0.05  # +5% per tier

        coins = int(base_coins * horse_mult)

        # Streak logic: check if last claim was within 25h (allows 1h margin)
        streak = cd.daily_streak or 0
        if cd.last_daily:
            gap = (now - cd.last_daily).total_seconds()
            if gap <= 90000:  # 25 hours
                streak += 1
            elif gap > 90000:
                streak = 1
        else:
            streak = 1

        cd.last_daily = now
        cd.daily_streak = streak
        await s.commit()

    # Give coins
    from game.player import add_coins
    await add_coins(user_id, coins)

    # Give life potions
    await add_materials(user_id, "life_potion", life_pot)

    msg = f"🎁 <b>Ежедневная награда</b>\n\n"
    msg += f"💰 +{coins:,} монет\n"
    msg += f"🧪 +{life_pot} life potion\n"
    msg += f"📅 Стрик: {streak}"

    # Wiki: 7+ streak = epic coin + flask
    if streak >= config.DAILY_STREAK_BONUS:
        # epic_coins is a User column, not a material
        async with async_session() as s:
            u = await s.get(User, user_id)
            if u:
                u.epic_coins = (u.epic_coins or 0) + 1
                await s.commit()
        await add_materials(user_id, "flask", 1)
        msg += "\n\n🎉 Бонус за стрик 7+!"
        msg += "\n💎 +1 EPIC Coin"
        msg += "\n🧪 +1 Flask"

    return {"success": True, "message": msg, "coins": coins}


async def get_weekly_reward(user_id: int) -> dict:
    """Wiki-accurate weekly: area-based coins + lootbox + 1-3 time cookies + 2 flasks.
    Horse tier affects coins. TT1+ chance of Pocketwatch part D."""
    from database.crud import get_user, add_materials
    from database.engine import async_session
    from database.models import Cooldown, Horse

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    async with async_session() as s:
        cd = await s.get(Cooldown, user_id)
        if not cd:
            from database.models import Cooldown as CD
            cd = CD(user_id=user_id)
            s.add(cd)
            await s.commit()

        now = datetime.utcnow()
        if cd.last_weekly and cd.last_weekly > now - timedelta(days=7):
            remaining = int((cd.last_weekly + timedelta(days=7) - now).total_seconds())
            d, rem = divmod(remaining, 86400)
            h = rem // 3600
            return {"success": False, "message": f"⏳ Еженедельная награда через {d}д {h}ч."}

        cd.last_weekly = now
        await s.commit()

    # Wiki: coins and lootbox based on max_area
    area = min(user.max_area, 16)
    if area < 1:
        area = 1
    base_coins, lootbox_type = config.WEEKLY_REWARD_TABLE.get(area, (750, "common_lootbox"))

    # Horse tier affects coins (wiki: horse tier multiplier)
    horse_tier = 1
    async with async_session() as s:
        horse = await s.get(Horse, user_id)
        if horse:
            horse_tier = horse.tier

    horse_mult = 1 + (horse_tier - 1) * 0.10  # +10% per tier above 1
    coins = int(base_coins * horse_mult)

    # Give rewards
    from game.player import add_coins as _add_coins
    await _add_coins(user_id, coins)
    await add_materials(user_id, lootbox_type, 1)

    time_cookies = random.randint(*config.WEEKLY_TIME_COOKIES)
    await add_materials(user_id, "time_cookie", time_cookies)
    await add_materials(user_id, "flask", config.WEEKLY_FLASKS)

    import json as _json
    with open(config.DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
        mat_names = _json.load(f).get("names", {})

    lb_name = mat_names.get(lootbox_type, lootbox_type)
    msg = (
        f"🎁 <b>Еженедельная награда!</b>\n\n"
        f"💰 +{coins:,} монет\n"
        f"📦 +1 {lb_name}\n"
        f"🍪 +{time_cookies} Time Cookie\n"
        f"🧪 +{config.WEEKLY_FLASKS} Flask"
    )

    return {"success": True, "message": msg}


async def get_vote_reward(user_id: int) -> dict:
    """Wiki-accurate vote: 12h cooldown, streak 0-7, lootbox scales, streak 7 = 25 cookies + flask + epic coin."""
    from database.crud import get_user, add_materials
    from database.engine import async_session
    from database.models import Cooldown, User

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    async with async_session() as s:
        cd = await s.get(Cooldown, user_id)
        if not cd:
            cd = Cooldown(user_id=user_id)
            s.add(cd)
            await s.commit()

        now = datetime.utcnow()
        if cd.last_vote and cd.last_vote > now - timedelta(hours=12):
            remaining = int((cd.last_vote + timedelta(hours=12) - now).total_seconds())
            h, rem = divmod(remaining, 3600)
            m = rem // 60
            return {"success": False, "message": f"⏳ Голосовать снова через {h}ч {m}м."}

        # Update streak: if last vote was within 24h, increment; else reset
        if cd.last_vote and cd.last_vote > now - timedelta(hours=24):
            cd.vote_streak = min(cd.vote_streak + 1, 7)
        else:
            cd.vote_streak = 1

        cd.last_vote = now
        await s.commit()
        streak = cd.vote_streak

    # Wiki: coins = level * 50 * streak multiplier
    coin_mult = 1 + (streak - 1) * 0.25 if streak > 1 else 1
    coins = int(user.level * 50 * coin_mult)
    await add_coins(user_id, coins)

    # Lootbox by streak (wiki)
    lootbox_by_streak = {
        0: "rare_lootbox",
        1: "epic_lootbox",
    }
    lootbox_type = lootbox_by_streak.get(streak, "edgy_lootbox")  # 2-7 = edgy
    await add_materials(user_id, lootbox_type, 1)

    # Adventure cooldown reset (always)
    from database.engine import async_session as _s
    async with _s() as s:
        cd = await s.get(Cooldown, user_id)
        if cd:
            cd.adventure_last = datetime.min
            await s.commit()

    # Streak 7: 25 arena cookies + flask + epic coin
    if streak >= 7:
        await add_materials(user_id, "arenacookie", 25)
        await add_materials(user_id, "flask", 1)
        await add_materials(user_id, "coin", 1)  # epic coin

    # Weekend (Fri/Sat/Sun UTC): miniboss/dungeon cooldown reset
    if now.weekday() in (4, 5, 6):  # Fri=4, Sat=5, Sun=6
        pass  # miniboss/dungeon cooldowns don't exist yet as separate fields

    import json as _json
    with open(config.DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
        mat_names = _json.load(f).get("names", {})
    lb_name = mat_names.get(lootbox_type, lootbox_type)

    msg = (
        f"🗳️ <b>Голосование!</b>\n\n"
        f"Streak: {streak}/7\n"
        f"💰 +{coins:,} монет\n"
        f"📦 +1 {lb_name}\n"
        f"🔄 Adventure кулдаун сброшен"
    )
    if streak >= 7:
        msg += (
            f"\n\n🎁 <b>Streak 7!</b>\n"
            f"  +25 Арена печенье\n"
            f"  +1 Фляга\n"
            f"  +1 EPIC монета"
        )

    return {"success": True, "message": msg}


async def get_vote_info(user_id: int) -> dict:
    """Show vote info: streak, cooldown, rewards table."""
    from database.crud import get_user
    from database.engine import async_session
    from database.models import Cooldown

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    streak = 0
    remaining_msg = ""
    async with async_session() as s:
        cd = await s.get(Cooldown, user_id)
        if cd:
            streak = cd.vote_streak
            if cd.last_vote:
                now = datetime.utcnow()
                if cd.last_vote > now - timedelta(hours=12):
                    remaining = int((cd.last_vote + timedelta(hours=12) - now).total_seconds())
                    h, rem = divmod(remaining, 3600)
                    m = rem // 60
                    remaining_msg = f"\n⏳ Голосовать через: {h}ч {m}м"

    lootbox_table = {
        0: "Rare Lootbox", 1: "Epic Lootbox",
    }
    lb = lootbox_table.get(streak, "Edgy Lootbox")

    text = (
        f"🗳️ <b>Голосование</b>\n\n"
        f"Стрик: <b>{streak}/7</b>{remaining_msg}\n\n"
        f"📊 Награды по стрику:\n"
        f"  0: Rare Lootbox\n"
        f"  1: Epic Lootbox\n"
        f"  2-7: Edgy Lootbox\n\n"
        f"🎁 Стрик 7: +25 печенье, +1 фляга, +1 EPIC монета\n"
        f"🔄 Всегда: сброс кулдауна adventure\n\n"
        f"Голосовать: <code>/vote</code>"
    )
    return {"success": True, "message": text}


# --- Give ---

async def give_coins(sender_id: int, receiver_username: str, amount: int) -> dict:
    """Give coins to another player. Restricted by TT difference."""
    from database.crud import get_user, remove_coins, add_coins
    from database.engine import async_session
    from database.models import User

    sender = await get_user(sender_id)
    if not sender:
        return {"success": False, "message": "Игрок не найден."}

    async with async_session() as s:
        from sqlalchemy import select
        result = await s.execute(select(User).where(User.username == receiver_username))
        receiver = result.scalar_one_or_none()
        if not receiver:
            return {"success": False, "message": f"❌ Игрок @{receiver_username} не найден."}
        if receiver.user_id == sender_id:
            return {"success": False, "message": "❌ Нельзя дарить себе."}

    # TT difference restriction
    tt_diff = abs(sender.tt_count - receiver.tt_count)
    if tt_diff > 2:
        return {
            "success": False,
            "message": f"❌ Нельзя передавать монеты игрокам с разницей TT > 2.\n"
                       f"Ваш TT: {sender.tt_count}, TT @{receiver_username}: {receiver.tt_count}"
        }

    if sender.coins < amount:
        return {"success": False, "message": f"❌ Недостаточно монет. У вас {sender.coins:,}."}

    await remove_coins(sender_id, amount)
    await add_coins(receiver.user_id, amount)
    return {"success": True, "message": f"💰 Отправлено {amount:,} монет @{receiver_username}!"}


# --- Use item ---

async def use_item(user_id: int, item: str) -> dict:
    from database.crud import get_inventory, remove_materials
    from database.engine import async_session
    from database.models import User

    inv = await get_inventory(user_id)
    if inv.get(item, 0) <= 0:
        return {"success": False, "message": f"❌ У вас нет {item}."}

    if item == "life_potion":
        await remove_materials(user_id, "life_potion", 1)
        return {"success": True, "message": "🧪 Зелье жизни использовано! HP восстановлено."}
    else:
        return {"success": False, "message": f"❌ Нельзя использовать {item}."}


# --- Open lootbox ---

async def open_lootbox(user_id: int, box_type: str = "common") -> dict:
    from database.crud import get_user, get_inventory, remove_materials, add_materials
    from game.lootbox import open_lootbox as _open_lb, format_lootbox_drops, LOOTBOX_TIERS

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    # Map short names to full keys
    box_map = {
        "common": "common_lootbox",
        "uncommon": "uncommon_lootbox",
        "rare": "rare_lootbox",
        "epic": "epic_lootbox",
        "edgy": "edgy_lootbox",
        "omega": "omega_lootbox",
        "godly": "godly_lootbox",
        "common_lootbox": "common_lootbox",
        "uncommon_lootbox": "uncommon_lootbox",
        "rare_lootbox": "rare_lootbox",
        "epic_lootbox": "epic_lootbox",
        "edgy_lootbox": "edgy_lootbox",
        "omega_lootbox": "omega_lootbox",
        "godly_lootbox": "godly_lootbox",
    }

    mat_key = box_map.get(box_type)
    if not mat_key:
        return {"success": False, "message": f"❌ Неизвестный лутбокс: {box_type}"}

    inv = await get_inventory(user_id)
    if inv.get(mat_key, 0) <= 0:
        return {"success": False, "message": f"❌ У вас нет {mat_key}. Купить: /buy {mat_key}"}

    # Remove the lootbox
    await remove_materials(user_id, mat_key, 1)

    # Determine tier key from mat_key
    tier_key = mat_key.replace("_lootbox", "")  # "common_lootbox" -> "common"

    # Open using new lootbox system
    result = _open_lb(user_id, tier_key, user.area)
    if not result["success"]:
        return result

    # Give all drops
    for mat, amt in result["drops"].items():
        await add_materials(user_id, mat, amt)

    from database.crud import add_profession_xp
    lb_xp = LOOTBOXER_XP.get(tier_key, 4)
    await add_profession_xp(user_id, "lootboxer", lb_xp)

    text = format_lootbox_drops(result["box_name"], result["drops"])
    return {"success": True, "message": text}


# --- Donate ---

async def donate_coins(user_id: int, amount: int) -> dict:
    from database.crud import get_user
    from database.engine import async_session
    from database.models import User

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}
    if user.coins < amount:
        return {"success": False, "message": "❌ Недостаточно монет."}

    epic = amount // 100  # 100 coins = 1 epic coin
    if epic < 1:
        return {"success": False, "message": "❌ Минимум 100 монет для доната."}

    async with async_session() as s:
        u = await s.get(User, user_id)
        u.coins -= amount
        u.epic_coins += epic
        await s.commit()

    return {"success": True, "message": f"💎 Донат: -{amount} монет, +{epic} EPIC монет!"}


# --- Promo codes ---
PROMO_CODES = {
    "WELCOME100": {"amount": 100, "type": "coins"},
    "EPIC2026": {"amount": 500, "type": "epic_coins"},
    "HUNT2026": {"amount": 200, "type": "coins"},
}

async def redeem_code(user_id: int, code: str) -> dict:
    from database.crud import get_user
    from database.engine import async_session
    from database.models import User

    promo = PROMO_CODES.get(code.upper())
    if not promo:
        return {"success": False, "message": "❌ Промокод не найден."}

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    async with async_session() as s:
        u = await s.get(User, user_id)
        if promo["type"] == "coins":
            u.coins += promo["amount"]
        elif promo["type"] == "epic_coins":
            u.epic_coins += promo["amount"]
        await s.commit()

    return {"success": True, "message": f"✅ Промокод активирован! +{promo['amount']} {'монет' if promo['type'] == 'coins' else 'EPIC монет'}"}
