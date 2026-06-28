"""
Tutorial command — step-by-step game guide with inline keyboard navigation.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.crud import get_user

router = Router()

PAGES = {
    "start": {
        "title": "Добро пожаловать в EPIC RPG!",
        "text": (
            "🎮 <b>EPIC RPG — Пошаговый гайд</b>\n\n"
            "Это текстовая RPG-игра с 15 зонами, подземельями, "
            "крафтом, питомцами, лошадьми и множеством систем.\n\n"
            "▶️ Нажмите «Далее» чтобы начать.\n"
            "⏩ Используйте номера страниц для быстрого перехода."
        ),
    },
    "basics": {
        "title": "Основы",
        "text": (
            "🎯 <b>Основы</b>\n\n"
            "Цель игры — проходить зоны, становиться сильнее и открывать новые команды.\n\n"
            "📋 <b>Команды:</b>\n"
            "  /start — регистрация\n"
            "  /profile — статы, HP, уровень\n"
            "  /help — список всех команд\n"
            "  /inventory — инвентарь\n"
            "  /cooldowns — кулдауны\n"
            "  /lang — смена языка (EN/RU)\n\n"
            "💡 Можно писать команды с / или без (rpg hunt, рпг охота).\n"
            "💡 Пробелы работают: /hunt alone = /hunt_alone"
        ),
    },
    "combat": {
        "title": "Бой",
        "text": (
            "⚔️ <b>Бой</b>\n\n"
            "🟢 /hunt — основной источник XP и монет. Кулдаун 1 минута.\n"
            "📖 /adventure — приключение. Больше XP, кулдаун 1 час.\n\n"
            "⚠️ <b>Внимание: HP!</b>\n"
            "Если HP падает до 0 — вы теряете 1 уровень!\n"
            "Используйте /heal чтобы восстановить HP.\n\n"
            "🧪 /heal — восстановить всё HP (тратит life potion).\n"
            "❤️ /bg — фон профиля.\n\n"
            "Формула урона: ATK оружия - DEF брони врага.\n"
            "Лошадь тира IV спасает от смерти (не теряете уровень)."
        ),
    },
    "working": {
        "title": "Работа",
        "text": (
            "🪵 <b>Работа — добыча ресурсов</b>\n\n"
            "🪓 /chop — рубка дерева. Кулдаун 5 мин.\n"
            "🎣 /fish — рыбалка. Кулдаун 5 мин.\n"
            "⛏️ /mine — добыча руды. Кулдаун 5 мин.\n"
            "🫧 /pickup — сбор предметов. Кулдаун 5 мин.\n\n"
            "Ресурсы нужны для:\n"
            "  • Крафта снаряжения\n"
            "  • Обмена с NPC (/npc)\n"
            "  • Обмена между игроками (/trade)\n\n"
            "Улучшайте инструменты: /upgrade axe/pickaxe/rod\n"
            "Чем выше уровень инструмента — тем ценнее дроп.\n\n"
            "Также есть /work и /proclaim для additional.worker XP."
        ),
    },
    "crafting": {
        "title": "Крафт и снаряжение",
        "text": (
            "⚒️ <b>Крафт</b>\n\n"
            "🔨 /craft — крафт снаряжения из ресурсов.\n"
            "  Крафтит по 5 штук за раз.\n"
            "  Тир 1→15: Wooden → Fish → Iron → Ruby → Dragon → Dark → Frost → Necro → Obsidian → Chrono → Ultimate → Perfect → Divine → Celestial → Void\n\n"
            "🔧 /forge (Area 7+) — улучшение оружия/брони\n"
            "🌀 /voidforge (Area 11+) — Void-крафт\n"
            "🗑️ /dismantle — разборка предметов\n\n"
            "📊 Тиры снаряжения:\n"
            "  Оружие: +ATK (от 10 до 11000)\n"
            "  Броня: +DEF (от 8 до 10000)\n\n"
            "Инструменты: /upgrade axe/pickaxe/rod (уровень 1-20+)"
        ),
    },
    "dungeons": {
        "title": "Подземелья",
        "text": (
            "🏰 <b>Подземелья</b>\n\n"
            "Подземелья — ключ к прогрессии зон!\n\n"
            "Купить ключ: /shop\n"
            "Войти: /dungeon [номер] (1-9)\n\n"
            "В подземелье идут 1-4 игрока.\n"
            "Убейте босса → откроется следующая зона!\n\n"
            "📋 Зоны и подземелья:\n"
            "  Area 1 → D1 Ancient Dragon\n"
            "  Area 2 → D2 Too Ancient Dragon\n"
            "  ...\n"
            "  Area 9 → D9 OwO Dragon\n\n"
            "⏰ Лимит времени: 2.5 мин на игрока.\n"
            "💰 Награда: монеты после победы.\n\n"
            "Ключи стоят дороже с каждым D:\n"
            "D1: 5,000 → D9: 2,500,000"
        ),
    },
    "economy": {
        "title": "Экономика",
        "text": (
            "💰 <b>Экономика</b>\n\n"
            "Ежедневные награды:\n"
            "  /daily — монеты + зелья жизни (23ч 50мин)\n"
            "  /weekly — монеты + лутбокс + печенья + фляги (7 дней)\n"
            "  /vote — голосуй за бота! Монеты + лутбокс (12ч)\n\n"
            "📊 Стрик голосования (0-7):\n"
            "  0: Rare Lootbox\n"
            "  1: Epic Lootbox\n"
            "  2-7: Edgy Lootbox\n"
            "  7: +25 Арена печенье + Фляга + EPIC монета\n\n"
            "🏦 /bank — банк (вкладывайте монеты)\n"
            "💳 /donate — обмен монет на EPIC монеты (100:1)\n"
            "🎁 /code [промокод] — ввести промокод\n"
            "💸 /give @user [сумма] — передать монеты (разница TT ≤2)"
        ),
    },
    "shop": {
        "title": "Магазин",
        "text": (
            "🛒 <b>Магазин</b>\n\n"
            "/shop — купить лутбоксы и предметы за монеты:\n"
            "  Common: 800\n"
            "  Uncommon: 6,000\n"
            "  Rare: 40,000\n"
            "  Epic: 150,000\n"
            "  Edgy: 420,666\n\n"
            "/open — открыть лутбокс\n"
            "/use [предмет] — использовать предмет\n\n"
            "💎 /epic shop — EPIC магазин (за EPIC монеты):\n"
            "  1000 монет — 50 EPIC\n"
            "  Улучшение оружия — 200 EPIC\n"
            "  Улучшение брони — 200 EPIC\n"
            "  Случайный питомец — 500 EPIC"
        ),
    },
    "horse": {
        "title": "Лошади",
        "text": (
            "🐴 <b>Лошади</b>\n\n"
            "/horse — информация о лошади\n"
            "/buy horse [тип] — купить лошадь:\n"
            "  Normal: бесплатно\n"
            "  Fast: 5,000\n"
            "  Strong: 5,000\n"
            "  Epic: 10,000\n\n"
            "🏋️ /train horse — тренировка (SPD/STR/END)\n"
            "  Кулдаун: 5 мин. Стоимость: уровень × 100\n\n"
            "🥚 /breed — спаривание (шанс на Special/Super Special!)\n"
            "🏇 /race — гонка (награда: horse_coins)\n\n"
            "Типы лошадей влияют на:\n"
            "  • Множитель монет в daily/weekly\n"
            "  • Шанс спасения от смерти (Tier IV)\n"
            "  • Epic Quest (Special/Super Special)"
        ),
    },
    "pets": {
        "title": "Питомцы",
        "text": (
            "🐾 <b>Питомцы (Area 12+)</b>\n\n"
            "/pets — список питомцев\n"
            "/pet [имя] — информация о питомце\n\n"
            "Тиры: D → C → B → A → S\n\n"
            "Питомцы дают бонусы:\n"
            "  • ATK/DEF/HP/XP\n"
            "  • Множители монет/дропа\n\n"
            "Питомцы получают XP вместе с вами.\n"
            "Повышение тира: /pet evolve\n"
            "Тренировка: /train pet\n\n"
            "Случайный питомец: /pet spawn\n"
            "Также можно получить в Training (шанс 4-20%)."
        ),
    },
    "timetravel": {
        "title": "Time Travel",
        "text": (
            "⏳ <b>Time Travel</b> (Area 11+)\n\n"
            "/timetravel — сброс прогресса за bonuses!\n\n"
            "Что сохраняется:\n"
            "  • Лошадь, питомцы, титулы\n"
            "  • EPIC монеты, достижения\n"
            "  • Бонусы (XP/монеты/дроп с TT)\n\n"
            "Что сбрасывается:\n"
            "  • Уровень, зона, монеты\n"
            "  • Снаряжение, инвентарь\n\n"
            "Формула бонусов (wiki-accurate):\n"
            "  XP: (99+x)×x/2\n"
            "  Монеты: (99+x)×x/2\n"
            "  Дроп: (49+x)×x/2\n\n"
            "Титулы за TT: 1→Time Traveler, 2→One time..., 5→..., 10→OOF\n"
            "Макс. TT: 25 regular → Super Time Travel\n"
            "STT: /super_timetravel"
        ),
    },
    "professions": {
        "title": "Профессии",
        "text": (
            "👷 <b>Профессии</b>\n\n"
            "5 профессий, каждая с уникальными бонусами:\n\n"
            "🪓 Worker — бонус к ресурсам (chop/fish/mine)\n"
            "⚒️ Crafter — бонус к крафту\n"
            "📦 Lootboxer — бонус к лутбоксам\n"
            "🏪 Merchant — бонус к монетам\n"
            "✨ Enchanter — бонус к зачарованию\n\n"
            "/profession — статус текущей профессии\n"
            "/profession select [тип] — выбрать профессию\n"
            "/profession rewards — получить награды за уровень\n\n"
            "XP копится автоматически при выполнении\n"
            "соответствующих команд."
        ),
    },
    "gambling": {
        "title": "Азартные игры",
        "text": (
            "🎰 <b>Азартные игры</b>\n\n"
            "Флип: /flip [сумма] — подбросить монету (45/54/1%)\n"
            "Кубик: /dice [сумма] — бросить кубик\n"
            "Стаканы: /cups [сумма] — угадай стакан (1.75x)\n"
            "Слоты: /slots [сумма] — 5 барабанов\n"
            "Блэкджек: /blackjack [сумма] — 7 card charlie\n"
            "Колесо: /wheel [сумма] — Area 8+\n"
            "Большие кубики: /big_dice [сумма] — Area 14+\n\n"
            "Мин. ставка: 10 | Макс: 100,000\n\n"
            "🎰 /lottery — купить лотерейный билет\n"
            "🃏 /cards — система карточек"
        ),
    },
    "quests": {
        "title": "Квесты",
        "text": (
            "📜 <b>Квесты</b>\n\n"
            "/quest — текущий квест\n"
            "/quest start — начать квест\n"
            "/quest claim — забрать награду\n"
            "/quest quit — бросить квест\n\n"
            "Типы квестов (9 штук):\n"
            "  Охота, Приключение, Крафт, Азарт,\n"
            "  Арена, Минибосс, Кулинария, Гильдия, Торговля\n\n"
            "Кулдаун: 6 часов после завершения.\n\n"
            "⚔️ /epic_quest — Эпический квест\n"
            "  Требуется Special/Super Special лошадь!\n"
            "  Special: до 15 волн\n"
            "  Super Special: до 100 волн"
        ),
    },
    "training": {
        "title": "Тренировка и Ультренировка",
        "text": (
            "🏋️ <b>Training</b> (Area 2+, TT2+)\n\n"
            "/training — мини-игра с головоломкой!\n"
            "6 типов: Forest, River, Field, Casino, Void, Mine\n\n"
            "Каждый тип — своя загадка:\n"
            "  🌲 Forest: найти сундук (кнопки)\n"
            "  🌊 River: переправа (угадай сторону)\n"
            "  🌾 Field: числовая загадка\n"
            "  🎰 Casino: угадай число\n"
            "  🌀 Void: Area-зависимая загадка\n"
            "  ⛏️ Mine: ruby-загадка\n\n"
            "XP: ~100 + 400×Area | Кулдаун: 15 мин\n"
            "Шанс питомца: 4% (10%/20% с хорошей лошадью)\n\n"
            "⚔️ /ultraining (Area 12+) — EPIC NPC бой!\n"
            "  ATTACK / BLOCK / ATTLOCK\n"
            "  25% шанс на double stage!\n"
            "  Награда: coolness (2 или 4)"
        ),
    },
    "guild": {
        "title": "Гильдии",
        "text": (
            "🏰 <b>Гильдии</b>\n\n"
            "/guild create [название] — создать гильдию\n"
            "/guild join [название] — вступить\n"
            "/guild leave — покинуть\n"
            "/guild info — информация\n"
            "/guild members — участники\n\n"
            "Гильдии дают:\n"
            "  • Общий XP топ\n"
            "  • Гильдейские квесты\n"
            "  • Общение с игроками\n\n"
            "Топ гильдий: /top guilds"
        ),
    },
    "misc": {
        "title": "Разное",
        "text": (
            "📊 <b>Дополнительно</b>\n\n"
            "📈 /top — рейтинг (18 типов!)\n"
            "  level, coins, timetravel, pets, coolness...\n"
            "  Формат: /top [тип] [страница]\n\n"
            "🔄 /trade — обмен ресурсами (A-F)\n"
            "  Ресурсы: дерево, рыба, яблоко, рубин\n"
            "  Ставки зависят от зоны!\n\n"
            "🏷️ /title — титулы\n"
            "  Получаются за уровень/зону/TT/coolness\n\n"
            "🏆 /achievements — достижения\n"
            "🍳 /cook — кулинария (Area 5+): баффы статов\n"
            "🏺 /farm — ферма: посадка семян\n"
            "💚 /greenhouse — теплица\n"
            "🎰 /lottery — лотерея\n"
            "💍 /marry — брак\n"
            "🌍 /world — мир\n"
            "🎰 /casino — казино\n\n"
            "Нужна помощь? /help [название команды]"
        ),
    },
    "tips": {
        "title": "Советы",
        "text": (
            "💡 <b>Советы для новичков</b>\n\n"
            "1️⃣ Начните с /hunt — это основной источник XP и монет.\n\n"
            "2️⃣ Не забывайте /heal — смерть = потеря уровня!\n\n"
            "3️⃣ Собирайте ресурсы (/chop, /fish) и крафтите\n"
            "лучшее снаряжение перед подземельем.\n\n"
            "4️⃣ /daily, /weekly, /vote — бесплатные монеты.\n\n"
            "5️⃣ Не тратьте всё на лутбоксы — крафтите!\n\n"
            "6️⃣ Лошадь спасает от смерти (Tier IV).\n\n"
            "7️⃣ TT даёт мощные бонусы, но сбрасывает прогресс.\n\n"
            "8️⃣ Прокачивайте инструменты — больше ресурсов.\n\n"
            "9️⃣ Кулинария даёт постоянные баффы.\n\n"
            "🔟 Изучите /trade — выгодные обмены по зонам."
        ),
    },
}

# Page order for next/prev navigation
PAGE_ORDER = list(PAGES.keys())


def _get_nav_keyboard(current_key: str) -> InlineKeyboardMarkup:
    """Build navigation keyboard for tutorial page."""
    idx = PAGE_ORDER.index(current_key)
    buttons = []

    # Top row: prev/next
    row = []
    if idx > 0:
        row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"tut:{PAGE_ORDER[idx - 1]}"))
    if idx < len(PAGE_ORDER) - 1:
        row.append(InlineKeyboardButton(text="Далее ➡️", callback_data=f"tut:{PAGE_ORDER[idx + 1]}"))
    if row:
        buttons.append(row)

    # Middle row: page counter
    buttons.append([
        InlineKeyboardButton(text=f"📄 {idx + 1}/{len(PAGE_ORDER)}", callback_data="noop")
    ])

    # Bottom row: quick jumps (every 3rd page)
    jump_row = []
    jump_targets = [0, 3, 6, 9, 12, 15]  # start, basics, crafting, economy, pets, training, tips
    for ti in jump_targets:
        if ti < len(PAGE_ORDER) and PAGE_ORDER[ti] != current_key:
            label = PAGES[PAGE_ORDER[ti]]["title"][:12]
            jump_row.append(InlineKeyboardButton(text=label, callback_data=f"tut:{PAGE_ORDER[ti]}"))
    if jump_row:
        buttons.append(jump_row)

    # Close button
    buttons.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="tut_close")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "/tutorial")
async def cmd_tutorial(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    page = PAGES["start"]
    kb = _get_nav_keyboard("start")
    text = f"<b>{page['title']}</b>\n\n{page['text']}"
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("tut:"))
async def cb_tutorial_nav(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    if key not in PAGES:
        await callback.answer()
        return

    page = PAGES[key]
    kb = _get_nav_keyboard(key)
    text = f"<b>{page['title']}</b>\n\n{page['text']}"

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        pass  # message not modified
    await callback.answer()


@router.callback_query(F.data == "tut_close")
async def cb_tutorial_close(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer()
