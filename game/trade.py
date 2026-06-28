"""
Trade system — wiki-accurate resource exchange between 4 base materials.
Trades use max_area for rate brackets.
"""
import json
import config
from database.crud import get_user, get_inventory


# Material display info
MATERIAL_INFO = {
    "wooden_log": {"emoji": "🪵", "name": "Wooden Log"},
    "normie_fish": {"emoji": "🐟", "name": "Normie Fish"},
    "apple": {"emoji": "🍎", "name": "Apple"},
    "ruby": {"emoji": "💎", "name": "Ruby"},
}


def _get_bracket(max_area: int) -> int:
    """Map max_area to the trade rate bracket key."""
    if max_area <= 2:
        return 1
    elif max_area == 3:
        return 3
    elif max_area <= 5:
        return 4
    elif max_area <= 7:
        return 6
    elif max_area <= 8:
        return 8
    elif max_area <= 11:
        return max_area  # 9, 10, 11 each have their own bracket
    elif max_area <= 15:
        return 12  # Area 12-15 share rates
    else:
        return 16  # The TOP


def get_trade_options(max_area: int) -> list[dict]:
    """Get available trades for the player's max_area."""
    bracket = _get_bracket(max_area)
    return config.TRADE_RATES.get(bracket, config.TRADE_RATES[1])


def format_trade_options(max_area: int) -> str:
    """Format trade options for display."""
    options = get_trade_options(max_area)
    bracket = _get_bracket(max_area)

    # Find area display label
    if bracket == 1:
        area_label = "Area 1-2"
    elif bracket == 4:
        area_label = "Area 4-5"
    elif bracket == 6:
        area_label = "Area 6-7"
    elif bracket == 16:
        area_label = "The TOP"
    else:
        area_label = f"Area {bracket}"

    text = f"🔄 <b>Trade</b> ({area_label})\n\n"

    for opt in options:
        give_info = MATERIAL_INFO[opt["give"][0]]
        recv_info = MATERIAL_INFO[opt["receive"][0]]
        text += (
            f"  <b>{opt['id']})</b> {give_info['emoji']} {opt['give'][1]} {give_info['name']}"
            f" → {recv_info['emoji']} {opt['receive'][1]} {recv_info['name']}\n"
        )

    text += "\nОбмен: <code>/trade [ID] (кол-во)</code>"
    return text


async def execute_trade(user_id: int, trade_id: str, amount: int) -> dict:
    """Execute a trade. Returns success/message."""
    from database.crud import add_materials, remove_materials

    user = await get_user(user_id)
    if not user:
        return {"success": False, "message": "Игрок не найден."}

    options = get_trade_options(user.max_area)
    trade = None
    for opt in options:
        if opt["id"].upper() == trade_id.upper():
            trade = opt
            break

    if not trade:
        valid_ids = [opt["id"] for opt in options]
        return {
            "success": False,
            "message": f"❌ Нет сделки с ID '{trade_id}'. Доступные: {', '.join(valid_ids)}"
        }

    give_item, give_amount = trade["give"]
    recv_item, recv_amount = trade["receive"]

    if amount <= 0:
        return {"success": False, "message": "❌ Количество должно быть больше 0."}

    total_give = give_amount * amount
    total_recv = recv_amount * amount

    inv = await get_inventory(user_id)
    have = inv.get(give_item, 0)
    if have < total_give:
        return {
            "success": False,
            "message": f"❌ Нужно {total_give} {MATERIAL_INFO[give_item]['name']}, у вас {have}."
        }

    await remove_materials(user_id, give_item, total_give)
    await add_materials(user_id, recv_item, total_recv)

    give_info = MATERIAL_INFO[give_item]
    recv_info = MATERIAL_INFO[recv_item]

    return {
        "success": True,
        "message": (
            f"🔄 Обменено {total_give}x {give_info['emoji']} {give_info['name']}"
            f" → {total_recv}x {recv_info['emoji']} {recv_info['name']}"
        ),
    }
