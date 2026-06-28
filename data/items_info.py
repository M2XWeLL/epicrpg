"""
Item help database. Each item has: emoji, description, how to obtain, sale price.
Prices match original EPIC RPG.
"""
ITEMS_INFO = {
    # === Logs ===
    "wooden_log": {
        "emoji": "🪵",
        "desc_en": "First tier of wooden logs",
        "desc_ru": "Первый уровень деревянных бревен",
        "obtain_en": "Obtained in chop, axe, bowsaw, chainsaw and from lootboxes\nIt can also be crafted (recipes items)",
        "obtain_ru": "Получается в chop, axe, bowsaw, chainsaw и из лутбоксов\nМожно скрафтить (рецепты)",
        "price": 25,
    },
    "epic_log": {
        "emoji": "🪵",
        "desc_en": "Second tier of wooden logs",
        "desc_ru": "Второй уровень деревянных бревен",
        "obtain_en": "Obtained in axe, bowsaw, chainsaw and from lootboxes",
        "obtain_ru": "Получается в axe, bowsaw, chainsaw и из лутбоксов",
        "price": 75,
    },
    "super_log": {
        "emoji": "🪵",
        "desc_en": "Third tier of wooden logs",
        "desc_ru": "Третий уровень деревянных бревен",
        "obtain_en": "Obtained in bowsaw, chainsaw and from lootboxes",
        "obtain_ru": "Получается в bowsaw, chainsaw и из лутбоксов",
        "price": 200,
    },
    "mega_log": {
        "emoji": "🪵",
        "desc_en": "Fourth tier of wooden logs",
        "desc_ru": "Четвертый уровень деревянных бревен",
        "obtain_en": "Obtained in bowsaw, chainsaw and from lootboxes",
        "obtain_ru": "Получается в bowsaw, chainsaw и из лутбоксов",
        "price": 500,
    },
    "hyper_log": {
        "emoji": "🪵",
        "desc_en": "Fifth tier of wooden logs",
        "desc_ru": "Пятый уровень деревянных бревен",
        "obtain_en": "Obtained in chainsaw and from lootboxes",
        "obtain_ru": "Получается в chainsaw и из лутбоксов",
        "price": 1250,
    },
    "ultra_log": {
        "emoji": "🪵",
        "desc_en": "Sixth tier of wooden logs",
        "desc_ru": "Шестой уровень деревянных бревен",
        "obtain_en": "Obtained in chainsaw and from lootboxes",
        "obtain_ru": "Получается в chainsaw и из лутбоксов",
        "price": 2500,
    },
    "ultimate_log": {
        "emoji": "🪵",
        "desc_en": "Seventh tier of wooden logs",
        "desc_ru": "Седьмой уровень деревянных бревен",
        "obtain_en": "Obtained in chainsaw and from lootboxes",
        "obtain_ru": "Получается в chainsaw и из лутбоксов",
        "price": 5000,
    },

    # === Fish ===
    "normie_fish": {
        "emoji": "🐟",
        "desc_en": "First tier of fish",
        "desc_ru": "Первый уровень рыбы",
        "obtain_en": "Obtained in fish, net, boat, bigboat and from lootboxes",
        "obtain_ru": "Получается в fish, net, boat, bigboat и из лутбоксов",
        "price": 40,
    },
    "golden_fish": {
        "emoji": "🐟",
        "desc_en": "Second tier of fish",
        "desc_ru": "Второй уровень рыбы",
        "obtain_en": "Obtained in fish, net, boat, bigboat and from lootboxes\nIt can also be crafted (recipes items)",
        "obtain_ru": "Получается в fish, net, boat, bigboat и из лутбоксов\nМожно скрафтить (рецепты)",
        "price": 200,
    },
    "epic_fish": {
        "emoji": "🐟",
        "desc_en": "Third tier of fish, unlocked in Area 2",
        "desc_ru": "Третий уровень рыбы, откроется в Area 2",
        "obtain_en": "Obtained in fish, net, boat, bigboat and from lootboxes\nIt can also be crafted (recipes items)",
        "obtain_ru": "Получается в fish, net, boat, bigboat и из лутбоксов\nМожно скрафтить (рецепты)",
        "price": 75000,
    },
    "super_fish": {
        "emoji": "🐟",
        "desc_en": "Fourth tier of fish",
        "desc_ru": "Четвертый уровень рыбы",
        "obtain_en": "Obtained in boat, bigboat and from lootboxes",
        "obtain_ru": "Получается в boat, bigboat и из лутбоксов",
        "price": 750,
    },
    "mega_fish": {
        "emoji": "🐟",
        "desc_en": "Fifth tier of fish",
        "desc_ru": "Пятый уровень рыбы",
        "obtain_en": "Obtained in bigboat and from lootboxes",
        "obtain_ru": "Получается в bigboat и из лутбоксов",
        "price": 1750,
    },
    "hyper_fish": {
        "emoji": "🐟",
        "desc_en": "Sixth tier of fish",
        "desc_ru": "Шестой уровень рыбы",
        "obtain_en": "Obtained in bigboat and from lootboxes",
        "obtain_ru": "Получается в bigboat и из лутбоксов",
        "price": 3500,
    },

    # === Monster drops ===
    "wolfskin": {
        "emoji": "🐺",
        "desc_en": "It is a monster drop",
        "desc_ru": "Выпадает с монстров",
        "obtain_en": "Dropped from WOLF (4%), found with hunt — [Area 1 ~ 2]",
        "obtain_ru": "Выпадает с WOLF (4%), охота — [Area 1 ~ 2]",
        "price": 500,
    },
    "zombieeye": {
        "emoji": "👁️",
        "desc_en": "It is a monster drop, unlocked in Area 3",
        "desc_ru": "Выпадает с монстров, откроется в Area 3",
        "obtain_en": "Dropped from ZOMBIE (4%), found with hunt — [Area 3 ~ 4]",
        "obtain_ru": "Выпадает с ZOMBIE (4%), охота — [Area 3 ~ 4]",
        "price": 2000,
    },
    "unicornhorn": {
        "emoji": "🦄",
        "desc_en": "It is a monster drop, unlocked in Area 5",
        "desc_ru": "Выпадает с монстров, откроется в Area 5",
        "obtain_en": "Dropped from UNICORN (4%), found with hunt — [Area 5 ~ 6]",
        "obtain_ru": "Выпадает с UNICORN (4%), охота — [Area 5 ~ 6]",
        "price": 7500,
    },
    "mermaid_hair": {
        "emoji": "🧜",
        "desc_en": "It is a monster drop, unlocked in Area 7",
        "desc_ru": "Выпадает с монстров, откроется в Area 7",
        "obtain_en": "Dropped from MERMAID (4%), found with hunt — [Area 7 ~ 8]",
        "obtain_ru": "Выпадает с MERMAID (4%), охота — [Area 7 ~ 8]",
        "price": 30000,
    },
    "chip": {
        "emoji": "🔧",
        "desc_en": "It is a monster drop, unlocked in Area 9",
        "desc_ru": "Выпадает с монстров, откроется в Area 9",
        "obtain_en": "Dropped from KILLER ROBOT (4%), found with hunt — [Area 9 ~ 10]",
        "obtain_ru": "Выпадает с KILLER ROBOT (4%), охота — [Area 9 ~ 10]",
        "price": 100000,
    },
    "dragonscale": {
        "emoji": "🐉",
        "desc_en": "It is a monster drop, unlocked in Area 11",
        "desc_ru": "Выпадает с монстров, откроется в Area 11",
        "obtain_en": "Dropped from SCALED DRAGONS (4%), found with hunt — [Area 11 ~ 15]",
        "obtain_ru": "Выпадает с SCALED DRAGONS (4%), охота — [Area 11 ~ 15]",
        "price": 250000,
    },
    "ruby": {
        "emoji": "💎",
        "desc_en": "A precious gemstone",
        "desc_ru": "Драгоценный камень",
        "obtain_en": "Obtained from lootboxes and rare drops",
        "obtain_ru": "Получается из лутбоксов и редких дропов",
        "price": 50000,
    },

    # === Crops ===
    "apple": {
        "emoji": "🍎",
        "desc_en": "First tier of fruit, unlocked in Area 3",
        "desc_ru": "Первый уровень фруктов, откроется в Area 3",
        "obtain_en": "Obtained in pickup, ladder, tractor, greenhouse and from lootboxes\nIt can also be crafted (recipes items)",
        "obtain_ru": "Получается в pickup, ladder, tractor, greenhouse и из лутбоксов\nМожно скрафтить (рецепты)",
        "price": 2000,
    },
    "banana": {
        "emoji": "🍌",
        "desc_en": "Second tier of fruit, unlocked in Area 3",
        "desc_ru": "Второй уровень фруктов, откроется в Area 3",
        "obtain_en": "Obtained in pickup, ladder, tractor, greenhouse and from lootboxes\nIt can also be crafted (recipes items)",
        "obtain_ru": "Получается в pickup, ladder, tractor, greenhouse и из лутбоксов\nМожно скрафтить (рецепты)",
        "price": 10000,
    },
    "potato": {
        "emoji": "🥔",
        "desc_en": "A humble potato",
        "desc_ru": "Скромная картошка",
        "obtain_en": "Obtained in farm, pickup and from lootboxes",
        "obtain_ru": "Получается на ферме, в pickup и из лутбоксов",
        "price": 10,
    },
    "carrot": {
        "emoji": "🥕",
        "desc_en": "An orange carrot",
        "desc_ru": "Оранжевая морковь",
        "obtain_en": "Obtained in farm and from lootboxes",
        "obtain_ru": "Получается на ферме и из лутбоксов",
        "price": 20,
    },
    "bread": {
        "emoji": "🍞",
        "desc_en": "Freshly baked bread",
        "desc_ru": "Свежеиспеченный хлеб",
        "obtain_en": "Obtained in farm, cook and from lootboxes",
        "obtain_ru": "Получается на ферме, в cook и из лутбоксов",
        "price": 30,
    },
    "Watermelon": {
        "emoji": "🍉",
        "desc_en": "A big watermelon",
        "desc_ru": "Большая арбузина",
        "obtain_en": "Obtained from lootboxes",
        "obtain_ru": "Получается из лутбоксов",
        "price": 250,
    },

    # === Coins / Special ===
    "coin": {
        "emoji": "🪙",
        "desc_en": "The main currency",
        "desc_ru": "Основная валюта",
        "obtain_en": "Obtained from almost everything",
        "obtain_ru": "Получается почти от всего",
        "price": 1,
    },
    "life_potion": {
        "emoji": "🧪",
        "desc_en": "Restores 50% of your max HP",
        "desc_ru": "Восстанавливает 50% максимального HP",
        "obtain_en": "Buy with /buy life_potion or from lootboxes",
        "obtain_ru": "Купить: /buy life_potion или из лутбоксов",
        "price": 10,
    },
    "arenacookie": {
        "emoji": "🍪",
        "desc_en": "Gives +10% damage in arena fights",
        "desc_ru": "Даёт +10% урона в арене",
        "obtain_en": "Buy with /buy arenacookie",
        "obtain_ru": "Купить: /buy arenacookie",
        "price": 50,
    },
    "lotteryticket": {
        "emoji": "🎫",
        "desc_en": "A lottery ticket for the weekly draw",
        "desc_ru": "Лотерейный билет для еженедельного розыгрыша",
        "obtain_en": "Buy with /buy lotteryticket",
        "obtain_ru": "Купить: /buy lotteryticket",
        "price": 500,
    },
    "seed": {
        "emoji": "🌱",
        "desc_en": "Plant this in the farm to grow crops",
        "desc_ru": "Посади на ферме чтобы вырастить урожай",
        "obtain_en": "Buy with /buy seed",
        "obtain_ru": "Купить: /buy seed",
        "price": 4000,
    },

    # === Returning Event items ===
    "smol_coin": {
        "emoji": "🪙",
        "desc_en": "A small event coin used in the Returning Event shop",
        "desc_ru": "Мелкая монета события, используется в магазине Возвращения",
        "obtain_en": "Obtained from hunt, adventure, and working commands during Returning Event",
        "obtain_ru": "Получается из охоты, приключений и рабочих команд во время события Возвращения",
        "price": 0,
    },
    "magic_bed": {
        "emoji": "🛏️",
        "desc_en": "A magical bed from the Returning Event",
        "desc_ru": "Магическая кровать из события Возвращения",
        "obtain_en": "Reward from Returning Event super daily (day 3)",
        "obtain_ru": "Награда за супер дейли события Возвращения (день 3)",
        "price": 0,
    },
    "omega_horse_token": {
        "emoji": "🐴",
        "desc_en": "OMEGA Horse Token from the Returning Event",
        "desc_ru": "Омега токен лошади из события Возвращения",
        "obtain_en": "Reward from Returning Event super daily (days 4, 7)",
        "obtain_ru": "Награда за супер дейли события Возвращения (дни 4, 7)",
        "price": 0,
    },

    # === Lootboxes ===
    "common_lootbox": {
        "emoji": "📦",
        "desc_en": "Contains a few items",
        "desc_ru": "Содержит несколько предметов",
        "obtain_en": "Buy with /buy common_lootbox",
        "obtain_ru": "Купить: /buy common_lootbox",
        "price": 400,
    },
    "uncommon_lootbox": {
        "emoji": "📦",
        "desc_en": "Contains some items",
        "desc_ru": "Содержит предметы",
        "obtain_en": "Buy with /buy uncommon_lootbox",
        "obtain_ru": "Купить: /buy uncommon_lootbox",
        "price": 3000,
    },
    "rare_lootbox": {
        "emoji": "📦",
        "desc_en": "Contains many items",
        "desc_ru": "Содержит много предметов",
        "obtain_en": "Buy with /buy rare_lootbox",
        "obtain_ru": "Купить: /buy rare_lootbox",
        "price": 20000,
    },
    "epic_lootbox": {
        "emoji": "📦",
        "desc_en": "Contains a lot of items",
        "desc_ru": "Содержит очень много предметов",
        "obtain_en": "Buy with /buy epic_lootbox",
        "obtain_ru": "Купить: /buy epic_lootbox",
        "price": 75000,
    },
    "edgy_lootbox": {
        "emoji": "📦",
        "desc_en": "Contains A LOT of items",
        "desc_ru": "Содержит ОЧЕНЬ много предметов",
        "obtain_en": "Buy with /buy edgy_lootbox",
        "obtain_ru": "Купить: /buy edgy_lootbox",
        "price": 210000,
    },
    "omega_lootbox": {
        "emoji": "📦",
        "desc_en": "Contains A TON of items",
        "desc_ru": "Содержит ТОННУ предметов",
        "obtain_en": "Buy with /buy omega_lootbox",
        "obtain_ru": "Купить: /buy omega_lootbox",
        "price": 1000000,
    },

    # === Dungeon key ===
    "dungeon_key": {
        "emoji": "🗝️",
        "desc_en": "Required to enter dungeons",
        "desc_ru": "Нужен для входа в подземелья",
        "obtain_en": "Buy with /buy dungeon_key",
        "obtain_ru": "Купить: /buy dungeon_key",
        "price": 500,
    },
}


def find_item(query: str) -> tuple | None:
    """Search for an item by name (fuzzy match). Returns (key, info) or None."""
    q = query.lower().strip()

    # Direct match
    if q in ITEMS_INFO:
        return q, ITEMS_INFO[q]

    # Try replacing spaces with underscores
    q_under = q.replace(" ", "_")
    if q_under in ITEMS_INFO:
        return q_under, ITEMS_INFO[q_under]

    # Partial match — find items where query is contained in the key
    q_nospace = q.replace(" ", "")
    matches = []
    for key, info in ITEMS_INFO.items():
        key_nospace = key.replace("_", "")
        if q in key or q in key.replace("_", " ") or q_nospace in key_nospace:
            matches.append((key, info))

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        return matches[0]

    return None
