"""Returning Event — triggers for players inactive 7+ days.

Provides: super daily rewards, quest, special shop, smol coin drops,
33% cooldown reduction, 2x monster drops, free dungeons.
"""
import json
import random
from datetime import datetime, timedelta

import config
from database.engine import async_session
from database.models import User, ReturningEvent, Inventory
from database.crud import (
    get_user, get_inventory, add_materials, remove_materials, has_materials,
)


async def check_and_start_returning(user_id: int) -> dict | None:
    """Check if player is returning and start event if needed.

    Returns welcome message dict if event started, None otherwise.
    """
    from database.crud import check_returning_player, create_returning_event

    # Already has active event?
    from database.crud import get_returning_event
    existing = await get_returning_event(user_id)
    if existing:
        return None

    if not await check_returning_player(user_id):
        return None

    re = await create_returning_event(user_id)
    return {
        "success": True,
        "message": (
            "🎉 <b>Добро пожаловать обратно!</b>\n\n"
            "Вы не играли 7+ дней. Для вас начато событие <b>Возвращение</b>!\n\n"
            "🎁 Бонусы на 7 дней:\n"
            "  • -33% кулдаун на все команды\n"
            "  • x2 шанс дропа монстров\n"
            "  • Бесплатные подземелья (без ключей)\n\n"
            "Команды:\n"
            "  /returning info — статус события\n"
            "  /returning superdaily — ежедневная награда\n"
            "  /returning quest — квест\n"
            "  /returning shop — магазин\n"
            "  /returning buy [item] — купить из магазина"
        ),
    }


async def get_returning_info(user_id: int) -> dict:
    """Get formatted event status."""
    from database.crud import get_returning_event
    re = await get_returning_event(user_id)
    if not re:
        return {"success": False, "message": "❌ У вас нет активного события Возвращение."}

    now = datetime.utcnow()
    started = re.started_at
    if started and started.tzinfo is not None:
        started = started.replace(tzinfo=None)
    remaining = max(0, config.RETURNING_DURATION - (now - started).days)

    # Quest progress
    smol_needed = 40
    shop_needed = 25
    daily_needed = 3

    lines = [
        f"🎉 <b>Событие Возвращение</b>",
        f"Осталось дней: <b>{remaining}</b>\n",
        f"📅 Супер дейли: день <b>{re.superdaily_day + 1}</b>/7",
        f"  Забрано: {re.quest_superdaily_claims}/3 (для квеста)\n",
        f"📋 <b>Квест:</b>",
        f"  🪙 Собрать {smol_needed} smol coins: <b>{re.quest_collected_smol}/{smol_needed}</b>",
        f"  🛒 Купить 25 в магазине: <b>{re.quest_shop_buys}/{shop_needed}</b>",
        f"  📅 Забрать 3 супер дейли: <b>{re.quest_superdaily_claims}/{daily_needed}</b>",
    ]

    if re.quest_claimed:
        lines.append("\n✅ Квест выполнен!")
    elif re.quest_collected_smol >= smol_needed and re.quest_shop_buys >= shop_needed and re.quest_superdaily_claims >= daily_needed:
        lines.append("\n🏆 Квест готов к получению! /returning quest")

    return {"success": True, "message": "\n".join(lines)}


async def claim_superdaily(user_id: int) -> dict:
    """Claim the next super daily reward."""
    from database.crud import get_returning_event

    re = await get_returning_event(user_id)
    if not re:
        return {"success": False, "message": "❌ У вас нет активного события Возвращение."}

    if re.superdaily_day >= 7:
        return {"success": False, "message": "❌ Вы уже забрали все супер дейли награды!"}

    day = re.superdaily_day
    rewards = config.RETURNING_SUPER_DAILY[day]

    # Give rewards
    reward_lines = []
    for item_id, amount in rewards:
        await add_materials(user_id, item_id, amount)
        emoji, name = _mat_info(item_id)
        reward_lines.append(f"  {emoji} {amount}x {name}")

    re.superdaily_day += 1
    re.quest_superdaily_claims += 1
    await _save_returning_event(re)

    return {
        "success": True,
        "message": (
            f"🎁 <b>Супер дейли — День {day + 1}/7</b>\n\n"
            + "\n".join(reward_lines)
        ),
    }


async def get_returning_shop() -> dict:
    """Show the returning shop items."""
    lines = ["🏪 <b>Магазин Возвращения</b>\n", "Цены в smol coins:\n"]

    for item_id, (cost, limit, name) in config.RETURNING_SHOP.items():
        limit_str = f"(лимит: {limit})" if limit > 0 else "(без лимита)"
        lines.append(f"  {name} — {cost} smol coins {limit_str}")

    lines.append("\nКупить: /returning buy [item]")
    lines.append("Ваши smol coins: /returning info")
    return {"success": True, "message": "\n".join(lines)}


async def buy_returning_shop(user_id: int, item_id: str) -> dict:
    """Buy an item from the returning shop."""
    from database.crud import get_returning_event
    import json as _json

    re = await get_returning_event(user_id)
    if not re:
        return {"success": False, "message": "❌ У вас нет активного события Возвращение."}

    if item_id not in config.RETURNING_SHOP:
        return {"success": False, "message": f"❌ Предмет '{item_id}' не найден в магазине."}

    cost, limit, name = config.RETURNING_SHOP[item_id]
    purchases = _json.loads(re.shop_purchases)
    current_bought = purchases.get(item_id, 0)

    if limit > 0 and current_bought >= limit:
        return {"success": False, "message": f"❌ Лимит исчерпан для {name} ({limit}/{limit})."}

    # Check smol coins
    inv = await get_inventory(user_id)
    smol = inv.get("smol_coin", 0)
    if smol < cost:
        return {"success": False, "message": f"❌ Нужно {cost} smol coins. У вас: {smol}"}

    # Deduct smol coins
    from database.crud import remove_materials as rm
    await rm(user_id, "smol_coin", cost)

    # Give reward based on item
    if item_id == "edgy_lootbox":
        await add_materials(user_id, "edgy_lootbox", 1)
    elif item_id == "arenacookie":
        await add_materials(user_id, "arenacookie", 40)
    elif item_id == "coins":
        from game.player import add_coins
        await add_coins(user_id, 1000)
    elif item_id == "dungeon_reset":
        # Reset dungeon cooldown
        from database.crud import get_cooldowns
        from database.models import Cooldown
        async with async_session() as s:
            cd = await s.get(Cooldown, user_id)
            if cd:
                cd.last_duel = datetime.min  # shares cooldown with dungeon
                await s.commit()
    elif item_id == "random_epic_item":
        # Random epic material
        epic_items = ["unicornhorn", "mermaid_hair", "ruby", "dragonscale", "chip"]
        chosen = random.choice(epic_items)
        await add_materials(user_id, chosen, random.randint(1, 3))
        _, reward_name = _mat_info(chosen)
        return {
            "success": True,
            "message": f"🎲 Вы получили: {reward_name}!",
        }

    # Track purchase
    purchases[item_id] = current_bought + 1
    re.shop_purchases = _json.dumps(purchases)
    re.quest_shop_buys += 1
    await _save_returning_event(re)

    return {"success": True, "message": f"✅ Куплено: {name} за {cost} smol coins."}


async def get_returning_quest(user_id: int) -> dict:
    """Show quest progress."""
    from database.crud import get_returning_event
    re = await get_returning_event(user_id)
    if not re:
        return {"success": False, "message": "❌ У вас нет активного события Возвращение."}

    smol_needed = 40
    shop_needed = 25
    daily_needed = 3

    smol_done = re.quest_collected_smol >= smol_needed
    shop_done = re.quest_shop_buys >= shop_needed
    daily_done = re.quest_superdaily_claims >= daily_needed

    lines = [
        "📋 <b>Квест Возвращения</b>\n",
        f"{'✅' if smol_done else '❌'} Собрать {smol_needed} smol coins: {re.quest_collected_smol}/{smol_needed}",
        f"{'✅' if shop_done else '❌'} Купить 25 в магазине: {re.quest_shop_buys}/{shop_needed}",
        f"{'✅' if daily_done else '❌'} Забрать 3 супер дейли: {re.quest_superdaily_claims}/{daily_needed}",
    ]

    if re.quest_claimed:
        lines.append("\n✅ Квест уже выполнен!")
    elif smol_done and shop_done and daily_done:
        lines.append("\n🏆 Все задачи выполнены! Заберите награду: /returning quest claim")
    else:
        total = smol_done + shop_done + daily_done
        lines.append(f"\nПрогресс: {total}/3")

    return {"success": True, "message": "\n".join(lines)}


async def claim_returning_quest(user_id: int) -> dict:
    """Claim the quest reward."""
    from database.crud import get_returning_event

    re = await get_returning_event(user_id)
    if not re:
        return {"success": False, "message": "❌ У вас нет активного события Возвращение."}

    if re.quest_claimed:
        return {"success": False, "message": "❌ Квест уже выполнен."}

    smol_needed = 40
    shop_needed = 25
    daily_needed = 3

    if re.quest_collected_smol < smol_needed or re.quest_shop_buys < shop_needed or re.quest_superdaily_claims < daily_needed:
        return {"success": False, "message": "❌ Еще не все задачи выполнены. /returning quest"}

    # Give rewards
    reward = config.RETURNING_QUEST_REWARD
    lines = ["🏆 <b>Квест Возвращения выполнен!</b>\n", "Награды:"]
    for item_id, amount in reward["items"]:
        await add_materials(user_id, item_id, amount)
        emoji, name = _mat_info(item_id)
        lines.append(f"  {emoji} {amount}x {name}")

    if reward.get("epic_coins"):
        async with async_session() as s:
            user = await s.get(User, user_id)
            if user:
                user.epic_coins += reward["epic_coins"]
                await s.commit()
        lines.append(f"  💎 {reward['epic_coins']} EPIC Coins")

    re.quest_claimed = True
    await _save_returning_event(re)

    return {"success": True, "message": "\n".join(lines)}


async def track_smol_coins(user_id: int, amount: int):
    """Track smol coin collection for the quest."""
    from database.crud import get_returning_event
    re = await get_returning_event(user_id)
    if re and not re.quest_claimed:
        re.quest_collected_smol += amount
        await _save_returning_event(re)


async def get_returning_shop_prices() -> dict:
    """Return shop item_id -> (cost, limit) mapping."""
    return {k: (v[0], v[1]) for k, v in config.RETURNING_SHOP.items()}


# --- Material helpers ---

def _mat_info(item_id: str) -> tuple[str, str]:
    """Get (emoji, name) for a material item from materials.json."""
    with open(config.DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
        mat_data = json.load(f)
    emoji = mat_data.get("emojis", {}).get(item_id, "❓")
    name = mat_data.get("names", {}).get(item_id, item_id)
    return emoji, name


# --- Internal helpers ---

async def _save_returning_event(re: ReturningEvent):
    """Commit a ReturningEvent object."""
    async with async_session() as s:
        s.add(re)
        await s.commit()
