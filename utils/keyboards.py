from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def hunt_keyboard(is_on_cooldown: bool = False, remaining: int = 0) -> InlineKeyboardMarkup:
    if is_on_cooldown:
        btn = InlineKeyboardButton(text=f"⏳ Охота ({remaining}с)", callback_data="action_hunt_cd")
    else:
        btn = InlineKeyboardButton(text="⚔️ Охота", callback_data="action_hunt")
    return InlineKeyboardMarkup(inline_keyboard=[[btn]])


def adventure_keyboard(is_on_cooldown: bool = False, remaining: int = 0) -> InlineKeyboardMarkup:
    if is_on_cooldown:
        btn = InlineKeyboardButton(text=f"⏳ Приключение ({remaining}с)", callback_data="action_adventure_cd")
    else:
        btn = InlineKeyboardButton(text="🗡️ Приключение", callback_data="action_adventure")
    return InlineKeyboardMarkup(inline_keyboard=[[btn]])


def work_keyboard(action: str, is_on_cooldown: bool = False, remaining: int = 0) -> InlineKeyboardMarkup:
    emojis = {"chop": "🪓", "mine": "⛏️", "fish": "🎣"}
    names = {"chop": "Рубить", "mine": "Копать", "fish": "Рыбачить"}
    emoji = emojis.get(action, "🔧")
    name = names.get(action, action)
    if is_on_cooldown:
        btn = InlineKeyboardButton(text=f"⏳ {name} ({remaining}с)", callback_data=f"action_{action}_cd")
    else:
        btn = InlineKeyboardButton(text=f"{emoji} {name}", callback_data=f"action_{action}")
    return InlineKeyboardMarkup(inline_keyboard=[[btn]])


def main_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    if lang == "ru":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Гайд", callback_data="open_guide")],
            [InlineKeyboardButton(text="⚔️ Охота", callback_data="action_hunt"),
             InlineKeyboardButton(text="🗡️ Приключение", callback_data="action_adventure")],
            [InlineKeyboardButton(text="🪓 Рубить", callback_data="action_chop"),
             InlineKeyboardButton(text="⛏️ Копать", callback_data="action_mine"),
             InlineKeyboardButton(text="🎣 Рыбачить", callback_data="action_fish")],
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Guide", callback_data="open_guide")],
        [InlineKeyboardButton(text="⚔️ Hunt", callback_data="action_hunt"),
         InlineKeyboardButton(text="🗡️ Adventure", callback_data="action_adventure")],
        [InlineKeyboardButton(text="🪓 Chop", callback_data="action_chop"),
         InlineKeyboardButton(text="⛏️ Mine", callback_data="action_mine"),
         InlineKeyboardButton(text="🎣 Fish", callback_data="action_fish")],
    ])


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
         InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
    ])


def cooldowns_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="cooldowns:refresh")]
    ])


def recipes_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⏪", callback_data=f"recipes:first:0"))
        buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"recipes:prev:{page}"))
    buttons.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="recipes:info"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"recipes:next:{page}"))
        buttons.append(InlineKeyboardButton(text="⏩", callback_data=f"recipes:last:{total_pages - 1}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def event_keyboard(event_type: str) -> InlineKeyboardMarkup:
    from game.events import EVENT_TYPES
    info = EVENT_TYPES.get(event_type, {})
    emoji = info.get("emoji", "🔧")
    button = info.get("button", "🔧 УЧАСТВОВАТЬ!")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=button, callback_data=f"event:{event_type}")]
    ])


def craft_keyboard(tier: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⚒️ Скрафтить Тир {tier}", callback_data=f"craft:{tier}")]
    ])


def area_keyboard(current_area: int) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i in range(1, 16):
        emoji = "📍" if i == current_area else f"{i}"
        row.append(InlineKeyboardButton(text=emoji, callback_data=f"area:{i}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def gambling_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Кости", callback_data="gamble:dice"),
         InlineKeyboardButton(text="🥤 Чашки", callback_data="gamble:cups")],
        [InlineKeyboardButton(text="🪙 Монетка", callback_data="gamble:cf"),
         InlineKeyboardButton(text="🎰 Слоты", callback_data="gamble:slots")],
        [InlineKeyboardButton(text="🃏 Блэкджек", callback_data="gamble:bj"),
         InlineKeyboardButton(text="🎟️ Лотерея", callback_data="gamble:lottery")],
    ])
