"""
Lootbox system — 7 tiers with area-gated drops.
"""
import random
import json
import config


LOOTBOX_TIERS = {
    "common": {
        "name": "Common Lootbox",
        "price": 800,
        "min_level": 2,
        "item_range": (1, 2),
        "cooldown_hours": 3,
        "common": {
            "wooden_log": (3, 8),
            "normie_fish": (2, 5),
        },
        "uncommon": {
            "epic_log": (2, 5),
            "golden_fish": (1, 3),
        },
        "rare": {
            "wolfskin": (1, 2),
        },
    },
    "uncommon": {
        "name": "Uncommon Lootbox",
        "price": 6000,
        "min_level": 4,
        "item_range": (3, 5),
        "cooldown_hours": 3,
        "common": {
            "wooden_log": (5, 15),
            "normie_fish": (3, 8),
            "epic_log": (3, 8),
            "golden_fish": (2, 5),
        },
        "uncommon": {
            "wolfskin": (2, 5),
        },
        "rare": {
            "common_lootbox": (1, 1),
            "zombieeye": (1, 3),
            "super_log": (1, 3),
        },
    },
    "rare": {
        "name": "Rare Lootbox",
        "price": 40000,
        "min_level": 6,
        "item_range": (7, 10),
        "cooldown_hours": 3,
        "common": {
            "wooden_log": (10, 25),
            "normie_fish": (5, 15),
            "apple": (3, 8),
            "epic_log": (5, 12),
            "golden_fish": (3, 8),
        },
        "uncommon": {
            "banana": (2, 5),
            "wolfskin": (3, 8),
            "zombieeye": (2, 5),
        },
        "rare": {
            "uncommon_lootbox": (1, 1),
            "super_log": (3, 6),
            "unicornhorn": (1, 2),
            "mega_log": (1, 3),
        },
    },
    "epic": {
        "name": "EPIC Lootbox",
        "price": 150000,
        "min_level": 8,
        "item_range": (12, 17),
        "cooldown_hours": 3,
        "common": {
            "apple": (5, 12),
            "epic_log": (8, 18),
            "golden_fish": (5, 10),
            "banana": (3, 8),
        },
        "uncommon": {
            "wolfskin": (5, 12),
            "zombieeye": (3, 8),
            "unicornhorn": (2, 5),
            "ruby": (1, 3),
            "super_log": (5, 10),
        },
        "rare": {
            "rare_lootbox": (1, 1),
            "mermaid_hair": (1, 3),
            "mega_log": (3, 8),
            "hyper_log": (1, 3),
        },
    },
    "edgy": {
        "name": "EDGY Lootbox",
        "price": 420666,
        "min_level": 10,
        "item_range": (19, 26),
        "cooldown_hours": 3,
        "common": {
            "epic_log": (10, 20),
            "golden_fish": (5, 12),
            "banana": (5, 10),
            "ruby": (2, 5),
        },
        "uncommon": {
            "wolfskin": (5, 12),
            "zombieeye": (3, 8),
            "unicornhorn": (3, 6),
            "mermaid_hair": (2, 5),
            "chip": (1, 3),
            "super_log": (5, 10),
            "mega_log": (3, 8),
        },
        "rare": {
            "epic_lootbox": (1, 1),
            "epic_fish": (2, 5),
            "hyper_log": (2, 5),
            "ultra_log": (1, 3),
        },
    },
    "omega": {
        "name": "OMEGA Lootbox",
        "price": 0,  # drop only
        "min_level": 12,
        "item_range": (31, 44),
        "cooldown_hours": 0,  # no buy cooldown
        "common": {
            "mega_log": (10, 20),
            "epic_fish": (5, 12),
            "hyper_log": (5, 10),
        },
        "uncommon": {
            "dragonscale": (2, 5),
            "epic_fish": (3, 8),
        },
        "rare": {
            "ultra_log": (3, 8),
        },
    },
    "godly": {
        "name": "GODLY Lootbox",
        "price": 0,  # drop only
        "min_level": 15,
        "item_range": (500, 800),
        "cooldown_hours": 0,
        "common": {
            "arenacookie": (20, 50),
        },
        "uncommon": {
            "dragonscale": (5, 10),
            "ultra_log": (5, 10),
        },
        "rare": {
            "ultimate_log": (3, 8),
        },
    },
}

# Area-gated items: items that can only drop in certain areas
AREA_GATED_ITEMS = {
    "wolfskin": 2,
    "zombieeye": 3,
    "apple": 3,
    "ruby": 5,
    "unicornhorn": 6,
    "mermaid_hair": 8,
    "chip": 10,
    "dragonscale": 11,
    "lotteryticket": 13,
    "banana": 6,
    "mega_log": 7,
    "hyper_log": 9,
    "ultra_log": 11,
    "ultimate_log": 14,
    "super_log": 5,
    "epic_fish": 7,
    "super_fish": 9,
    "mega_fish": 11,
}


def _filter_by_area(pool: dict, user_area: int) -> dict:
    """Remove items that can't be obtained in the user's current area."""
    filtered = {}
    for mat, amt_range in pool.items():
        min_area = AREA_GATED_ITEMS.get(mat, 1)
        if user_area >= min_area:
            filtered[mat] = amt_range
    return filtered


def open_lootbox(user_id: int, box_type: str, user_area: int) -> dict:
    """Open a lootbox and return the drops."""
    tier = LOOTBOX_TIERS.get(box_type)
    if not tier:
        return {"success": False, "message": f"❌ Неизвестный лутбокс: {box_type}"}

    min_count, max_count = tier["item_range"]
    total_items = random.randint(min_count, max_count)

    drops = {}
    items_collected = 0

    # Distribute items across rarity pools
    for rarity in ["common", "uncommon", "rare"]:
        pool = tier.get(rarity, {})
        pool = _filter_by_area(pool, user_area)
        if not pool:
            continue

        if rarity == "common":
            count = random.randint(total_items // 2, total_items)
        elif rarity == "uncommon":
            count = random.randint(total_items // 4, total_items // 2)
        else:
            count = random.randint(1, max(1, total_items // 4))

        for _ in range(count):
            mat = random.choice(list(pool.keys()))
            amt_range = pool[mat]
            amt = random.randint(amt_range[0], amt_range[1])
            drops[mat] = drops.get(mat, 0) + amt

    return {"success": True, "drops": drops, "box_type": box_type, "box_name": tier["name"]}


def format_lootbox_drops(box_name: str, drops: dict) -> str:
    """Format lootbox drops for display."""
    with open(config.DATA_DIR / "materials.json", "r", encoding="utf-8") as f:
        mat_data = json.load(f)
    names = mat_data.get("names", {})
    emojis = mat_data.get("emojis", {})

    text = f"📦 <b>{box_name}</b>\n\n"
    for mat, amt in sorted(drops.items(), key=lambda x: -x[1]):
        name = names.get(mat, mat)
        emoji = emojis.get(mat, "•")
        text += f"  {emoji} +{amt} {name}\n"

    total = sum(drops.values())
    text += f"\nВсего: {total} предметов"
    return text


def get_shop_text() -> str:
    """Format the lootbox shop."""
    text = "📦 <b>Магазин лутбоксов</b>\n\n"
    for key, tier in LOOTBOX_TIERS.items():
        if tier["price"] > 0:
            text += f"  {tier['name']} — {tier['price']:,} монет (Lvl {tier['min_level']})\n"
        else:
            text += f"  {tier['name']} — только по дропу\n"
    text += "\nКупить: /buy [lootbox_name]"
    text += "\nОткрыть: /open [lootbox_name]"
    return text
