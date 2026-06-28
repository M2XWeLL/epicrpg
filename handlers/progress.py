"""
Progress commands: inventory, top, title, professions, quest, horse, boosts, artifacts, achievements, cards.
"""
import json
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user, get_equipment, get_tools, get_inventory
from game.player import add_coins as _add_coins, add_xp as _add_xp
from database.engine import async_session
from database.models import User, Horse
from game.player import calc_atk, calc_def, calc_xp_for_level, get_tt_bonus
from game.areas import get_area
import config

router = Router()


@router.message(F.text == "/inventory")
async def cmd_inventory(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    inv = await get_inventory(message.from_user.id)
    eq = await get_equipment(message.from_user.id)
    tools = await get_tools(message.from_user.id)

    with open(config.DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
        mat_data = json.load(f)
    names = mat_data.get("names", {})

    lang = user.lang if user else "en"

    if lang == "ru":
        text = "🎒 <b>Инвентарь</b>\n\n"
        text += "📦 <b>Материалы:</b>\n"
        for mat, amt in inv.items():
            if amt > 0 and mat not in ("life_potion", "common_lootbox", "artifact_core",
                                        "basic_bait", "advanced_bait", "golden_bait"):
                name = names.get(mat, mat)
                text += f"  {name}: {amt}\n"

        special = []
        if inv.get("life_potion", 0) > 0:
            special.append(f"🧪 Зелье жизни: {inv['life_potion']}")
        if inv.get("common_lootbox", 0) > 0:
            special.append(f"📦 Лутбоксы: {inv['common_lootbox']}")
        if inv.get("artifact_core", 0) > 0:
            special.append(f"💎 Артефакт ядро: {inv['artifact_core']}")
        baits = sum(inv.get(b, 0) for b in ("basic_bait", "advanced_bait", "golden_bait"))
        if baits > 0:
            special.append(f"🍖 Приманки: {baits}")
        if special:
            text += "\n✨ <b>Предметы:</b>\n" + "\n".join(f"  {s}" for s in special) + "\n"

        weapon_name = config.TIER_NAMES.get(eq.get("weapon_tier", 1), "T1")
        armor_name = config.TIER_NAMES.get(eq.get("armor_tier", 1), "T1")
        text += f"\n⚔️ <b>Снаряжение:</b>\n"
        text += f"  Оружие: {weapon_name} (Тир {eq.get('weapon_tier', 1)})\n"
        text += f"  Броня: {armor_name} (Тир {eq.get('armor_tier', 1)})\n"

        text += f"\n🔧 <b>Инструменты:</b>\n"
        text += f"  🪓 Топор: {tools.get('axe', 1)} ур.\n"
        text += f"  ⛏️ Кирка: {tools.get('pickaxe', 1)} ур.\n"
        text += f"  🎣 Удочка: {tools.get('rod', 1)} ур.\n"
    else:
        text = "🎒 <b>Inventory</b>\n\n"
        text += "📦 <b>Materials:</b>\n"
        for mat, amt in inv.items():
            if amt > 0 and mat not in ("life_potion", "common_lootbox", "artifact_core",
                                        "basic_bait", "advanced_bait", "golden_bait"):
                name = names.get(mat, mat)
                text += f"  {name}: {amt}\n"

        special = []
        if inv.get("life_potion", 0) > 0:
            special.append(f"🧪 Life potion: {inv['life_potion']}")
        if inv.get("common_lootbox", 0) > 0:
            special.append(f"📦 Lootboxes: {inv['common_lootbox']}")
        if inv.get("artifact_core", 0) > 0:
            special.append(f"💎 Artifact core: {inv['artifact_core']}")
        baits = sum(inv.get(b, 0) for b in ("basic_bait", "advanced_bait", "golden_bait"))
        if baits > 0:
            special.append(f"🍖 Baits: {baits}")
        if special:
            text += "\n✨ <b>Items:</b>\n" + "\n".join(f"  {s}" for s in special) + "\n"

        weapon_name = config.TIER_NAMES.get(eq.get("weapon_tier", 1), "T1")
        armor_name = config.TIER_NAMES.get(eq.get("armor_tier", 1), "T1")
        text += f"\n⚔️ <b>Equipment:</b>\n"
        text += f"  Weapon: {weapon_name} (Tier {eq.get('weapon_tier', 1)})\n"
        text += f"  Armor: {armor_name} (Tier {eq.get('armor_tier', 1)})\n"

        text += f"\n🔧 <b>Tools:</b>\n"
        text += f"  🪓 Axe: {tools.get('axe', 1)} lvl\n"
        text += f"  ⛏️ Pickaxe: {tools.get('pickaxe', 1)} lvl\n"
        text += f"  🎣 Rod: {tools.get('rod', 1)} lvl\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/top")
@router.message(F.text.startswith("/top "))
async def cmd_top(message: Message):
    args = message.text.split()[1:]

    if not args:
        leaderboard_type = "level"
        page = 1
    else:
        # Check if first arg is a number (page)
        if args[0].isdigit():
            leaderboard_type = "level"
            page = int(args[0])
        elif len(args) >= 2 and args[1].isdigit():
            leaderboard_type = args[0].lower()
            page = int(args[1])
        else:
            leaderboard_type = args[0].lower()
            page = 1

    from game.leaderboard import resolve_type, get_leaderboard, format_leaderboard, LEADERBOARD_TYPES

    resolved = resolve_type(leaderboard_type)
    if not resolved:
        types_list = ", ".join(LEADERBOARD_TYPES.keys())
        await message.answer(
            f"❌ Неизвестный тип: {leaderboard_type}\n\n"
            f"Доступные: {types_list}\n"
            f"Формат: /top [тип] (страница)",
            parse_mode="HTML"
        )
        return

    result = await get_leaderboard(resolved, page)
    result["type_key"] = resolved
    text = format_leaderboard(result)
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/title")
async def cmd_title(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    # Check which titles user qualifies for
    qualified = []
    for tid, tdata in config.TITLES.items():
        req = tdata["req"]
        val = tdata["value"]
        if req == "coolness" and user.coolness >= val:
            qualified.append(tdata["name"])
        elif req == "level" and user.level >= val:
            qualified.append(tdata["name"])
        elif req == "area" and user.area >= val:
            qualified.append(tdata["name"])
        elif req == "tt" and user.tt_count >= val:
            qualified.append(tdata["name"])

    current = user.title or "Без титула"
    text = f"🏷️ <b>Титул</b>\n\nТекущий: {current}\n\n"
    if qualified:
        text += "Доступные:\n" + "\n".join(f"  ⭐ {t}" for t in qualified)
        text += "\n\nНазначить: /title set [название]"
    else:
        text += "Пока нет доступных титулов. Продолжайте играть!"

    args = message.text.split()[1:]
    if args and args[0] == "set" and len(args) > 1:
        new_title = " ".join(args[1:])
        if new_title in qualified:
            async with async_session() as s:
                u = await s.get(User, message.from_user.id)
                u.title = new_title
                await s.commit()
            await message.answer(f"🏷️ Титул изменён на: <b>{new_title}</b>", parse_mode="HTML")
            return

    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/quest"))
async def cmd_quest(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    args = message.text.split()[1:] if message.text else []
    action = args[0].lower() if args else ""

    from game.quest import generate_quest, get_quest_status, claim_quest, quit_quest

    if action == "start":
        result = await generate_quest(message.from_user.id)
    elif action == "claim":
        result = await claim_quest(message.from_user.id)
    elif action == "quit":
        result = await quit_quest(message.from_user.id)
    else:
        result = await get_quest_status(message.from_user.id)

    await message.answer(result["message"], parse_mode="HTML")


@router.message(F.text.startswith("/epic quest"))
@router.message(F.text.startswith("/epic_quest"))
async def cmd_epic_quest(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    args = message.text.split()[1:] if message.text else []
    from game.quest import epic_quest_start, epic_quest_fight, get_quest_status

    if not args:
        # Show epic quest info
        from database.engine import async_session as _sess
        from database.models import Horse
        async with _sess() as s:
            horse = await s.get(Horse, message.from_user.id)
            horse_type = horse.horse_type if horse else "none"

        if horse_type not in ("special", "super_special"):
            await message.answer(
                "⚔️ <b>Эпический квест</b>\n\n"
                "Требуется лошадь типа Special или Super Special!\n\n"
                "Special: до 15 волн\n"
                "Super Special: до 100 волн\n\n"
                "Получить Special: /breed (шанс при спаривании)",
                parse_mode="HTML"
            )
            return

        max_waves = 15 if horse_type == "special" else 100
        await message.answer(
            f"⚔️ <b>Эпический квест</b>\n\n"
            f"Ваш тип лошади: {horse_type}\n"
            f"Макс. волн: {max_waves}\n\n"
            f"Введите количество волн: /epic quest [число]\n"
            f"Пример: /epic quest 10",
            parse_mode="HTML"
        )
        return

    # Parse wave count
    try:
        waves = int(args[0])
    except ValueError:
        await message.answer("❌ Укажите число волн: /epic quest 10")
        return

    # Start and fight
    start_result = await epic_quest_start(message.from_user.id, waves)
    if not start_result["success"]:
        await message.answer(start_result["message"])
        return

    fight_result = await epic_quest_fight(message.from_user.id, waves)
    await message.answer(fight_result["message"], parse_mode="HTML")


@router.message(F.text == "/boosts")
async def cmd_boosts(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    tt_bonus = get_tt_bonus(user.tt_count)

    text = (
        f"⬆️ <b>Бусты</b>\n\n"
        f"⏳ Time Travel: x{1 + tt_bonus:.2f} ({user.tt_count} TT)\n"
    )

    # Pet bonuses
    from game.player import get_pet_bonuses
    pets = await get_user_pets(message.from_user.id)
    if pets:
        text += f"🐾 Питомцы: +{len(pets)} бонус(ов)\n"

    # Horse bonus
    async with async_session() as s:
        horse = await s.get(Horse, message.from_user.id)
        if horse:
            text += f"🐴 Лошадь ({horse.name}): +{horse.speed} скорость\n"

    # Title
    if user.title:
        text += f"🏷️ Титул: {user.title}\n"

    # Cook boosts
    cook_parts = []
    if user.cook_hp_boost > 0:
        cook_parts.append(f"+{user.cook_hp_boost} HP")
    if user.cook_atk_boost > 0:
        cook_parts.append(f"+{user.cook_atk_boost} ATK")
    if user.cook_def_boost > 0:
        cook_parts.append(f"+{user.cook_def_boost} DEF")
    if user.cook_level_boost > 0:
        cook_parts.append(f"+{user.cook_level_boost} levels")
    if user.cook_coins_mult > 0:
        cook_parts.append(f"+{user.cook_coins_mult}% coins")
    if user.cook_fish_mult > 0:
        cook_parts.append(f"+{user.cook_fish_mult}% fish")
    if user.cook_logs_mult > 0:
        cook_parts.append(f"+{user.cook_logs_mult}% logs")
    if user.cook_flat_coins > 0:
        cook_parts.append(f"+{user.cook_flat_coins} coins/cmd")
    if cook_parts:
        text += f"🍳 Кулинария: {', '.join(cook_parts)}\n"

    # Artifacts
    inv = await get_inventory(message.from_user.id)
    artifacts = json.loads((await _get_artifacts(message.from_user.id)))
    if artifacts:
        text += f"🏺 Артефакты: {len(artifacts)}\n"

    if text.count("\n") <= 3:
        text += "\nПока нет активных бустов. Сначала: /timetravel, /pets, /horse"

    await message.answer(text, parse_mode="HTML")


async def get_user_pets(user_id):
    from sqlalchemy import select
    from database.models import Pet
    async with async_session() as s:
        result = await s.execute(select(Pet).where(Pet.user_id == user_id))
        return result.scalars().all()


async def _get_artifacts(user_id):
    inv = await get_inventory(user_id)
    return inv.get("artifacts", "[]")


@router.message(F.text == "/artifacts")
async def cmd_artifacts(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    inv = await get_inventory(message.from_user.id)
    artifacts = json.loads(inv.get("artifacts", "[]"))

    if not artifacts:
        await message.answer(
            "🏺 <b>Артефакты</b>\n\n"
            "У вас нет артефактов.\n\n"
            "Получить: /forge (Area 11+)",
            parse_mode="HTML"
        )
        return

    text = "🏺 <b>Артефакты</b>\n\n"
    for i, art in enumerate(artifacts):
        text += f"  {i+1}. {art}\n"
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/achievements")
async def cmd_achievements(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    # Simple achievement check based on current state
    earned = []
    if user.level >= 1:
        earned.append("first_hunt")
    if user.level >= 50:
        earned.append("level_50")
    if user.level >= 100:
        earned.append("level_100")
    if user.area >= 5:
        earned.append("area_5")
    if user.area >= 10:
        earned.append("area_10")
    if user.area >= 15:
        earned.append("area_15")
    if user.tt_count >= 1:
        earned.append("tt_1")
    if user.tt_count >= 5:
        earned.append("tt_5")
    if user.coins >= 100000:
        earned.append("coins_100k")
    if user.coins >= 1000000:
        earned.append("coins_1m")
    if user.coolness >= 10:
        earned.append("coolness_10")
    if user.coolness >= 50:
        earned.append("coolness_50")

    text = "🏆 <b>Достижения</b>\n\n"
    for aid, adata in config.ACHIEVEMENTS.items():
        check = "✅" if aid in earned else "❌"
        text += f"{check} {adata['emoji']} <b>{adata['name']}</b> — {adata['desc']}\n"

    text += f"\nПолучено: {len(earned)}/{len(config.ACHIEVEMENTS)}"
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/cards")
async def cmd_cards(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    # Simple card system - collect cards by doing actions
    text = (
        "🃏 <b>Карточки</b>\n\n"
        "Собирайте карточек, выполняя действия!\n\n"
        "Доступные карточки:\n"
        "  ⚔️ Карточка Охотника — /hunt 100 раз\n"
        "  🪓 Карточка Лесоруба — /chop 100 раз\n"
        "  ⛏️ Карточка Шахтёра — /mine 100 раз\n"
        "  🎣 Карточка Рыбака — /fish 100 раз\n"
        "  🏰 Карточка Подземелий — /dungeon 50 раз\n"
        "  💎 Карточка Времени — /timetravel 10 раз\n\n"
        "Прогресс: /cards progress"
    )
    await message.answer(text, parse_mode="HTML")
