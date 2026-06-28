"""
Translations for EN/RU language system.
Keys match text used in formatters and handlers.
"""
T = {
    "en": {
        # /start
        "start_title": "EPIC RPG",
        "start_welcome": "Welcome to EPIC RPG, {name}!",
        "start_purpose": "The main purpose of the game is to reach higher areas to become stronger and unlock new commands\nThere's a total of 20 areas, and you start in area #1",
        "start_how": "HOW TO PLAY",
        "start_hunt": "Get XP and COINS with 🟢 hunt and 📖 adventure, check your progress with profile",
        "start_heal": "WARNING! You will lose a level if you die! Use 🧪 heal when your HP is low",
        "start_items": "ITEMS AND COINS",
        "start_chop": "Get items with 🪵 chop and 🐟 fish to craft equipment or trade with NPC!",
        "start_shop": "Use your 🪙 coins in the shop",
        "start_daily": "Get more coins and items with daily, weekly and vote",
        "start_dungeons": "DUNGEONS AND AREAS",
        "start_dungeon_text": "When you feel ready, buy a 🗝️ dungeon key and enter with dungeon! If you kill the 🐉 boss, you will unlock the next area!",
        "start_area_text": "Each area unlocks commands, items, recipes, mobs, boosts and a harder dungeon",
        "start_more": "MORE",
        "start_help_text": "Check all commands with help! There are a lot more things to do",
        "start_vote": "You can vote for the bot (command vote) to get rewards!",
        "start_rules": "Make sure to read rules",

        # Guide
        "guide_title": "📖 EPIC RPG Guide",
        "guide_purpose": "The main purpose of the game is to reach higher areas to become stronger and unlock new commands.\n\nThere are a total of 20 areas and the TOP in this game. Each area will have a new set of enemies, new dungeons, commands, items etc. The player will always start in Area 1.",
        "guide_how": "How do I play?",
        "guide_how_text": "Start by getting coins and XP doing the <code>hunt</code> and <code>adventure</code> commands, remember to <code>heal</code> often to not die and lose a level! You can always check your HP and progress with <code>profile</code>.\n\nStart crafting better gear to be stronger and be able to defeat your enemies with ease! Whenever you feel ready, buy a dungeon key and test your skills by going into a dungeon with a friend, or even up to 4 players! Defeating the dungeon will unlock the next area, and a harder dungeon.",
        "guide_items": "How do I get items though?",
        "guide_items_text": "Use the working commands available to you, which currently is either <code>fish</code> or <code>chop</code>. These items will be used to craft better gears for yourself, or you can trade them with <code>npc</code>.\n\nUse <code>shop</code> to see what items you can buy with your current amount of coins!",
        "guide_money": "I don't have any money. What do I do?",
        "guide_money_text": "You can always get more coins through <code>daily</code>, <code>weekly</code> and <code>vote</code> commands!",
        "start_lang_pick": "Choose your language:",

        # /help
        "help_title": "Commands",
        "help_info": "For more info: help [command/item/event]",
        "help_prefix": "Add / or rpg before any command",
        "help_example": "Examples: /hunt or rpg hunt",
        "help_progress": "Progress",
        "help_fighting": "Fighting",
        "help_economy": "Economy",
        "help_working": "Working",
        "help_gambling": "Gambling",
        "help_rewards": "More rewards",
        "help_unlocked": "Unlocked in higher areas",

        # Combat
        "combat_kill": "{name} found and killed a {emoji} {mob}",
        "combat_earned": "Earned {coins} coins and {xp} XP",
        "combat_lost_hp": "Lost {dmg} HP, remaining HP is {hp}/{max}",
        "combat_got_drop": "{name} got 1 {emoji} {item}",
        "combat_defeated": "{name} found a {emoji} {mob} but lost the fight",
        "combat_coins_lost": "Lost {coins} coins",
        "combat_levelup": "Level up! Now level {level}",

        # Cooldowns
        "cd_title": "Cooldowns",
        "cd_ready": "Ready",
        "cd_remaining": "{m}m {s}s",

        # Common
        "not_registered": "Register first: /start",
        "area_required": "Area {min} required.",
        "coins": "coins",

        # Language
        "lang_set": "Language set to English",
        "lang_cmd": "/lang — switch language",
    },
    "ru": {
        # /start
        "start_title": "EPIC RPG",
        "start_welcome": "Добро пожаловать в EPIC RPG, {name}!",
        "start_purpose": "Основная цель игры — добираться до более высоких зон, становиться сильнее и открывать новые команды\nВсего 20 зон, и вы начинаете в зоне #1",
        "start_how": "КАК ИГРАТЬ",
        "start_hunt": "Получайте ОПЫТ и МОНЕТЫ с 🟢 hunt и 📖 adventure, проверьте прогресс в profile",
        "start_heal": "ВНИМАНИЕ! Вы потеряете уровень при смерти! Используйте 🧪 heal когда HP низкие",
        "start_items": "ПРЕДМЕТЫ И МОНЕТЫ",
        "start_chop": "Получайте предметы с 🪵 chop и 🐟 fish для крафта снаряжения или торговли!",
        "start_shop": "Тратьте 🪙 монеты в shop",
        "start_daily": "Получайте больше монет и предметов с daily, weekly и vote",
        "start_dungeons": "ПОДЗЕМЕЛЬЯ И ЗОНЫ",
        "start_dungeon_text": "Когда будете готовы, купите 🗝️ dungeon key и войдите через dungeon! Если убьёте 🐉 босса, откроете следующую зону!",
        "start_area_text": "Каждая зона открывает команды, предметы, рецепты, мобов, бусты и более сложное подземелье",
        "start_more": "ЕЩЁ",
        "start_help_text": "Все команды в help! Тут ещё очень много всего",
        "start_vote": "Голосуйте за бота (команда vote) чтобы получить награды!",
        "start_rules": "Обязательно прочитайте rules",

        # Guide
        "guide_title": "📖 Гайд EPIC RPG",
        "guide_purpose": "Основная цель игры — добираться до более высоких зон, становиться сильнее и открывать новые команды.\n\nВсего 20 зон и рейтинг игроков. Каждая зона открывает новых врагов, подземелья, команды, предметы и т.д. Начинаете вы в зоне #1.",
        "guide_how": "Как играть?",
        "guide_how_text": "Начните зарабатывать монеты и опыт через команды <code>hunt</code> и <code>adventure</code>. Не забывайте часто использовать <code>heal</code>, чтобы не умереть и не потерять уровень! Проверяйте HP и прогресс через <code>profile</code>.\n\nКрафтите лучшее снаряжение чтобы стать сильнее! Когда будете готовы, купите ключ подземелья и протестируйте свои навыки в подземелье с другом или до 4 игроков! Победа в подземелье откроет следующую зону и более сложное подземелье.",
        "guide_items": "Как получить предметы?",
        "guide_items_text": "Используйте команды работы: <code>fish</code> или <code>chop</code>. Эти предметы используются для крафта снаряжения или для обмена с <code>npc</code>.\n\nИспользуйте <code>shop</code> чтобы посмотреть что можно купить на ваши монеты!",
        "guide_money": "У меня нет денег. Что делать?",
        "guide_money_text": "Монеты всегда можно получить через команды <code>daily</code>, <code>weekly</code> и <code>vote</code>!",
        "start_lang_pick": "Выберите язык:",

        # /help
        "help_title": "Команды",
        "help_info": "Подробнее: help [команда/предмет/событие]",
        "help_prefix": "Добавьте / или рпг перед любой командой",
        "help_example": "Примеры: /hunt или рпг hunt",
        "help_progress": "Прогресс",
        "help_fighting": "Бой",
        "help_economy": "Экономика",
        "help_working": "Работа",
        "help_gambling": "Азартные игры",
        "help_rewards": "Награды",
        "help_unlocked": "Открывается на высоких зонах",

        # Combat
        "combat_kill": "{name} нашёл и убил {emoji} {mob}",
        "combat_earned": "Заработал {coins} монет и {xp} XP",
        "combat_lost_hp": "Потеряно {dmg} HP, осталось {hp}/{max}",
        "combat_got_drop": "{name} получил 1 {emoji} {item}",
        "combat_defeated": "{name} нашёл {emoji} {mob}, но проиграл бой",
        "combat_coins_lost": "Потеряно {coins} монет",
        "combat_levelup": "Level up! Уровень {level}",

        # Cooldowns
        "cd_title": "Кулдауны",
        "cd_ready": "Готово",
        "cd_remaining": "{m}м {s}с",

        # Common
        "not_registered": "Сначала зарегистрируйтесь: /start",
        "area_required": "Нужна зона {min}.",
        "coins": "монет",

        # Language
        "lang_set": "Язык установлен на русский",
        "lang_cmd": "/lang — сменить язык",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    """Get translated string. Falls back to English."""
    text = T.get(lang, T["en"]).get(key, T["en"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
