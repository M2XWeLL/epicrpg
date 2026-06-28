"""
EPIC NPC trade logic — trade wooden logs for fish, apples, rubies at area-dependent rates.
"""
import config


def get_trade_rates(area: int) -> dict:
    """Get available trades for the given area."""
    rates = config.NPC_TRADE_RATES.get(area, config.NPC_TRADE_RATES.get(1))
    available = {}
    for item, wood_cost in rates.items():
        if wood_cost > 0:
            available[item] = wood_cost
    return available


def format_trade_rates(area: int) -> str:
    """Format trade rates for display."""
    rates = get_trade_rates(area)
    if not rates:
        return "❌ Нет доступных сделок в этой локации."

    names = {
        "fish": ("🐟 Рыба", "normie_fish"),
        "apple": ("🍎 Яблоко", "apple"),
        "ruby": ("💎 Рубин", "ruby"),
    }

    text = f"🏪 <b>EPIC NPC — Локация {area}</b>\n\n"
    text += "Обмен: wooden_log → предмет\n\n"
    for item, wood_cost in rates.items():
        display_name, mat_key = names.get(item, (item, item))
        text += f"  {wood_cost} 🪵 → 1 {display_name}\n"

    text += "\nКупить: /npc buy [предмет] [кол-во]"
    text += "\nПродать: /npc sell [предмет] [кол-во]"
    return text


async def npc_buy(user_id: int, item: str, amount: int) -> dict:
    """Buy item from NPC by spending wooden logs."""
    from database.crud import get_user, get_inventory, remove_materials, add_materials

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    rates = get_trade_rates(user.area)
    if item not in rates:
        return {"success": False, "message": f"❌ Предмет '{item}' не продаётся в этой локации."}

    wood_cost_per = rates[item]
    total_wood = wood_cost_per * amount

    inv = await get_inventory(user_id)
    if inv.get("wooden_log", 0) < total_wood:
        return {"success": False, "message": f"❌ Нужно {total_wood} wooden_log, у вас {inv.get('wooden_log', 0)}."}

    mat_key = {"fish": "normie_fish", "apple": "apple", "ruby": "ruby"}[item]
    await remove_materials(user_id, "wooden_log", total_wood)
    await add_materials(user_id, mat_key, amount)

    names = {"fish": "🐟 normie_fish", "apple": "🍎 apple", "ruby": "💎 ruby"}
    return {
        "success": True,
        "message": f"🏪 Куплено {amount}x {names[item]} за {total_wood} wooden_log."
    }


async def npc_sell(user_id: int, item: str, amount: int) -> dict:
    """Sell item to NPC, receiving wooden logs."""
    from database.crud import get_user, get_inventory, remove_materials, add_materials

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    rates = get_trade_rates(user.area)
    if item not in rates:
        return {"success": False, "message": f"❌ Нельзя продать '{item}' в этой локации."}

    mat_key = {"fish": "normie_fish", "apple": "apple", "ruby": "ruby"}[item]
    inv = await get_inventory(user_id)
    if inv.get(mat_key, 0) < amount:
        return {"success": False, "message": f"❌ У вас только {inv.get(mat_key, 0)}x {mat_key}."}

    wood_cost_per = rates[item]
    wood_gained = wood_cost_per * amount

    await remove_materials(user_id, mat_key, amount)
    await add_materials(user_id, "wooden_log", wood_gained)

    names = {"fish": "🐟 normie_fish", "apple": "🍎 apple", "ruby": "💎 ruby"}
    return {
        "success": True,
        "message": f"🏪 Продано {amount}x {names[item]}, получено {wood_gained} wooden_log."
    }
