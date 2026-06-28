"""
Area-unlocked commands: area, enchant, training, axe, net, pickup, ladder, farm,
multidice, cook, bowsaw, boat, pickaxe upgrade, refine, big_arena, tractor, wheel,
chainsaw, bigboat, drill, minintboss, forge, voidforge, greenhouse, dynamite, pets (upgrade),
ultraining, badge, transmute, big_dice, super_timetravel, transcend.
"""
import random
import math
import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.crud import get_user, get_equipment, get_tools, set_equipment, set_tools, add_materials, remove_materials, get_inventory, get_cooldowns
from database.engine import async_session
from database.models import User, Cooldown
from game.player import calc_atk, calc_def, add_xp, add_coins, remove_coins
from game.training import calc_training_xp, get_pet_spawn_chance
from game.crafting import load_recipes
from game.areas import get_area
from config import DATA_DIR
import config

router = Router()


def _check_area(user, required: int) -> str | None:
    if user.area < required:
        return f"❌ Нужна Area {required} для этой команды."
    return None


# --- /area [num] ---
@router.message(F.text.startswith("/area"))
async def cmd_area(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    if not args:
        area_data = get_area(user.area)
        name = area_data.get("name", f"Area {user.area}") if area_data else f"Area {user.area}"
        next_req = None
        na = get_area(user.area + 1)
        if na:
            next_req = na.get("min_level", 999)
        text = (
            f"📍 <b>Текущая локация</b>\n\n"
            f"  {name} (Area {user.area})\n\n"
            f"  Текстуры: {area_data.get('drops', []) if area_data else '—'}\n"
        )
        if next_req:
            text += f"\n  Следующая: Area {user.area + 1} (Ур. {next_req})"
        else:
            text += f"\n  Максимальная локация!"
        await message.answer(text, parse_mode="HTML")
        return

    try:
        target = int(args[0])
    except ValueError:
        await message.answer("Укажите номер локации: /area [номер]")
        return

    area_data = get_area(target)
    if not area_data:
        await message.answer("❌ Локация не найдена.")
        return

    if user.level < area_data.get("min_level", 1):
        await message.answer(f"❌ Нужен уровень {area_data['min_level']} для Area {target}.")
        return

    async with async_session() as s:
        u = await s.get(User, message.from_user.id)
        u.area = target
        if target > u.max_area:
            u.max_area = target
        await s.commit()

    await message.answer(f"📍 Вы переместились в <b>{area_data.get('name', f'Area {target}')}</b>!", parse_mode="HTML")


# --- /enchant ---
@router.message(F.text.startswith("/enchant sword"))
async def cmd_enchant_sword(message: Message):
    from game.enchant import enchant
    result = await enchant(message.from_user.id, "sword")
    await message.answer(result["message"], parse_mode="HTML")


@router.message(F.text.startswith("/enchant armor"))
async def cmd_enchant_armor(message: Message):
    from game.enchant import enchant
    result = await enchant(message.from_user.id, "armor")
    await message.answer(result["message"], parse_mode="HTML")


@router.message(F.text == "/enchant")
async def cmd_enchant(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 2)
    if err:
        await message.answer(err)
        return

    from game.enchant import ENCHANT_TABLE, ENCHANT_COST, get_available_enchants

    available = get_available_enchants(user.tt_count)

    text = (
        f"✨ <b>Enchant</b>\n\n"
        f"Used to enchant your armor or sword, an enchant will increase your AT (on swords) or DEF (on armors)\n"
        f"Cost: {ENCHANT_COST:,} coins\n\n"
        f"The enchant you will get is random and will be one of the followings:\n"
    )
    for ench in available:
        tt_text = f" [Unlocked in the {ench['tt_req']}{'st' if ench['tt_req'] == 1 else 'th'} time travel]" if ench["tt_req"] > 0 else ""
        text += f"• {ench['name']} (+{ench['bonus_pct']}% AT/DEF){tt_text}\n"

    text += (
        f"\n<b>Usage</b>\n"
        f"<code>enchant sword</code> or <code>enchant armor</code>\n\n"
        f"<b>Higher Tiers</b>\n"
        f"<code>refine</code> — unlocked in area 7, better chances but x10 price\n"
        f"<code>transmute</code> — unlocked in area 13, better chances but x100 price\n"
        f"<code>transcend</code> — unlocked in area 15, better chances but x1000 price"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/refine sword"))
async def cmd_refine_sword(message: Message):
    from game.enchant import refine
    result = await refine(message.from_user.id, "sword")
    await message.answer(result["message"], parse_mode="HTML")


@router.message(F.text.startswith("/refine armor"))
async def cmd_refine_armor(message: Message):
    from game.enchant import refine
    result = await refine(message.from_user.id, "armor")
    await message.answer(result["message"], parse_mode="HTML")


@router.message(F.text.startswith("/transmute sword"))
async def cmd_transmute_sword(message: Message):
    from game.enchant import transmute
    result = await transmute(message.from_user.id, "sword")
    await message.answer(result["message"], parse_mode="HTML")


@router.message(F.text.startswith("/transmute armor"))
async def cmd_transmute_armor(message: Message):
    from game.enchant import transmute
    result = await transmute(message.from_user.id, "armor")
    await message.answer(result["message"], parse_mode="HTML")


@router.message(F.text.startswith("/transcend sword"))
async def cmd_transcend_sword(message: Message):
    from game.enchant import transcend
    result = await transcend(message.from_user.id, "sword")
    await message.answer(result["message"], parse_mode="HTML")


@router.message(F.text.startswith("/transcend armor"))
async def cmd_transcend_armor(message: Message):
    from game.enchant import transcend
    result = await transcend(message.from_user.id, "armor")
    await message.answer(result["message"], parse_mode="HTML")
# --- In-memory training state (user_id -> puzzle) ---
_training_state: dict[int, dict] = {}


@router.message(F.text == "/training")
async def cmd_training(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 2)
    if err:
        await message.answer(err)
        return

    # Check cooldown
    cd = await get_cooldowns(user_id)
    now = datetime.utcnow()
    if cd.last_training and cd.last_training > datetime.min:
        elapsed = (now - cd.last_training).total_seconds()
        if elapsed < config.COOLDOWNS["training"]:
            remaining = int(config.COOLDOWNS["training"] - elapsed)
            m, s = divmod(remaining, 60)
            await message.answer(f"⏳ Тренировка через {m}м {s}с")
            return

    # Set cooldown
    from database.engine import async_session
    from database.models import Cooldown
    async with async_session() as s:
        cd_obj = await s.get(Cooldown, user_id)
        if cd_obj:
            cd_obj.last_training = now
            await s.commit()

    # Get ruby count for Mine Training
    inv = await get_inventory(user_id)
    ruby_count = inv.get("ruby", 0) if inv else 0

    # Generate puzzle
    from game.training import generate_training
    puzzle = generate_training(user.max_area, ruby_count)

    # Store state for callback
    _training_state[user_id] = {
        "answer": puzzle["answer"],
        "max_area": user.max_area,
        "tt_count": user.tt_count,
        "horse_tier": 0,
    }

    # Get horse tier for pet spawn chance
    from database.crud import get_user as _get_user_for_horse
    from sqlalchemy import select
    async with async_session() as s:
        from database.models import Horse
        horse = await s.get(Horse, user_id)
        if horse:
            _training_state[user_id]["horse_tier"] = horse.tier

    if puzzle.get("keyboard"):
        await message.answer(puzzle["message"], parse_mode="HTML", reply_markup=puzzle["keyboard"])
    else:
        await message.answer(puzzle["message"], parse_mode="HTML")


@router.message(F.text == "/ultraining")
async def cmd_ultraining(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 12)
    if err:
        await message.answer(err)
        return

    # Check cooldown
    cd = await get_cooldowns(user_id)
    now = datetime.utcnow()
    if cd.last_training and cd.last_training > datetime.min:
        elapsed = (now - cd.last_training).total_seconds()
        if elapsed < config.COOLDOWNS["training"]:
            remaining = int(config.COOLDOWNS["training"] - elapsed)
            m, s = divmod(remaining, 60)
            await message.answer(f"⏳ Ультратренировка через {m}м {s}с")
            return

    # Set cooldown
    from database.engine import async_session
    from database.models import Cooldown
    async with async_session() as s:
        cd_obj = await s.get(Cooldown, user_id)
        if cd_obj:
            cd_obj.last_training = now
            await s.commit()

    # Ultraining: EPIC NPC fight
    # Player chooses ATTACK, BLOCK, or ATTLOCK
    import random

    # NPC stats scale with player level
    npc_atk = int(user.level * random.uniform(0.8, 1.2))
    npc_def = int(user.level * random.uniform(0.6, 1.0))

    # Double stage chance
    is_double = random.random() < config.ULTRAINING_DOUBLE_CHANCE
    if is_double:
        npc_atk = int(npc_atk * 1.5)
        npc_def = int(npc_def * 1.5)

    # Player stats
    eq = await get_equipment(user_id)
    player_atk = calc_atk(user.level, eq.get("weapon_tier", 1))
    player_def = calc_def(user.level, eq.get("armor_tier", 1))

    # Store for callback
    _training_state[user_id] = {
        "type": "ultraining",
        "npc_atk": npc_atk,
        "npc_def": npc_def,
        "player_atk": player_atk,
        "player_def": player_def,
        "is_double": is_double,
        "max_area": user.max_area,
        "tt_count": user.tt_count,
    }

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="ATTACK (+AT)", callback_data="ultra:attack"),
            InlineKeyboardButton(text="BLOCK (+DEF)", callback_data="ultra:block"),
            InlineKeyboardButton(text="ATTLOCK (balanced)", callback_data="ultra:attlock"),
        ],
    ])

    double_text = " (DOUBLE STAGE!)" if is_double else ""
    await message.answer(
        f"🏋️‍♂️ <b>Ultraining{double_text}</b>\n\n"
        f"EPIC NPC:\n  ATK: {npc_atk}\n  DEF: {npc_def}\n\n"
        f"Ваши статы:\n  ATK: {player_atk}\n  DEF: {player_def}\n\n"
        f"Выберите действие:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def _handle_ultraining_choice(user_id: int, choice: str) -> dict:
    """Resolve ultraining NPC fight based on player's choice."""
    state = _training_state.pop(user_id, None)
    if not state or state.get("type") != "ultraining":
        return {"success": False, "message": "❌ Нет активной ультратренировки."}

    npc_atk = state["npc_atk"]
    npc_def = state["npc_def"]
    player_atk = state["player_atk"]
    player_def = state["player_def"]
    is_double = state["is_double"]
    max_area = state["max_area"]
    tt_count = state["tt_count"]

    # Calculate effective stats based on choice
    if choice == "attack":
        effective_atk = player_atk * 1.5
        effective_def = player_def * 0.7
    elif choice == "block":
        effective_atk = player_atk * 0.7
        effective_def = player_def * 1.5
    else:  # attlock
        effective_atk = player_atk * 1.1
        effective_def = player_def * 1.1

    # Simulate combat: player wins if effective stats > NPC stats
    player_power = effective_atk + effective_def
    npc_power = npc_atk + npc_def
    win = player_power > npc_power

    # XP reward (scales with max_area and TT)
    xp = int((config.TRAINING_XP_BASE + max(0, max_area - 2) * config.TRAINING_XP_PER_AREA) * random.uniform(0.8, 1.2))
    from game.player import get_tt_xp_bonus
    tt_mult = 1 + get_tt_xp_bonus(tt_count)
    xp = int(xp * tt_mult)

    if win:
        coolness = config.ULTRAINING_DOUBLE_COOLNESS if is_double else config.ULTRAINING_COOLNESS
        await add_xp(user_id, xp)

        from database.engine import async_session
        from database.models import User
        async with async_session() as s:
            u = await s.get(User, user_id)
            if u:
                u.coolness += coolness
                await s.commit()

        msg = (
            f"🏋️‍♂️ <b>Ultraining — Победа!</b>\n\n"
            f"{'🎯 DOUBLE STAGE! ' if is_double else ''}"
            f"+{xp} XP, +{coolness} coolness"
        )
    else:
        msg = (
            f"🏋️‍♂️ <b>Ultraining — Поражение</b>\n\n"
            f"EPIC NPC оказался сильнее.\n"
            f"Попробуйте снова через 15 мин."
        )

    return {"success": True, "message": msg}


# --- Callback handlers for training ---
@router.callback_query(F.data.startswith("train:"))
async def cb_training_answer(callback: CallbackQuery):
    user_id = callback.from_user.id
    state = _training_state.pop(user_id, None)

    if not state:
        await callback.answer("Нет активной тренировки.", show_alert=True)
        return

    answer = callback.data.split(":", 1)[1]
    correct = state["answer"]

    if answer.lower() == correct.lower():
        # Success
        xp = calc_training_xp(state["max_area"], state["tt_count"])
        await add_xp(user_id, xp)

        msg = f"🎉 <b>Тренировка пройдена!</b>\n\n+{xp} XP"

        # Pet spawn chance
        pet_chance = get_pet_spawn_chance(state["tt_count"], state["horse_tier"])
        if pet_chance > 0 and random.random() < pet_chance:
            from game.pets import catch_pet
            pet_result = await catch_pet(user_id, state["max_area"])
            if pet_result.get("caught"):
                msg += f"\n\n🐾 ПОЙМАН ПИТОМЕЦ: {pet_result['emoji']} {pet_result['name']} (Tier {pet_result['pet_tier']})!"
            elif pet_result.get("reason") == "max_pets":
                msg += "\n\n❌ Инвентарь питомцев полон! /pets release [id]"

        await callback.message.edit_text(msg, parse_mode="HTML")
    else:
        await callback.message.edit_text(
            f"❌ <b>Неверный ответ!</b>\n\nПравильный: {correct}\nПопробуйте через 15 мин."
        )

    await callback.answer()


@router.callback_query(F.data.startswith("ultra:"))
async def cb_ultraining_answer(callback: CallbackQuery):
    user_id = callback.from_user.id
    choice = callback.data.split(":", 1)[1]
    result = await _handle_ultraining_choice(user_id, choice)
    await callback.message.edit_text(result["message"], parse_mode="HTML")
    await callback.answer()


# --- /axe (upgrade axe tool) ---


# --- /axe (upgrade axe tool) ---
@router.message(F.text == "/axe")
async def cmd_axe(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 3)
    if err:
        await message.answer(err)
        return

    tools = await get_tools(message.from_user.id)
    current = tools.get("axe", 1)
    cost = current * 500
    if user.coins < cost:
        await message.answer(f"❌ Улучшение топора до {current + 1} уровня: {cost} монет.")
        return

    await remove_coins(message.from_user.id, cost)
    tools["axe"] = current + 1
    await set_tools(message.from_user.id, tools)
    await message.answer(f"🪓 Топор улучшен до уровня {current + 1}! (-{cost} монет)")


# --- /net ---
@router.message(F.text == "/net")
async def cmd_net(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 3)
    if err:
        await message.answer(err)
        return

    # Net: catch fish with reduced cooldown
    from game.work import gather_resources
    result = await gather_resources(message.from_user.id, "fish", user.area)
    await message.answer(result["message"])


# --- /pickup ---
@router.message(F.text == "/pickup")
async def cmd_pickup(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 3)
    if err:
        await message.answer(err)
        return

    # Gather all resource types at once
    from game.work import gather_resources
    results = []
    for action in ["chop", "mine", "fish"]:
        r = await gather_resources(message.from_user.id, action, user.area)
        results.append(r["message"])
    await message.answer("📦 <b>Сбор ресурсов:</b>\n\n" + "\n\n".join(results), parse_mode="HTML")


# --- /ladder ---
@router.message(F.text == "/ladder")
async def cmd_ladder(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 4)
    if err:
        await message.answer(err)
        return

    if random.random() < 0.6:
        xp = user.level * 10
        await add_xp(message.from_user.id, xp)
        await message.answer(f"🪜 Лестница: Вы нашли скрытую площадку! +{xp} XP")
    else:
        dmg = random.randint(5, 20)
        await message.answer(f"🪜 Лестница: Вы упали! -{dmg} HP (косметически)")


# --- /farm ---
@router.message(F.text == "/farm")
@router.message(F.text.startswith("/farm "))
async def cmd_farm(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 4)
    if err:
        await message.answer(err)
        return

    args = message.text.split()[1:]
    seed_type = args[0] if args else ""

    from game.farm import farm
    result = await farm(message.from_user.id, seed_type=seed_type)
    await message.answer(result["message"], parse_mode="HTML")


# --- /multidice ---
@router.message(F.text.startswith("/multidice"))
async def cmd_multidice(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 5)
    if err:
        await message.answer(err)
        return

    bet = int(args[0]) if args else 0
    if bet < config.GAMBLING_MIN_BET:
        await message.answer(f"❌ Минимум ставка: {config.GAMBLING_MIN_BET}")
        return
    if user.coins < bet:
        await message.answer("❌ Недостаточно монет.")
        return

    await remove_coins(message.from_user.id, bet)
    rolls = [random.randint(1, 6) for _ in range(3)]
    total = sum(rolls)

    if total > 12:
        winnings = bet * 3
        await add_coins(message.from_user.id, winnings)
        from game.quest import on_gambling_win
        await on_gambling_win(message.from_user.id, winnings)
        text = f"🎲 <b>Multi Dice</b>\n\n[{rolls[0]}] [{rolls[1]}] [{rolls[2]}] = {total}\n\n🎉 Выигрыш: +{winnings} монет!"
    elif total == 12:
        winnings = bet * 2
        await add_coins(message.from_user.id, winnings)
        from game.quest import on_gambling_win
        await on_gambling_win(message.from_user.id, winnings)
        text = f"🎲 <b>Multi Dice</b>\n\n[{rolls[0]}] [{rolls[1]}] [{rolls[2]}] = {total}\n\n🎉 Выигрыш: +{winnings} монет!"
    else:
        text = f"🎲 <b>Multi Dice</b>\n\n[{rolls[0]}] [{rolls[1]}] [{rolls[2]}] = {total}\n\n💀 Проигрыш: -{bet} монет."

    await message.answer(text, parse_mode="HTML")


# --- /cook ---
@router.message(F.text.startswith("/cook"))
async def cmd_cook(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 5)
    if err:
        await message.answer(err)
        return

    if not args:
        text = "🍳 <b>Рецепты готовки</b>\n\n"
        for name, recipe in config.COOK_RECIPES.items():
            mats = ", ".join(f"{k}: {v}" for k, v in recipe["materials"].items())
            text += f"  {recipe['name']} ({recipe['buff']}) — {mats}\n"
        text += "\nГотовить: /cook [рецепт]"
        await message.answer(text, parse_mode="HTML")
        return

    recipe_name = args[0]
    recipe = config.COOK_RECIPES.get(recipe_name)
    if not recipe:
        await message.answer("❌ Неизвестный рецепт. Доступные: " + ", ".join(config.COOK_RECIPES.keys()))
        return

    inv = await get_inventory(message.from_user.id)
    for mat, amt in recipe["materials"].items():
        if inv.get(mat, 0) < amt:
            await message.answer(f"❌ Недостаточно {mat}. Нужно {amt}.")
            return

    for mat, amt in recipe["materials"].items():
        await remove_materials(message.from_user.id, mat, amt)

    await message.answer(
        f"🍳 Приготовлено: <b>{recipe['name']}</b>!\n"
        f"Бафф: {recipe['buff']}",
        parse_mode="HTML"
    )

    # Quest hook
    from game.quest import on_cook
    await on_cook(message.from_user.id, recipe_name)


# --- /bowsaw ---
@router.message(F.text == "/bowsaw")
async def cmd_bowsaw(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 6)
    if err:
        await message.answer(err)
        return

    tools = await get_tools(message.from_user.id)
    current = tools.get("axe", 1)
    cost = current * 1000
    if user.coins < cost:
        await message.answer(f"❌ Улучшение бензопилы: {cost} монет.")
        return

    await remove_coins(message.from_user.id, cost)
    tools["axe"] = current + 2
    await set_tools(message.from_user.id, tools)
    await message.answer(f"🪚 Бензопила улучшена! Уровень топора: {current + 2} (-{cost} монет)")


# --- /boat ---
@router.message(F.text == "/boat")
async def cmd_boat(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 6)
    if err:
        await message.answer(err)
        return

    from game.work import gather_resources
    result = await gather_resources(message.from_user.id, "fish", user.area)
    await message.answer(result["message"])


# --- /pickaxe (upgrade) ---
@router.message(F.text == "/pickaxe")
async def cmd_pickaxe(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 6)
    if err:
        await message.answer(err)
        return

    tools = await get_tools(message.from_user.id)
    current = tools.get("pickaxe", 1)
    cost = current * 800
    if user.coins < cost:
        await message.answer(f"❌ Улучшение кирки: {cost} монет.")
        return

    await remove_coins(message.from_user.id, cost)
    tools["pickaxe"] = current + 1
    await set_tools(message.from_user.id, tools)
    await message.answer(f"⛏️ Кирка улучшена до уровня {current + 1}! (-{cost} монет)")


# --- /refine ---
@router.message(F.text.startswith("/refine"))
async def cmd_refine(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 7)
    if err:
        await message.answer(err)
        return

    if not args:
        text = "⚒️ <b>Переплавка (5:1)</b>\n\n"
        for low, high in config.REFINE_TYPES:
            text += f"  {low} → {high}\n"
        text += "\nИспользовать: /refine [материал]"
        await message.answer(text, parse_mode="HTML")
        return

    material = args[0]
    pair = None
    for low, high in config.REFINE_TYPES:
        if low == material:
            pair = (low, high)
            break

    if not pair:
        await message.answer("❌ Этот материал нельзя переплавить.")
        return

    inv = await get_inventory(message.from_user.id)
    if inv.get(material, 0) < config.REFINE_COST:
        await message.answer(f"❌ Нужно {config.REFINE_COST}x {material}.")
        return

    await remove_materials(message.from_user.id, material, config.REFINE_COST)
    await add_materials(message.from_user.id, pair[1], 1)
    await message.answer(f"⚒️ {config.REFINE_COST}x {pair[0]} → 1x {pair[1]}")


# --- /big_arena ---
@router.message(F.text == "/big_arena")
async def cmd_big_arena(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 7)
    if err:
        await message.answer(err)
        return

    from game.arena import arena_fight
    result = await arena_fight(message.from_user.id)
    text = result["log"]
    if result["victory"]:
        text += f"\n\n🎉 Победа! +{result['coins']} монет, +{result['xp']} XP"
    else:
        text += "\n\n💀 Поражение!"
    await message.answer(text)


# --- /tractor ---
@router.message(F.text == "/tractor")
async def cmd_tractor(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 8)
    if err:
        await message.answer(err)
        return

    wood = random.randint(30, 80)
    stone = random.randint(20, 50)
    iron = random.randint(5, 15)
    await add_materials(message.from_user.id, "wooden_log", wood)
    await add_materials(message.from_user.id, "potato", stone)
    await add_materials(message.from_user.id, "carrot", iron)
    await message.answer(
        f"🚜 <b>Трактор</b>\n\n"
        f"🪵 +{wood} wooden_log\n"
        f"🥔 +{stone} potato\n"
        f"🥕 +{iron} carrot"
    )


# --- /wheel ---
@router.message(F.text == "/wheel")
async def cmd_wheel(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 8)
    if err:
        await message.answer(err)
        return
    if user.coins < 100:
        await message.answer("❌ Нужно 100 монет.")
        return

    await remove_coins(message.from_user.id, 100)
    prizes = [
        ("💎 1000 монет", 1000),
        ("🪵 50 дерева", 0),
        ("⛓️ 20 железа", 0),
        ("💀 Ничего", 0),
        ("💎 500 монет", 500),
        ("🔥 50 XP", 0),
    ]
    idx = random.randint(0, len(prizes) - 1)
    prize_name, coins = prizes[idx]

    if coins > 0:
        await add_coins(message.from_user.id, coins)
    elif "XP" in prize_name:
        xp = 50
        await add_xp(message.from_user.id, xp)

    await message.answer(f"🎡 <b>Колесо Фортуны</b>\n\nВыпало: {prize_name}")


# --- /chainsaw ---
@router.message(F.text == "/chainsaw")
async def cmd_chainsaw(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 9)
    if err:
        await message.answer(err)
        return

    tools = await get_tools(message.from_user.id)
    current = tools.get("axe", 1)
    cost = current * 2000
    if user.coins < cost:
        await message.answer(f"❌ Улучшение бензопилы v2: {cost} монет.")
        return

    await remove_coins(message.from_user.id, cost)
    tools["axe"] = current + 3
    await set_tools(message.from_user.id, tools)
    await message.answer(f"🪚 Бензопила v2! Уровень топора: {current + 3} (-{cost} монет)")


# --- /bigboat ---
@router.message(F.text == "/bigboat")
async def cmd_bigboat(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 9)
    if err:
        await message.answer(err)
        return

    from game.work import gather_resources
    result = await gather_resources(message.from_user.id, "fish", user.area)
    await message.answer(result["message"])


# --- /drill ---
@router.message(F.text == "/drill")
async def cmd_drill(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 10)
    if err:
        await message.answer(err)
        return

    tools = await get_tools(message.from_user.id)
    current = tools.get("pickaxe", 1)
    cost = current * 3000
    if user.coins < cost:
        await message.answer(f"❌ Улучшение дрели: {cost} монет.")
        return

    await remove_coins(message.from_user.id, cost)
    tools["pickaxe"] = current + 2
    await set_tools(message.from_user.id, tools)
    await message.answer(f"🔩 Дрель! Уровень кирки: {current + 2} (-{cost} монет)")


# --- /minintboss ---
@router.message(F.text == "/minintboss")
async def cmd_minintboss(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 10)
    if err:
        await message.answer(err)
        return

    from game.arena import miniboss_fight
    result = await miniboss_fight(message.from_user.id)
    text = result["log"]
    if result["victory"]:
        text += f"\n\n🎉 Победа! +{result['coins']} монет, +{result['xp']} XP"
    else:
        text += "\n\n💀 Поражение!"
    await message.answer(text)


# --- /forge ---
@router.message(F.text == "/forge")
@router.message(F.text.startswith("/forge "))
async def cmd_forge(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 11)
    if err:
        await message.answer(err)
        return

    recipes = load_recipes()
    forge = recipes.get("forge", {})

    if not args:
        text = "🔨 <b>Кузница (Forge)</b>\n\n"
        for tier_str, r in sorted(forge.items(), key=lambda x: int(x[0])):
            if user.level < r["level"]:
                text += f"🔒 Lvl {r['level']} — {r['weapon_name']} / {r['armor_name']}\n"
            else:
                w_mats = ", ".join(f"{k}: {v}" for k, v in r["weapon_materials"].items())
                text += f"⚔️ Lvl {r['level']} — {r['weapon_name']} ({r['weapon_atk']} at)\n   {w_mats}\n"
                a_mats = ", ".join(f"{k}: {v}" for k, v in r["armor_materials"].items())
                text += f"🛡️ Lvl {r['level']} — {r['armor_name']} ({r['armor_def']} def)\n   {a_mats}\n"
        text += "\nКовать: /forge [уровень]"
        await message.answer(text, parse_mode="HTML")
        return

    try:
        tier = int(args[0])
    except ValueError:
        await message.answer("Формат: /forge [уровень] (70, 100, 200, 500)")
        return

    recipe = forge.get(str(tier))
    if not recipe:
        await message.answer("❌ Рецепт не найден. Доступные: " + ", ".join(forge.keys()))
        return

    if user.level < recipe["level"]:
        await message.answer(f"❌ Нужен уровень {recipe['level']}.")
        return

    eq = await get_equipment(message.from_user.id)
    current_weapon = eq.get("weapon_tier", 0)

    if len(args) > 1 and args[1].lower() in ("armor", "def"):
        craft_type = "armor"
    elif current_weapon >= tier:
        craft_type = "armor"
    else:
        craft_type = "weapon"

    if craft_type == "weapon":
        mats = recipe.get("weapon_materials", {})
        result_name = recipe["weapon_name"]
        result_stat = f"{recipe['weapon_atk']} ATK"
    else:
        mats = recipe.get("armor_materials", {})
        result_name = recipe["armor_name"]
        result_stat = f"{recipe['armor_def']} DEF"

    inv = await get_inventory(message.from_user.id)
    for mat, amt in mats.items():
        if inv.get(mat, 0) < amt:
            await message.answer(f"❌ Недостаточно {mat}. Нужно {amt}, есть {inv.get(mat, 0)}.")
            return

    for mat, amt in mats.items():
        await remove_materials(message.from_user.id, mat, amt)

    new_eq = dict(eq)
    if craft_type == "weapon":
        new_eq["weapon_tier"] = tier
    else:
        new_eq["armor_tier"] = tier
    await set_equipment(message.from_user.id, new_eq)

    await message.answer(
        f"🔨 <b>Кузница</b>\n\nВыковано: {result_name} ({result_stat})!",
        parse_mode="HTML"
    )


# --- /voidforge ---
@router.message(F.text == "/voidforge")
@router.message(F.text.startswith("/voidforge "))
async def cmd_voidforge(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 16)
    if err:
        await message.answer(err)
        return

    recipes = load_recipes()
    voidforge = recipes.get("voidforge", {})

    if not args:
        text = "🌀 <b>Void Forge</b>\n\n"
        for key, r in sorted(voidforge.items(), key=lambda x: _vf_area(x[1])):
            area = r.get("area", 0)
            if user.area < area:
                text += f"🔒 Area {area} — "
            else:
                text += f"✅ Area {area} — "
            if "weapon" in r and "weapon_name" in r:
                text += f"⚔️ {r['weapon_name']} ({r['weapon_atk']} ATK)\n"
            else:
                text += f"🛡️ {r['armor_name']} ({r['armor_def']} DEF)\n"
            mats = r.get("weapon_materials", r.get("armor_materials", {}))
            mat_str = ", ".join(f"{k}: {v}" for k, v in mats.items())
            text += f"   {mat_str}\n"
        text += "\nКовать: /voidforge [area] [weapon|armor]\n"
        text += "Пример: /voidforge 16 weapon"
        await message.answer(text, parse_mode="HTML")
        return

    if len(args) < 1:
        await message.answer("Формат: /voidforge [area] [weapon|armor]\nПример: /voidforge 16 weapon")
        return

    try:
        area = int(args[0])
    except ValueError:
        await message.answer("❌ Введите номер area (16-20).")
        return

    if user.area < area:
        await message.answer(f"❌ Нужна Area {area} для этой команды.")
        return

    # Determine weapon or armor
    craft_type = "weapon"
    if len(args) > 1 and args[1].lower() in ("armor", "def"):
        craft_type = "armor"

    # Find matching recipe
    recipe = None
    for key, r in voidforge.items():
        if r.get("area") == area:
            if craft_type == "weapon" and "weapon" in r and "weapon_name" in r:
                recipe = r
                break
            elif craft_type == "armor" and "armor" in r and "armor_name" in r:
                recipe = r
                break

    if not recipe:
        await message.answer(f"❌ Рецепт не найден для Area {area} ({craft_type}).")
        return

    # Check TT requirement
    tt_min = recipe.get("tt_min", 0)
    if tt_min and user.time_travel < tt_min:
        await message.answer(f"❌ Нужно Time Travel ×{tt_min}. У вас: {user.time_travel}")
        return

    # Check base equipment requirement
    requires = recipe.get("requires", {})
    eq = await get_equipment(message.from_user.id)
    if craft_type == "weapon":
        base_item = requires.get("weapon")
        if base_item:
            # Check if player has the required weapon tier (by name mapping)
            req_tier = _weapon_name_to_tier(base_item)
            if req_tier and eq.get("weapon_tier", 0) < req_tier:
                await message.answer(f"❌ Нужно иметь: {base_item}")
                return
    else:
        base_item = requires.get("armor")
        if base_item:
            req_tier = _armor_name_to_tier(base_item)
            if req_tier and eq.get("armor_tier", 0) < req_tier:
                await message.answer(f"❌ Нужно иметь: {base_item}")
                return

    # Check materials
    if craft_type == "weapon":
        mats = recipe.get("weapon_materials", {})
        result_name = recipe["weapon_name"]
        result_stat = f"{recipe['weapon_atk']} ATK"
    else:
        mats = recipe.get("armor_materials", {})
        result_name = recipe["armor_name"]
        result_stat = f"{recipe['armor_def']} DEF"

    inv = await get_inventory(message.from_user.id)
    for mat, amt in mats.items():
        if inv.get(mat, 0) < amt:
            mat_display = _mat_name(mat)
            await message.answer(f"❌ Недостаточно {mat_display}. Нужно {amt}, есть {inv.get(mat, 0)}.")
            return

    for mat, amt in mats.items():
        await remove_materials(message.from_user.id, mat, amt)

    new_eq = dict(eq)
    if craft_type == "weapon":
        new_eq["weapon_tier"] = recipe.get("weapon_tier", area)
    else:
        new_eq["armor_tier"] = recipe.get("armor_tier", area)
    await set_equipment(message.from_user.id, new_eq)

    await message.answer(
        f"🌀 <b>Void Forge</b>\n\nВыковано: {result_name} ({result_stat})!",
        parse_mode="HTML"
    )


def _vf_area(recipe: dict) -> int:
    return recipe.get("area", 0)


def _weapon_name_to_tier(name: str) -> int | None:
    """Map a weapon name to its tier number."""
    mapping = {
        "basic_sword": 1, "fish_sword": 2, "apple_sword": 4, "zombie_sword": 6,
        "ruby_sword": 8, "unicorn_sword": 11, "hair_sword": 14, "coin_sword": 17,
        "electronical_sword": 20, "edgy_sword": 50,
        "ultra_edgy_sword": 70, "omega_sword": 100, "ultra_omega_sword": 200, "godly_sword": 500,
    }
    return mapping.get(name)


def _armor_name_to_tier(name: str) -> int | None:
    """Map an armor name to its tier number."""
    mapping = {
        "fish_armor": 1, "wolf_armor": 2, "eye_armor": 4, "banana_armor": 6,
        "epic_armor": 8, "ruby_armor": 11, "coin_armor": 14, "mermaid_armor": 17,
        "electronical_armor": 20, "edgy_armor": 50,
        "ultra_edgy_armor": 70, "omega_armor": 100, "ultra_omega_armor": 200,
    }
    return mapping.get(name)


def _mat_name(mat_id: str) -> str:
    with open(DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
        mat_names = json.load(f).get("names", {})
    return mat_names.get(mat_id, mat_id.replace("_", " ").title())
@router.message(F.text == "/greenhouse")
async def cmd_greenhouse(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 11)
    if err:
        await message.answer(err)
        return
    if user.coins < config.GREENHOUSE_COST:
        await message.answer(f"❌ Нужно {config.GREENHOUSE_COST} монет.")
        return

    await remove_coins(message.from_user.id, config.GREENHOUSE_COST)
    for mat, amt in config.GREENHOUSE_YIELD.items():
        await add_materials(message.from_user.id, mat, amt)
    await message.answer(
        f"🌿 <b>Оранжерея</b>\n\n"
        f"Выращено ресурсов за {config.GREENHOUSE_DURATION // 60} мин:\n"
        + "\n".join(f"  {k}: +{v}" for k, v in config.GREENHOUSE_YIELD.items()) +
        f"\n\n(-{config.GREENHOUSE_COST} монет)"
    )


# --- /dynamite ---
@router.message(F.text == "/dynamite")
async def cmd_dynamite(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 12)
    if err:
        await message.answer(err)
        return

    inv = await get_inventory(message.from_user.id)
    if inv.get("ruby", 0) < 3:
        await message.answer("❌ Нужно 3x ruby для динамита.")
        return

    await remove_materials(message.from_user.id, "ruby", 3)
    wood = random.randint(30, 80)
    mega_log = random.randint(5, 15)
    await add_materials(message.from_user.id, "wooden_log", wood)
    await add_materials(message.from_user.id, "mega_log", mega_log)
    await message.answer(
        f"💥 <b>Динамит</b>\n\n"
        f"🪵 +{wood} wooden_log\n"
        f"🪵 +{mega_log} mega_log"
    )


# --- /badge ---
@router.message(F.text == "/badge")
async def cmd_badge(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 12)
    if err:
        await message.answer(err)
        return

    if random.random() < 0.3:
        async with async_session() as s:
            u = await s.get(User, message.from_user.id)
            u.coolness += 5
            await s.commit()
        await message.answer("🏅 Бейдж получен! +5 coolness")
    else:
        await message.answer("❌ Бейдж не выпал. Попробуйте ещё раз.")


# --- /transmute ---
@router.message(F.text.startswith("/transmute"))
async def cmd_transmute(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 13)
    if err:
        await message.answer(err)
        return

    if not args:
        await message.answer("Формат: /transmute [материал]\n5x любого → 1x следующего тира")
        return

    material = args[0]
    pair = None
    for low, high in config.REFINE_TYPES:
        if low == material:
            pair = (low, high)
            break

    if not pair:
        await message.answer("❌ Этот материал нельзя трансмутировать.")
        return

    inv = await get_inventory(message.from_user.id)
    if inv.get(material, 0) < config.TRANSMUTE_RATE:
        await message.answer(f"❌ Нужно {config.TRANSMUTE_RATE}x {material}.")
        return

    await remove_materials(message.from_user.id, material, config.TRANSMUTE_RATE)
    await add_materials(message.from_user.id, pair[1], 1)
    await message.answer(f"🔮 {config.TRANSMUTE_RATE}x {pair[0]} → 1x {pair[1]}")


# --- /big_dice ---
@router.message(F.text.startswith("/big_dice"))
async def cmd_big_dice(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 14)
    if err:
        await message.answer(err)
        return

    bet = int(args[0]) if args else 0
    if bet < config.GAMBLING_MIN_BET:
        await message.answer(f"❌ Минимум ставка: {config.GAMBLING_MIN_BET}")
        return
    if user.coins < bet:
        await message.answer("❌ Недостаточно монет.")
        return

    await remove_coins(message.from_user.id, bet)
    player = random.randint(1, 20)
    bot = random.randint(1, 20)

    if player > bot:
        winnings = bet * 3
        await add_coins(message.from_user.id, winnings)
        from game.quest import on_gambling_win
        await on_gambling_win(message.from_user.id, winnings)
        text = f"🎲 <b>Big Dice</b>\n\nВы: {player} | Бот: {bot}\n\n🎉 Выигрыш: +{winnings} монет!"
    elif player == bot:
        await add_coins(message.from_user.id, bet)
        text = f"🎲 <b>Big Dice</b>\n\nВы: {player} | Бот: {bot}\n\n🤝 Ничья!"
    else:
        text = f"🎲 <b>Big Dice</b>\n\nВы: {player} | Бот: {bot}\n\n💀 Проигрыш: -{bet} монет."

    await message.answer(text, parse_mode="HTML")


# --- /alchemy ---
@router.message(F.text == "/alchemy")
@router.message(F.text.startswith("/alchemy "))
async def cmd_alchemy(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 7)
    if err:
        await message.answer(err)
        return

    if not args:
        text = (
            "🧪 <b>Алхимия</b>\n\n"
            "Конвертирует предметы в редкие ресурсы.\n\n"
            "Рецепты:\n"
            "  /alchemy ruby — 50 wooden_log → 1 ruby\n"
            "  /alchemy unicornhorn — 100 golden_fish → 1 unicornhorn\n"
            "  /alchemy mermaid_hair — 100 epic_fish → 1 mermaid_hair\n"
            "  /alchemy dragonscale — 50 banana + 50 apple → 1 dragonscale\n"
            "  /alchemy chip — 200 bread → 1 chip"
        )
        await message.answer(text, parse_mode="HTML")
        return

    recipe_name = args[0].lower()
    inv = await get_inventory(message.from_user.id)

    alchemy_recipes = {
        "ruby": {"wooden_log": 50},
        "unicornhorn": {"golden_fish": 100},
        "mermaid_hair": {"epic_fish": 100},
        "dragonscale": {"banana": 50, "apple": 50},
        "chip": {"bread": 200},
    }

    recipe = alchemy_recipes.get(recipe_name)
    if not recipe:
        await message.answer("❌ Неизвестный рецепт. Доступные: " + ", ".join(alchemy_recipes.keys()))
        return

    # Check materials
    for mat, amt in recipe.items():
        if inv.get(mat, 0) < amt:
            await message.answer(f"❌ Нужно {amt}x {mat}, у вас {inv.get(mat, 0)}.")
            return

    # Consume
    for mat, amt in recipe.items():
        await remove_materials(message.from_user.id, mat, amt)
    await add_materials(message.from_user.id, recipe_name, 1)

    await message.answer(f"🧪 Алхимия: {' + '.join(f'{v}x {k}' for k, v in recipe.items())} → 1x {recipe_name}")


# --- /alchemy ---
ALCHEMY_RECIPES = {
    "life_potion": {
        "name": "Зелье жизни",
        "materials": {"apple": 10, "banana": 5, "normie_fish": 8},
        "result": "life_potion",
        "result_emoji": "🧪",
        "result_amount": 1,
        "area": 7,
    },
    "golden_potion": {
        "name": "Золотое зелье",
        "materials": {"golden_fish": 5, "apple": 20, "ruby": 1},
        "result": "coins",
        "result_emoji": "💰",
        "result_amount": 1000,
        "area": 7,
    },
    "epic_lootbox": {
        "name": "Эпичный лутбокс",
        "materials": {"epic_fish": 3, "unicornhorn": 1, "ruby": 2},
        "result": "epic_lootbox",
        "result_emoji": "📦",
        "result_amount": 1,
        "area": 7,
    },
    "rare_lootbox": {
        "name": "Редкий лутбокс",
        "materials": {"golden_fish": 10, "wolfskin": 3, "carrot": 15},
        "result": "rare_lootbox",
        "result_emoji": "📦",
        "result_amount": 1,
        "area": 7,
    },
    "lotteryticket": {
        "name": "Лотерейный билет",
        "materials": {"coin": 100, "epic_log": 2},
        "result": "lotteryticket",
        "result_emoji": "🎟️",
        "result_amount": 1,
        "area": 7,
    },
}


@router.message(F.text == "/alchemy")
@router.message(F.text.startswith("/alchemy "))
async def cmd_alchemy(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 7)
    if err:
        await message.answer(err)
        return

    if not args:
        text = "⚗️ <b>Алхимия</b>\n\n"
        for key, recipe in ALCHEMY_RECIPES.items():
            mats = ", ".join(f"{k}: {v}" for k, v in recipe["materials"].items())
            text += f"  {recipe['result_emoji']} {recipe['name']} — {mats}\n"
        text += "\nСоздать: /alchemy [рецепт]"
        await message.answer(text, parse_mode="HTML")
        return

    recipe_name = args[0]
    recipe = ALCHEMY_RECIPES.get(recipe_name)
    if not recipe:
        await message.answer("❌ Неизвестный рецепт. Доступные: " + ", ".join(ALCHEMY_RECIPES.keys()))
        return

    inv = await get_inventory(message.from_user.id)
    for mat, amt in recipe["materials"].items():
        if inv.get(mat, 0) < amt:
            await message.answer(f"❌ Недостаточно {mat}. Нужно {amt}.")
            return

    for mat, amt in recipe["materials"].items():
        await remove_materials(message.from_user.id, mat, amt)

    if recipe["result"] == "coins":
        await add_coins(message.from_user.id, recipe["result_amount"])
        await message.answer(
            f"⚗️ <b>Алхимия</b>\n\nСоздано: {recipe['result_emoji']} {recipe['name']}!\n"
            f"+{recipe['result_amount']} монет",
            parse_mode="HTML"
        )
    else:
        await add_materials(message.from_user.id, recipe["result"], recipe["result_amount"])
        await message.answer(
            f"⚗️ <b>Алхимия</b>\n\nСоздано: {recipe['result_emoji']} {recipe['name']} × {recipe['result_amount']}!",
            parse_mode="HTML"
        )


# --- /hunt hardmode ---
@router.message(F.text.startswith("/hunt hardmode"))
async def cmd_hunt_hardmode(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 13)
    if err:
        await message.answer(err)
        return

    eq = await get_equipment(message.from_user.id)
    player_atk = calc_atk(user.level, eq.get("weapon_tier", 1))
    player_def = calc_def(user.level, eq.get("armor_tier", 1))

    # Hardmode mobs are 3x stronger
    mob_hp = user.level * 30
    mob_atk = user.level * 8
    mob_def = user.level * 3

    log = [f"💀 <b>Hunt HARDMODE</b>"]

    player_hp = 100 + user.level * 5
    for rnd in range(1, 11):
        dmg = max(1, math.floor((player_atk - mob_def / 2) * random.uniform(0.85, 1.15)))
        mob_hp -= dmg
        log.append(f"Раунд {rnd}: Вы наносите {dmg} урона.")
        if mob_hp <= 0:
            break

        dmg2 = max(1, math.floor((mob_atk - player_def / 2) * random.uniform(0.85, 1.15)))
        player_hp -= dmg2
        log.append(f"Раунд {rnd}: Моб наносит {dmg2} урона.")
        if player_hp <= 0:
            break

    if mob_hp <= 0:
        xp = int(user.level * 40 * 3)
        coins_reward = int(user.level * 15 * 3)
        await add_xp(message.from_user.id, xp)
        await add_coins(message.from_user.id, coins_reward)

        # Better drops
        from game.work import _get_log_tier
        log_tier = _get_log_tier(user.area)
        drop_amt = random.randint(5, 15)
        await add_materials(message.from_user.id, log_tier, drop_amt)

        text = "\n".join(log)
        text += f"\n\n🎉 Победа! +{xp} XP, +{coins_reward} монет, +{drop_amt} {log_tier}"
    else:
        text = "\n".join(log)
        text += "\n\n💀 Поражение!"

    await message.answer(text, parse_mode="HTML")


# --- /adventure hardmode ---
@router.message(F.text.startswith("/adventure hardmode"))
async def cmd_adventure_hardmode(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return
    err = _check_area(user, 14)
    if err:
        await message.answer(err)
        return

    eq = await get_equipment(message.from_user.id)
    player_atk = calc_atk(user.level, eq.get("weapon_tier", 1))
    player_def = calc_def(user.level, eq.get("armor_tier", 1))

    # Adventure hardmode: 3 bosses, scaled harder
    bosses = [
        {"name": "ЗОМБИ-КОРОЛЬ", "emoji": "🧟", "hp_mult": 3.0, "atk_mult": 2.5, "def_mult": 1.5},
        {"name": "ДРАКОН", "emoji": "🐉", "hp_mult": 4.0, "atk_mult": 3.0, "def_mult": 2.0},
        {"name": "ЛОРД ТЬМЫ", "emoji": "👿", "hp_mult": 5.0, "atk_mult": 3.5, "def_mult": 2.5},
    ]
    boss = random.choice(bosses)

    boss_hp = user.level * 10 * boss["hp_mult"]
    boss_atk = user.level * 6 * boss["atk_mult"]
    boss_def = user.level * 2 * boss["def_mult"]

    log = [f"⚔️ <b>Adventure HARDMODE</b>"]
    log.append(f"Встречен: {boss['emoji']} {boss['name']} (HP: {int(boss_hp)})")

    player_hp = 100 + user.level * 5
    for rnd in range(1, 16):
        dmg = max(1, math.floor((player_atk - boss_def / 2) * random.uniform(0.85, 1.15)))
        boss_hp -= dmg
        log.append(f"Раунд {rnd}: Вы наносите {dmg} урона.")
        if boss_hp <= 0:
            break

        dmg2 = max(1, math.floor((boss_atk - player_def / 2) * random.uniform(0.85, 1.15)))
        player_hp -= dmg2
        log.append(f"Раунд {rnd}: {boss['name']} наносит {dmg2} урона.")
        if player_hp <= 0:
            break

    if boss_hp <= 0:
        xp = int(user.level * 80 * 3)
        coins_reward = int(user.level * 40 * 3)
        await add_xp(message.from_user.id, xp)
        await add_coins(message.from_user.id, coins_reward)

        # Rare drops from hardmode
        drops = []
        if random.random() < 0.3:
            await add_materials(message.from_user.id, "ruby", 1)
            drops.append("💎 +1 ruby")
        if random.random() < 0.2:
            await add_materials(message.from_user.id, "unicornhorn", 1)
            drops.append("🦄 +1 unicornhorn")
        if random.random() < 0.25:
            await add_materials(message.from_user.id, "epic_log", random.randint(2, 5))
            drops.append(f"🪵 +epic_log")
        await add_materials(message.from_user.id, "coin", random.randint(50, 200))
        drops.append("🪙 +coin")

        text = "\n".join(log)
        text += f"\n\n🎉 Победа! +{xp} XP, +{coins_reward} монет"
        if drops:
            text += "\n" + "\n".join(drops)
    else:
        text = "\n".join(log)
        text += "\n\n💀 Поражение!"

    await message.answer(text, parse_mode="HTML")
