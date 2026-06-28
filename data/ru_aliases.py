"""
Russian command and item name aliases.
Maps Russian → English so players can use both languages.
"""

# --- Russian commands → English commands ---
RU_COMMANDS = {
    # Progress
    "профиль": "profile", "проф": "profile",
    "инвентарь": "inventory", "инв": "inventory",
    "профессии": "professions", "професии": "professions",
    "кулдауны": "cooldowns", "кулдаун": "cooldowns", "кд": "cooldowns",
    "квест": "quest",
    "лошадь": "horse", "конь": "horse",
    "питомцы": "pets", "питомец": "pets", "зверёк": "pets", "зверек": "pets",
    "фьюжн": "fusion", "слияние": "fusion",
    "титул": "title",
    "достижения": "achievements", "ачивки": "achievements",
    "бусты": "boosts", "артефакты": "artifacts", "арты": "artifacts",
    "карточки": "cards", "топ": "top",
    "туториал": "tutorial", "гайд": "tutorial", "обучение": "tutorial",
    # Fighting
    "охота": "hunt", "приключение": "adventure", "приклю": "adventure",
    "лечение": "heal", "исцелить": "heal",
    "дуэль": "duel", "дуэл": "duel",
    "подземелье": "dungeon", "данж": "dungeon", "данжон": "dungeon",
    "арена": "arena", "ав": "arena",
    "минибосс": "miniboss", "минибос": "miniboss", "миба": "miniboss",
    # Economy
    "магазин": "shop", "шоп": "shop", "магазинчик": "shop",
    "эпик шоп": "epic shop", "эпичный магазин": "epic shop",
    "купить": "buy", "продать": "sell",
    "передать": "give", "give": "give",
    "использовать": "use",
    "лотерея": "lottery", "лутерка": "lottery",
    "лутбокс": "lootbox", "лутб": "lootbox", "лут": "lootbox",
    "открыть": "open",
    # Working
    "рубить": "chop", "рублить": "chop", "дрова": "chop",
    "рыбачить": "fish", "рыба": "fish",
    "копать": "mine", "шахта": "mine",
    "сбор": "pickup", "пикап": "pickup",
    "ферма": "farm", "фарм": "farm",
    "крафт": "craft", "крафтик": "craft",
    "разбор": "dismantle",
    "рецепты": "recipes", "рецепт": "recipes",
    "готовка": "cook",
    # Gambling
    "кубики": "dice", "dice": "dice",
    "большие кубики": "big dice", "большой кубик": "big dice",
    "стаканы": "cups", "cups": "cups",
    "блэкджек": "blackjack", "blackjack": "blackjack",
    "слоты": "slots", "слот": "slots", "slots": "slots",
    "монетка": "cf", "cf": "cf",
    # Rewards
    "ежедневная": "daily", "дэйли": "daily", "дэйлика": "daily",
    "еженедельная": "weekly", "викли": "weekly",
    "голосовать": "vote", "голос": "vote",
    "промокод": "code", "код": "code",
    "донат": "donate",
    # Higher areas
    "зачарование": "enchant", "зачаровать": "enchant", "заинт": "enchant",
    "тренировка": "training", "треник": "training", "трени": "training",
    "лестница": "ladder",
    "гильдия": "guild", "гилда": "guild",
    "мультикости": "multidice", "мультикость": "multidice", "мультик": "multidice",
    "бензопила": "bowsaw", "bowsaw": "bowsaw",
    "лодка": "boat", "boat": "boat",
    "переплавка": "refine",
    "большая арена": "big arena", "большая ав": "big arena", "big arena": "big arena",
    "алхимия": "alchemy",
    "трактор": "tractor",
    "колесо": "wheel", "колесо фортуны": "wheel",
    "цепная пила": "chainsaw", "chainsaw": "chainsaw",
    "большая лодка": "bigboat", "bigboat": "bigboat",
    "дрель": "drill",
    "динамит": "dynamite",
    "ультротренировка": "ultraining", "ультратреник": "ultraining",
    "бейдж": "badge",
    "трансмутация": "transmute",
    "кузница": "forge",
    "оранжерея": "greenhouse",
    "трансценд": "transcend",
    "хардмод охота": "hunt hardmode", "хард охота": "hunt hardmode",
    "хардмод приключение": "adventure hardmode", "хард приклю": "adventure hardmode",
    "тим травел": "timetravel", "тт": "timetravel",
    "путешествие во времени": "timetravel",
    "супер тт": "super timetravel", "супер путешествие": "super timetravel",
    # Bank
    "банк": "bank", "депозит": "deposit", "снять": "withdraw",
    # Marriage
    "свадьба": "marry", "жена": "marry", "муж": "marry",
    "развод": "divorce",
    "охота вместе": "hunt_together", "охота вдвоём": "hunt_together",
    "охота одна": "hunt_alone", "одиночная охота": "hunt_alone",
    # Epic quest
    "эпик квест": "epic_quest", "эпическое задание": "epic_quest",
    # Quest
    "квест": "quest", "задание": "quest",
    "квест начать": "quest_start", "начать квест": "quest_start",
    "квест прогресс": "quest_progress", "прогресс квеста": "quest_progress",
    "квест бросить": "quest_quit", "бросить квест": "quest_quit",
    # Refine/transmute/transcend
    "шлифовка": "refine", "шлифовать": "refine",
    "трансмутация": "transmute", "трансмутировать": "transmute",
    "трансцендентность": "transcend", "трансцендировать": "transcend",
    # Cosmetic
    "фон": "bg", "мир": "world",
    # Misc
    "настройки": "settings",
    "помощь": "help", "хелп": "help",
    "правила": "rules",
    "старт": "start",
    "язык": "lang",
    "монеты": "coins",
    "жизнь": "life", "здоровье": "life",
    # Trade
    "обмен": "trade", "торговля": "trade",
}

# --- Russian item names → English item IDs ---
RU_ITEMS = {
    # Logs
    "деревянное бревно": "wooden_log", "древесина": "wooden_log",
    "эпичный лог": "epic_log", "супер лог": "super_log",
    "мега лог": "mega_log", "хайпер лог": "hyper_log",
    "ультра лог": "ultra_log", "ультимейт лог": "ultimate_log",
    # Fish
    "рыба": "normie_fish", "золотая рыба": "golden_fish",
    "эпичная рыба": "epic_fish", "супер рыба": "super_fish",
    "мега рыба": "mega_fish", "хайпер рыба": "hyper_fish",
    # Crops
    "яблоко": "apple", "банан": "banana", "картошка": "potato",
    "морковь": "carrot", "хлеб": "bread", "арбуз": "Watermelon",
    # Monster drops
    "волчья шкура": "wolfskin", "шкура волка": "wolfskin",
    "глаз зомби": "zombieeye", "рог единорога": "unicornhorn",
    "волос русалки": "mermaid_hair", "чип": "chip",
    "чешуя дракона": "dragonscale", "рубин": "ruby",
    # Coins / Special
    "монета": "coin", "монеты": "coin", "зелье жизни": "life_potion",
    "печенье арены": "arenacookie", "лотерейный билет": "lotteryticket",
    "семя": "seed", "семена": "seed",
    # Lootboxes
    "обычный лутбокс": "common_lootbox", "необычный лутбокс": "uncommon_lootbox",
    "редкий лутбокс": "rare_lootbox", "эпичный лутбокс": "epic_lootbox",
    "еджий лутбокс": "edgy_lootbox", "омега лутбокс": "omega_lootbox",
    "божественный лутбокс": "godly_lootbox",
    # Equipment
    "базовый меч": "basic_sword", "базовая броня": "basic_armor",
    "базовая лошадь": "basic_horse", "ключ подземелья": "dungeon_key",
    "купить ключ": "dungeon buy", "купить ключ подземелья": "dungeon buy",
    # Cook
    "запечённая рыба": "baked_fish", "хейрн": "hairn",
    "фруктовый салат": "fruit_salad", "яблочный сок": "apple_juice",
    "морковный хлеб": "carrot_bread", "апельсиновый сок": "orange_juice",
    "супер печенье": "super_cookie",
}


def resolve_item(query: str) -> str:
    """Resolve Russian item names to English item IDs."""
    q = query.lower().strip()
    if q in RU_ITEMS:
        return RU_ITEMS[q]
    q_under = q.replace(" ", "_")
    if q_under in RU_ITEMS:
        return RU_ITEMS[q_under]
    return q
