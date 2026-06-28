"""
Crafting commands: /craft, /recipes, /dismantle, /cook.
"""
import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from database.crud import get_user, get_equipment, get_inventory
from game.crafting import craft_equipment, dismantle_equipment, get_craft_cost, load_recipes
from config import DATA_DIR, TIER_NAMES, COOK_RECIPES

router = Router()


def _mat_name(mat_id: str) -> str:
    with open(DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
        mat_names = json.load(f).get("names", {})
    return mat_names.get(mat_id, mat_id.replace("_", " ").title())


@router.message(F.text == "/craft")
@router.message(F.text.startswith("/craft "))
async def cmd_craft(message: Message):
    args = message.text.split()[1:]

    # /craft [item] [amount] — convert materials (e.g. /craft epic_log 5)
    if args:
        await _handle_item_craft(message, args)
        return

    eq = await get_equipment(message.from_user.id)
    user = await get_user(message.from_user.id)
    if not eq or not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    current_tier = eq.get("weapon_tier", 1)
    next_tier = current_tier + 1
    cost = get_craft_cost(next_tier)
    if not cost:
        await message.answer("✅ У вас максимальное снаряжение!")
        return

    if user.level < cost["level"]:
        await message.answer(f"❌ Нужен уровень {cost['level']} для этого рецепта.")
        return

    text = f"⚒️ <b>Крафт: Level {cost['level']}</b>\n\n"

    # Weapon
    text += f"⚔️ <b>{cost['weapon_name']}</b> ({cost['weapon_atk']} at)\n"
    for mat, amt in cost.get("weapon_materials", {}).items():
        text += f"  • {_mat_name(mat)} × {amt:,}\n"

    # Armor
    text += f"\n🛡️ <b>{cost['armor_name']}</b> ({cost['armor_def']} def)\n"
    for mat, amt in cost.get("armor_materials", {}).items():
        text += f"  • {_mat_name(mat)} × {amt:,}\n"

    # Craft button
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚒️ Craft", callback_data=f"craft:{next_tier}")]
    ])

    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("craft:"))
async def cb_craft(callback: CallbackQuery):
    tier = int(callback.data.split(":")[1])
    result = await craft_equipment(callback.from_user.id, tier)
    await callback.answer()
    if result["success"]:
        await callback.message.edit_text(result["message"])
    else:
        await callback.answer(result["message"], show_alert=True)


# --- /recipes ---
@router.message(F.text == "/recipes")
@router.message(F.text.startswith("/recipes "))
async def cmd_recipes(message: Message):
    args = message.text.split()[1:]
    recipes = load_recipes()
    craft = recipes.get("craft", {})
    tt = recipes.get("time_travel", {})
    items = recipes.get("items", {})
    cook = recipes.get("cook", {})

    if not args:
        text = (
            "📖 <b>Рецепты</b>\n\n"
            "See more with <code>recipes [basic, advanced, tryhard, items, cook, tt]</code>\n"
            "See a specific recipe with <code>recipes [recipe name]</code>"
        )
        await message.answer(text, parse_mode="HTML")
        return

    category = args[0].lower()

    if category in ("basic", "advanced", "tryhard"):
        if category == "basic":
            tiers = {k: v for k, v in craft.items() if v["level"] <= 10}
            header = "📖 <b>Level 1 recipes</b>\n\n"
        elif category == "advanced":
            tiers = {k: v for k, v in craft.items() if 10 < v["level"] <= 50}
            header = "📖 <b>Level 11-50 recipes</b>\n\n"
        else:
            tiers = {k: v for k, v in craft.items() if v["level"] > 50}
            header = "📖 <b>Level 50+ recipes</b>\n\n"

        text = header
        for tier_str in sorted(tiers.keys(), key=int):
            r = tiers[tier_str]
            text += f"<b>Level {r['level']} recipes</b>\n"
            w_mats = " + ".join(f"{amt:,} {_mat_name(k)}" for k, amt in r["weapon_materials"].items())
            a_mats = " + ".join(f"{amt:,} {_mat_name(k)}" for k, amt in r["armor_materials"].items())
            text += f"🗡️ {r['weapon_name']} [{r['weapon_atk']} at] ➜ {w_mats}\n"
            text += f"🛡️ {r['armor_name']} [{r['armor_def']} def] ➜ {a_mats}\n\n"

        text += "ℹ️ Make sure you meet the level requirement!"
        await message.answer(text, parse_mode="HTML")
        return

    if category == "tt":
        text = "⏳ <b>Time Travel recipes</b>\n\n"
        for key in sorted(tt.keys()):
            r = tt[key]
            text += f"<b>Time travel {r['tt']} recipes</b>\n"
            w_mats = " + ".join(f"{amt:,} {_mat_name(k)}" for k, amt in r["weapon_materials"].items())
            a_mats = " + ".join(f"{amt:,} {_mat_name(k)}" for k, amt in r["armor_materials"].items())
            text += f"🗡️ {r['weapon_name']} [{r['weapon_atk']} at] ➜ {w_mats}\n"
            text += f"🛡️ {r['armor_name']} [{r['armor_def']} def] ➜ {a_mats}\n\n"

        text += "ℹ️ Make sure you meet the time travel requirement!"
        await message.answer(text, parse_mode="HTML")
        return

    if category == "items":
        text = "📦 <b>Item recipes</b>\n\n"
        for key, r in items.items():
            mats = " + ".join(f"{amt:,} {_mat_name(k)}" for k, amt in r["materials"].items())
            text += f"{_mat_name(r['result'])} = {mats}\n"
        text += "\nℹ️ Use dismantle to dismantle the item instead of crafting it (you get 80% of the original craft)"
        await message.answer(text, parse_mode="HTML")
        return

    if category == "cook":
        text = "🍳 <b>Cook recipes</b>\n\n"
        for key, r in cook.items():
            mats = " + ".join(f"{amt:,} {_mat_name(k)}" for k, amt in r["materials"].items())
            text += f"  🍳 <b>{r['name']}</b> ({r['buff']}) ➜ {mats}\n"
        text += "\nℹ️ Recipes are consumed instantly!"
        await message.answer(text, parse_mode="HTML")
        return

    # Specific recipe lookup
    search = " ".join(args).lower()
    found = False
    text = ""

    for tier_str, r in craft.items():
        if search in r["weapon_name"].lower() or search in r["armor_name"].lower():
            w_mats = " + ".join(f"{amt:,} {_mat_name(k)}" for k, amt in r["weapon_materials"].items())
            a_mats = " + ".join(f"{amt:,} {_mat_name(k)}" for k, amt in r["armor_materials"].items())
            text += f"<b>Level {r['level']} recipes</b>\n"
            text += f"🗡️ {r['weapon_name']} [{r['weapon_atk']} at] ➜ {w_mats}\n"
            text += f"🛡️ {r['armor_name']} [{r['armor_def']} def] ➜ {a_mats}\n\n"
            found = True

    for key, r in items.items():
        if search in r.get("result", "").lower() or search in r.get("result_name", "").lower():
            mats = " + ".join(f"{amt:,} {_mat_name(k)}" for k, amt in r["materials"].items())
            text += f"{_mat_name(r['result'])} = {mats}\n"
            found = True

    for key, r in cook.items():
        if search in r["name"].lower():
            mats = " + ".join(f"{amt:,} {_mat_name(k)}" for k, amt in r["materials"].items())
            text += f"🍳 <b>{r['name']}</b> ({r['buff']}) ➜ {mats}\n"
            found = True

    if not found:
        text = "❌ Рецепт не найден."

    await message.answer(text, parse_mode="HTML")


# --- /cook ---
@router.message(F.text == "/cook")
async def cmd_cook(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    if user.area < 5:
        await message.answer("❌ Cook доступен с Area 5.")
        return

    text = "🍳 <b>Cook recipes</b>\n\n"
    for key, r in COOK_RECIPES.items():
        mats = " + ".join(f"{amt} {_mat_name(k)}" for k, amt in r["materials"].items())
        text += f"  <code>/cook {key}</code> — <b>{r['name']}</b> ({r['buff']})\n    ➜ {mats}\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/cook "))
async def cmd_cook_item(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    if user.area < 5:
        await message.answer("❌ Cook доступен с Area 5.")
        return

    item_id = message.text[len("/cook "):].strip().lower()
    recipe = COOK_RECIPES.get(item_id)

    if not recipe:
        await message.answer(f"❌ Рецепт «{item_id}» не найден. Используй /cook для списка.")
        return

    # Check materials
    inv = await get_inventory(message.from_user.id)
    from database.crud import has_materials, remove_materials

    if not await has_materials(message.from_user.id, recipe["materials"]):
        text = f"❌ Недостаточно ресурсов для {recipe['name']}!\n\nНужно:\n"
        for mat, amt in recipe["materials"].items():
            have = inv.get(mat, 0)
            text += f"  • {_mat_name(mat)}: {have}/{amt}\n"
        await message.answer(text, parse_mode="HTML")
        return

    # Check and deduct coins (500 per cook)
    from database.crud import add_coins
    cook_cost = config.COOK_COST_COINS
    if user.coins < cook_cost:
        await message.answer(f"❌ Нужно {cook_cost} монет для кулинарии. У вас: {user.coins}")
        return
    await add_coins(message.from_user.id, -cook_cost)

    # Consume materials
    for mat, amt in recipe["materials"].items():
        await remove_materials(message.from_user.id, mat, amt)

    # Apply buffs
    from database.engine import async_session
    from database.models import User
    import re

    async with async_session() as s:
        db_user = await s.get(User, message.from_user.id)
        if db_user:
            buff_text = recipe.get("buff", "")
            applied = []
            # Parse "+N к макс. HP" or "+N max HP"
            hp_match = re.search(r'\+(\d+)\s*(?:к\s*макс\.?\s*HP|max\s*HP)', buff_text)
            if hp_match:
                db_user.cook_hp_boost += int(hp_match.group(1))
                applied.append(f"+{hp_match.group(1)} max HP")
            # Parse "+N DEF"
            def_match = re.search(r'\+(\d+)\s*DEF', buff_text)
            if def_match:
                db_user.cook_def_boost += int(def_match.group(1))
                applied.append(f"+{def_match.group(1)} DEF")
            # Parse "+N ATK"
            atk_match = re.search(r'\+(\d+)\s*ATK', buff_text)
            if atk_match:
                db_user.cook_atk_boost += int(atk_match.group(1))
                applied.append(f"+{atk_match.group(1)} ATK")
            # Parse "+N уровень/уровней"
            lvl_match = re.search(r'\+(\d+)\s*(?:уровен|level)', buff_text)
            if lvl_match:
                db_user.cook_level_boost += int(lvl_match.group(1))
                db_user.level += int(lvl_match.group(1))
                applied.append(f"+{lvl_match.group(1)} levels")
            # Apply multiplier buffs
            coins_mult = recipe.get("coins_mult", 0)
            fish_mult = recipe.get("fish_mult", 0)
            logs_mult = recipe.get("logs_mult", 0)
            flat_coins = recipe.get("flat_coins", 0)
            if coins_mult > 0:
                db_user.cook_coins_mult += coins_mult
                applied.append(f"+{coins_mult}% coins")
            if fish_mult > 0:
                db_user.cook_fish_mult += fish_mult
                applied.append(f"+{fish_mult}% fish")
            if logs_mult > 0:
                db_user.cook_logs_mult += logs_mult
                applied.append(f"+{logs_mult}% logs")
            if flat_coins > 0:
                db_user.cook_flat_coins += flat_coins
                applied.append(f"+{flat_coins} coins/command")
            await s.commit()

    # Crafter XP for cooking
    from database.crud import add_profession_xp
    await add_profession_xp(message.from_user.id, "crafter", 15)

    await message.answer(
        f"🍳 <b>{recipe['name']}</b>\n\n"
        f"Приготовлено! {recipe['buff']}",
        parse_mode="HTML",
    )


# --- /dismantle [item] [amount] ---
@router.message(F.text == "/dismantle")
@router.message(F.text.startswith("/dismantle "))
async def cmd_dismantle(message: Message):
    args = message.text.split()[1:]

    # /dismantle [item] [amount] — dismantle a material from inventory
    if args:
        await _handle_item_dismantle(message, args)
        return

    # /dismantle — dismantle current equipped gear
    result = await dismantle_equipment(message.from_user.id)
    await message.answer(result["message"])


async def _handle_item_craft(message: Message, args: list):
    """Handle /craft [item] [amount] — convert lower materials to higher."""
    if len(args) < 1:
        await message.answer("Формат: /craft [item] [amount]\nПример: /craft epic_log 5")
        return

    item_id = args[0].lower()
    amount = int(args[1]) if len(args) >= 2 else 1

    recipes = load_recipes()
    items = recipes.get("items", {})
    recipe = items.get(item_id)

    if not recipe:
        # List available items
        text = "📦 <b>Доступные рецепты конвертации:</b>\n\n"
        for key, r in items.items():
            mats = " + ".join(f"{amt:,} {_mat_name(k)}" for k, amt in r["materials"].items())
            text += f"<code>/craft {key}</code> — {r['result_name']}\n  ➜ {mats}\n\n"
        await message.answer(text, parse_mode="HTML")
        return

    # Calculate total cost
    total_cost = {}
    for mat, amt in recipe["materials"].items():
        total_cost[mat] = amt * amount

    # Check materials
    from database.crud import has_materials, remove_materials, add_materials
    if not await has_materials(message.from_user.id, total_cost):
        inv = await get_inventory(message.from_user.id)
        text = f"❌ Недостаточно ресурсов для {amount}x {recipe['result_name']}!\n\nНужно:\n"
        for mat, amt in total_cost.items():
            have = inv.get(mat, 0)
            text += f"  • {_mat_name(mat)}: {have:,}/{amt:,}\n"
        await message.answer(text, parse_mode="HTML")
        return

    # Execute conversion
    for mat, amt in total_cost.items():
        await remove_materials(message.from_user.id, mat, amt)
    await add_materials(message.from_user.id, item_id, amount)

    from database.crud import add_profession_xp
    await add_profession_xp(message.from_user.id, "crafter", 5)

    await message.answer(
        f"✅ Сконвертировано! {amount}x {_mat_name(item_id)}",
        parse_mode="HTML",
    )


async def _handle_item_dismantle(message: Message, args: list):
    """Handle /dismantle [item] [amount] — dismantle materials from inventory."""
    if len(args) < 1:
        await message.answer("Формат: /dismantle [item] [amount]\nПример: /dismantle epic_log 5")
        return

    item_id = args[0].lower()
    amount = int(args[1]) if len(args) >= 2 else 1

    recipes = load_recipes()
    items = recipes.get("items", {})

    # Find the recipe that produces this item
    recipe = items.get(item_id)
    if not recipe:
        # List available items that can be dismantled
        text = "🔧 <b>Доступные рецепты для разбора:</b>\n\n"
        for key, r in items.items():
            mats = " + ".join(f"{amt:,} {_mat_name(k)}" for k, amt in r["materials"].items())
            text += f"<code>/dismantle {key}</code> — {r['result_name']}\n  ➜ Вернёт 80%: {mats}\n\n"
        text += "ℹ️ Возвращается 80% материалов (20% потеря)"
        await message.answer(text, parse_mode="HTML")
        return

    # Check if user has the item
    inv = await get_inventory(message.from_user.id)
    have = inv.get(item_id, 0)
    if have < amount:
        await message.answer(
            f"❌ У вас только {have}x {_mat_name(item_id)}. Нужно: {amount}",
            parse_mode="HTML",
        )
        return

    # Calculate 80% return per unit, times amount
    from database.crud import remove_materials, add_materials
    returned = {}
    for mat, amt in recipe["materials"].items():
        return_per_unit = max(1, int(amt * 0.8))
        total_return = return_per_unit * amount
        returned[mat] = total_return

    # Remove the item
    await remove_materials(message.from_user.id, item_id, amount)

    # Give back 80% of materials
    for mat, amt in returned.items():
        await add_materials(message.from_user.id, mat, amt)

    from database.crud import add_profession_xp
    await add_profession_xp(message.from_user.id, "crafter", 5)

    mat_text = " + ".join(f"{amt:,}x {_mat_name(m)}" for m, amt in returned.items())
    await message.answer(
        f"🔧 Разобрано! {amount}x {_mat_name(item_id)}\nВозвращено (80%): {mat_text}",
        parse_mode="HTML",
    )
