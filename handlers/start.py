"""
Start and language selection commands.
New users: language pick → tutorial → welcome.
Returning users: welcome with profile summary.
Admin: /start new — wipe account.
"""
import json
from datetime import datetime as _dt
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.crud import get_or_create_user
from database.engine import async_session
from database.models import User, Inventory, Cooldown, Horse, Pet, Profession
from config import DEFAULT_MATERIALS

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username or "")
    created = user.level == 1 and user.tt_count == 0 and user.area == 1 and not user.lang

    if created or not user.lang or user.lang not in ("en", "ru"):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        ])
        await message.answer(
            "👋 <b>Welcome to EPIC RPG!</b>\n\n"
            "Choose your language / Выберите язык:",
            parse_mode="HTML", reply_markup=kb,
        )
        return

    lang = user.lang
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="/help", callback_data="cmd:/help")],
    ])
    if lang == "ru":
        text = (
            f"👋 С возвращением, <b>{user.username or 'Игрок'}</b>!\n\n"
            f"📊 Уровень: {user.level} | Зона: {user.area}\n"
            f"💰 Монеты: {user.coins:,}\n\n"
            f"Начать: /hunt | Статы: /profile\n"
            f"Туториал: /tutorial"
        )
    else:
        text = (
            f"👋 Welcome back, <b>{user.username or 'Player'}</b>!\n\n"
            f"📊 Level: {user.level} | Area: {user.area}\n"
            f"💰 Coins: {user.coins:,}\n\n"
            f"Start: /hunt | Profile: /profile\n"
            f"Tutorial: /tutorial"
        )
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.message(F.text == "/start new")
async def cmd_start_new(message: Message):
    """Admin-only: wipe account back to fresh state."""
    if (message.from_user.username or "").lower() not in ("besp0ke", "dmitriy_1339"):
        await message.answer("❌ Эта команда недоступна.")
        return

    uid = message.from_user.id
    async with async_session() as s:
        # --- Wipe user ---
        u = await s.get(User, uid)
        if u:
            u.level = 1; u.xp = 0; u.coins = 100; u.epic_coins = 0
            u.area = 1; u.max_area = 1; u.tt_count = 0; u.current_hp = 0
            u.title = ""; u.lang = ""; u.coolness = 0; u.bank = 0
            u.ascended = False; u.life_boost_active = False
            u.quest_completed = False; u.epic_quest_wave = 0
            for c in ("cook_hp_boost", "cook_atk_boost", "cook_def_boost", "cook_level_boost",
                       "cook_coins_mult", "cook_fish_mult", "cook_logs_mult", "cook_flat_coins"):
                setattr(u, c, 0)

        # --- Wipe inventory ---
        inv = await s.get(Inventory, uid)
        if inv:
            inv.materials = json.dumps(dict(DEFAULT_MATERIALS))
            inv.equipment = json.dumps({"weapon_tier": 1, "armor_tier": 1})
            inv.tools = json.dumps({"axe": 1, "pickaxe": 1, "rod": 1})

        # --- Wipe cooldowns ---
        cd = await s.get(Cooldown, uid)
        if cd:
            for col in Cooldown.__table__.columns.keys():
                if col == "user_id":
                    continue
                if "streak" in col:
                    setattr(cd, col, 0)
                else:
                    setattr(cd, col, _dt.min)

        # --- Wipe horse ---
        h = await s.get(Horse, uid)
        if h:
            h.name = "Starter Horse"; h.horse_type = "normal"; h.tier = 1
            h.level = 1; h.xp = 0; h.epicness = 0; h.fail_count = 0; h.coins = 0

        # --- Delete all pets ---
        from sqlalchemy import select as _sel
        pets = (await s.execute(_sel(Pet).where(Pet.user_id == uid))).scalars().all()
        for p in pets:
            await s.delete(p)

        # --- Wipe professions ---
        prof = await s.get(Profession, uid)
        if prof:
            for name in ("worker", "crafter", "lootboxer", "merchant", "enchanter"):
                setattr(prof, f"{name}_level", 1)
                setattr(prof, f"{name}_xp", 0)

        await s.commit()

    await message.answer("🔄 Аккаунт сброшен! Используй /start чтобы начать заново.")


@router.message(F.text == "/lang")
async def cmd_lang(message: Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username or "")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_switch:ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_switch:en")],
    ])
    current = "Русский" if user.lang == "ru" else "English"
    text = f"🌐 Текущий язык: {current}\nВыберите язык / Choose language:"
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("lang_switch:"))
async def cb_lang_switch(callback: CallbackQuery):
    lang = callback.data.split(":", 1)[1]
    if lang not in ("en", "ru"):
        await callback.answer()
        return

    await get_or_create_user(callback.from_user.id, callback.from_user.username or "")

    from sqlalchemy import update as _upd
    async with async_session() as s:
        await s.execute(_upd(User).where(User.user_id == callback.from_user.id).values(lang=lang))
        await s.commit()

    await callback.answer()
    if lang == "ru":
        text = "🇷🇺 Язык изменён на русский"
    else:
        text = "🇬🇧 Language set to English"
    await callback.message.edit_text(text)


@router.callback_query(F.data.startswith("lang:"))
async def cb_language_pick(callback: CallbackQuery):
    lang = callback.data.split(":", 1)[1]
    if lang not in ("en", "ru"):
        await callback.answer()
        return

    await get_or_create_user(callback.from_user.id, callback.from_user.username or "")

    from sqlalchemy import update as _upd
    async with async_session() as s:
        await s.execute(_upd(User).where(User.user_id == callback.from_user.id).values(lang=lang))
        await s.commit()

    await callback.answer()

    if lang == "ru":
        text = (
            "🇷🇺 <b>Язык установлен: Русский</b>\n\n"
            "Добро пожаловать в EPIC RPG!\n"
            "Это текстовая RPG-игра с 15 зонами, подземельями, "
            "крафтом, питомцами, лошадьми и множеством систем.\n\n"
            "Изучите игру с помощью пошагового гайда 👇"
        )
    else:
        text = (
            "🇬🇧 <b>Language set: English</b>\n\n"
            "Welcome to EPIC RPG!\n"
            "A text-based RPG with 15 areas, dungeons, "
            "crafting, pets, horses and many systems.\n\n"
            "Learn the game with the step-by-step guide 👇"
        )

    from handlers.tutorial import PAGES, _get_nav_keyboard
    page = PAGES["start"]
    kb = _get_nav_keyboard("start")
    tutorial_text = f"<b>{page['title']}</b>\n\n{page['text']}"

    try:
        await callback.message.edit_text(text, parse_mode="HTML")
    except Exception:
        pass

    await callback.message.answer(tutorial_text, parse_mode="HTML", reply_markup=kb)
