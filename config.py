import os
from pathlib import Path

BOT_TOKEN = os.getenv("EPIC_RPG_BOT_TOKEN", "7397663968:AAHlW7ejW71UjpVfGAUKXhu77VHXtfYExjc")
BASE_DIR = Path(__file__).parent
DB_URL = os.getenv("DB_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'epic_rpg.db'}")
DATA_DIR = BASE_DIR / "data"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# --- Cooldowns (seconds) ---
COOLDOWNS = {
    "hunt": 60,          # 1 min
    "adventure": 3600,   # 1 hour
    "chop": 300,         # 5 min
    "mine": 300,         # 5 min
    "fish": 300,         # 5 min
    "pickup": 300,       # 5 min
    "arena": 300,        # 5 min
    "duel": 120,         # 2 min
    "daily": 86400,      # 24 hours
    "weekly": 604800,    # 7 days
    "vote": 43200,       # 12 hours
    "enchant": 600,      # 10 min
    "training": 900,     # 15 min
    "farm": 600,         # 10 min
    "cook": 900,         # 15 min
    "greenhouse": 7200,  # 2 hours
    "multidice": 300,    # 5 min
}

# --- Player stat formulas ---
ATK_WEAPON_TIER = {
    1: 10, 2: 25, 3: 50, 4: 85, 5: 130, 6: 185, 7: 250, 8: 325, 9: 410, 10: 500,
    11: 600, 12: 710, 13: 830, 14: 960, 15: 1100,
    # Forge
    70: 300, 100: 400, 200: 500, 500: 0,
    # Void Forge
    16: 750, 17: 1000, 18: 2500, 19: 5000, 20: 10000,
}
ARMOR_DEF_TIER = {
    1: 8, 2: 20, 3: 40, 4: 70, 5: 110, 6: 160, 7: 220, 8: 290, 9: 370, 10: 460,
    11: 560, 12: 670, 13: 790, 14: 920, 15: 1060,
    # Forge
    70: 300, 100: 400, 200: 500, 500: 0,
    # Void Forge
    16: 750, 17: 1000, 18: 2500, 19: 5000, 20: 10000,
}
MAX_LEVEL = 150
MAX_AREA = 15

# --- XP curve: floor(100 * L^2.2 + 500 * L) ---
XP_BASE = 100
XP_EXP = 2.2
XP_FLAT = 500

# --- TT bonuses (wiki-accurate quadratic formulas) ---
# XP:       (99 + x) * x / 2
# Duel XP:  (99 + x) * x / 4
# Drops:    (49 + x) * x / 2
# Items:    (49 + x) * x / 2
TT_MAX_REGULAR = 25  # max regular TTs before STT unlocks
TT_ENCHANT_BONUS_PER_TT = 0.2  # enchant multiplier per TT (linear)
TT_CD_REDUCTION = 0.01
TT_CD_MAX = 0.50
BASE_MAX_LEVEL = 50
TT_LEVEL_BONUS = 15  # extra max level per TT

# --- TT titles (wiki) ---
TT_TITLES = {
    1:  "Time Traveler",
    2:  "One time wasn't enough",
    5:  "I spend too much time here",
    10: "OOF",
    25: "OOFMEGA",
    50: "GOOFDLY",
    75: "VOOFID",
}

# --- TT dungeon unlocks (wiki) ---
# highest dungeon unlocked by TT count
TT_DUNGEON_UNLOCK = {
    0: 10,
    1: 11, 2: 11,
    3: 12, 4: 12,
    5: 13, 6: 13, 7: 13, 8: 13, 9: 13,
    10: 14, 11: 14, 12: 14, 13: 14, 14: 14, 15: 14, 16: 14, 17: 14, 18: 14, 19: 14, 20: 14, 21: 14, 22: 14, 23: 14, 24: 14,
    25: 15,
}

# --- Coin trading restrictions (wiki) ---
TT_NO_TRADE_AFTER = {2: (0, 1), 20: (0, 19)}  # tt_count -> max TT of players you can trade with

# --- Crafting ---
CONVERSION_RATE = 5

# --- Pet system (wiki-accurate) ---
PET_MAX_BASE = 5  # base max pets, +1 per TT
PET_RANK_ORDER = ["F", "E", "D", "C", "B", "A", "S", "SS", "SS+"]
PET_RANK_MULT = {"F": 1, "E": 2, "D": 3, "C": 4, "B": 5, "A": 6, "S": 7, "SS": 8, "SS+": 9}
PET_SKILL_SCORES = {
    "fast": 2, "happy": 4, "clever": 6, "digger": 8, "lucky": 10,
    "time_traveler": 12, "epic": 14, "ascended": 504,
    "perfect": 0, "fighter": 0, "master": 0, "normie": 0,
}
# Tier roman numeral mappings
_TIER_ROMAN = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII",
    8: "VIII", 9: "IX", 10: "X", 11: "XI", 12: "XII", 13: "XIII",
    14: "XIV", 15: "XV", 16: "XVI", 17: "XVII", 18: "XVIII", 19: "XIX",
    20: "XX", 21: "XXI", 22: "XXII", 23: "XXIII", 24: "XXIV", 25: "XXV",
}
_TIER_ARABIC = {v: k for k, v in _TIER_ROMAN.items()}


def pet_tier_to_num(tier_str: str) -> int:
    return _TIER_ARABIC.get(tier_str, 1)


def pet_num_to_tier(num: int) -> str:
    return _TIER_ROMAN.get(num, "I")


def calc_pet_score(tier_num: int, skill: str, rank: str) -> int:
    """Wiki formula: pet_score = tier * (tier + skill_score * rank_multiplier)"""
    skill_score = PET_SKILL_SCORES.get(skill, 0)
    rank_mult = PET_RANK_MULT.get(rank, 1)
    return tier_num * (tier_num + skill_score * rank_mult)

# --- Materials (real Epic RPG) ---
DEFAULT_MATERIALS = {
    "wooden_log": 0, "epic_log": 0, "super_log": 0, "mega_log": 0,
    "hyper_log": 0, "ultra_log": 0, "ultimate_log": 0,
    "normie_fish": 0, "golden_fish": 0, "epic_fish": 0,
    "super_fish": 0, "mega_fish": 0, "hyper_fish": 0,
    "apple": 0, "banana": 0, "potato": 0, "carrot": 0, "bread": 0, "Watermelon": 0,
    "wolfskin": 0, "zombieeye": 0, "unicornhorn": 0, "mermaid_hair": 0,
    "ruby": 0, "chip": 0, "coin": 0, "dragonscale": 0, "lotteryticket": 0,
    "life_potion": 0, "arenacookie": 0,
    "common_lootbox": 0, "uncommon_lootbox": 0, "rare_lootbox": 0,
    "epic_lootbox": 0, "edgy_lootbox": 0, "omega_lootbox": 0, "godly_lootbox": 0,
    "heart": 0, "dragonessence": 0, "timedragonessence": 0,
    "dark_energy": 0, "void_lootbox": 0,
    "master_key_c": 0,
    "epic_berries": 0, "horse_coins": 0,
    "seed": 0, "time_cookie": 0, "flask": 0,
    # Returning event items
    "smol_coin": 0, "magic_bed": 0, "omega_horse_token": 0,
    # Regular event items
    "diamond": 0, "amber": 0, "emerald": 0, "sapphire": 0,
}

# --- Tier names for equipment display ---
TIER_NAMES = {
    1: "Wooden", 2: "Fish", 3: "Iron", 4: "Ruby", 5: "Dragon",
    6: "Dark", 7: "Frost", 8: "Necro", 9: "Obsidian", 10: "Chrono",
    11: "Ultimate", 12: "Perfect", 13: "Divine", 14: "Celestial", 15: "Void",
}

# --- Zone-unlocked commands ---
ZONE_COMMANDS = {
    2: {"enchant": "Enchant"},
    5: {"alchemy": "Alchemy"},
    8: {"arena": "Arena"},
    11: {"timetravel": "Time Travel"},
    12: {"pets": "Pets"},
    15: {"void": "Void"},
}

# --- Standard Dungeons (D1-D9) ---
DUNGEONS = {
    1: {
        "name": "Ancient Dragon",
        "boss_emoji": "🐉",
        "key_price": 5000,
        "hp_per_player": 50,
        "boss_atk": 37,
        "boss_def": 0,
        "time_limit": 2.5,  # minutes per player
        "reward_min": 10000,
        "reward_max": 45000,
        "commands": {
            "bite":    {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":    {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":   {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
        },
        "description": "Первое подземелье. Простой бой без особых механик.",
    },
    2: {
        "name": "The Too Ancient Dragon",
        "boss_emoji": "🐉",
        "key_price": 25000,
        "hp_per_player": 225,
        "boss_atk": 71,
        "boss_def": 0,
        "time_limit": 2.5,
        "reward_min": 30000,
        "reward_max": 50000,
        "commands": {
            "bite":        {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":        {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":       {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
            "epic punch":  {"chance": 0.05, "type": "attack", "multiplier": 40.0},
        },
        "description": "Появляется EPIC PUNCH — шанс 5% нанести огромный урон.",
    },
    3: {
        "name": "The Ancientest Dragon",
        "boss_emoji": "🐉",
        "key_price": 60000,
        "hp_per_player": 425,
        "boss_atk": 109,
        "boss_def": 0,
        "time_limit": 2.5,
        "reward_min": 50000,
        "reward_max": 70000,
        "commands": {
            "bite":        {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":        {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":       {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
            "epic punch":  {"chance": 0.05, "type": "attack", "multiplier": 40.0},
        },
        "description": "Ещё сильнее. EPIC PUNCH остаётся.",
    },
    4: {
        "name": "The Purple Dragon",
        "boss_emoji": "🟣",
        "key_price": 150000,
        "hp_per_player": 625,
        "boss_atk": 143,
        "boss_def": 0,
        "time_limit": 2.5,
        "reward_min": 75000,
        "reward_max": 110000,
        "commands": {
            "bite":            {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":            {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":           {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
            "healing spell":   {"chance": 0.9,  "type": "heal", "heal_pct": 0.2},
        },
        "description": "Вместо EPIC PUNCH появляется HEALING SPELL — восстановление 20% HP.",
    },
    5: {
        "name": "The Huh IDK Dragon",
        "boss_emoji": "🐉",
        "key_price": 350000,
        "hp_per_player": 1500,
        "boss_atk": 179,
        "boss_def": 0,
        "time_limit": 2.5,
        "reward_min": 90000,
        "reward_max": 150000,
        "commands": {
            "bite":            {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":            {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":           {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
            "healing spell":   {"chance": 0.9,  "type": "heal", "heal_pct": 0.2},
        },
        "description": "Больше HP, HEALING SPELL по-прежнему доступен.",
    },
    6: {
        "name": "The XD Dragon",
        "boss_emoji": "🐉",
        "key_price": 600000,
        "hp_per_player": 2500,
        "boss_atk": 215,
        "boss_def": 0,
        "time_limit": 2.5,
        "reward_min": 120000,
        "reward_max": 190000,
        "commands": {
            "bite":            {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":            {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":           {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
            "healing spell":   {"chance": 0.9,  "type": "heal", "heal_pct": 0.2},
        },
        "description": "Ещё сильнее. HEALING SPELL критически важен.",
    },
    7: {
        "name": "The 4nC13nT Dragon",
        "boss_emoji": "🐉",
        "key_price": 1000000,
        "hp_per_player": 4000,
        "boss_atk": 253,
        "boss_def": 0,
        "time_limit": 2.5,
        "reward_min": 140000,
        "reward_max": 220000,
        "commands": {
            "bite":    {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":    {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":   {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
            "dodge":   {"chance": 0.5,  "type": "counter", "counter_multiplier": 1.5},
        },
        "description": "HEALING SPELL заменяется на DODGE — контратака с шансом 50%.",
    },
    8: {
        "name": "The Meme Dragon",
        "boss_emoji": "🐉",
        "key_price": 1500000,
        "hp_per_player": 6000,
        "boss_atk": 286,
        "boss_def": 0,
        "time_limit": 2.5,
        "reward_min": 170000,
        "reward_max": 270000,
        "commands": {
            "bite":    {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":    {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":   {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
            "dodge":   {"chance": 0.5,  "type": "counter", "counter_multiplier": 1.5},
        },
        "description": "DODGE остаётся. Босс становится серьёзным.",
    },
    9: {
        "name": "The OwO Dragon",
        "boss_emoji": "🐉",
        "key_price": 2500000,
        "hp_per_player": 15000,
        "boss_atk": 283,
        "boss_def": 0,
        "time_limit": 2.5,
        "reward_min": 210000,
        "reward_max": 310000,
        "commands": {
            "bite":    {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":    {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":   {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
            "dodge":   {"chance": 0.5,  "type": "counter", "counter_multiplier": 1.5},
        },
        "description": "Последнее стандартное подземелье. Огромный HP босса.",
    },
}

# --- Hunt mob pools ---
AREA_MOBS = {
    1: [
        {"name": "SLIME", "emoji": "🟢", "hp": 30, "atk": 5, "def": 2, "xp": 10, "coins": 8},
        {"name": "WOLF", "emoji": "🐺", "hp": 50, "atk": 8, "def": 3, "xp": 15, "coins": 12,
         "drop": {"item": "wolfskin", "chance": 0.04}},
        {"name": "BANDIT", "emoji": "🗡️", "hp": 70, "atk": 12, "def": 5, "xp": 22, "coins": 18},
    ],
    2: [
        {"name": "GOBLIN", "emoji": "👺", "hp": 120, "atk": 18, "def": 8, "xp": 35, "coins": 25},
        {"name": "GOBLIN ARCHER", "emoji": "🏹", "hp": 90, "atk": 22, "def": 5, "xp": 30, "coins": 20},
        {"name": "TROLL", "emoji": "👹", "hp": 200, "atk": 15, "def": 12, "xp": 50, "coins": 40},
        {"name": "WOLF", "emoji": "🐺", "hp": 55, "atk": 10, "def": 4, "xp": 18, "coins": 15,
         "drop": {"item": "wolfskin", "chance": 0.04}},
    ],
    3: [
        {"name": "ZOMBIE", "emoji": "🧟", "hp": 250, "atk": 25, "def": 15, "xp": 60, "coins": 45,
         "drop": {"item": "zombieeye", "chance": 0.04}},
        {"name": "SKELETON", "emoji": "💀", "hp": 180, "atk": 30, "def": 10, "xp": 55, "coins": 40},
        {"name": "WRAITH", "emoji": "👻", "hp": 220, "atk": 35, "def": 8, "xp": 65, "coins": 50},
    ],
    4: [
        {"name": "FIRE IMP", "emoji": "🔥", "hp": 350, "atk": 40, "def": 18, "xp": 90, "coins": 65},
        {"name": "MAGMA GOLEM", "emoji": "🌋", "hp": 500, "atk": 35, "def": 25, "xp": 110, "coins": 80},
        {"name": "ZOMBIE", "emoji": "🧟", "hp": 280, "atk": 28, "def": 18, "xp": 70, "coins": 50,
         "drop": {"item": "zombieeye", "chance": 0.04}},
    ],
    5: [
        {"name": "WYVERN", "emoji": "🐉", "hp": 600, "atk": 50, "def": 28, "xp": 140, "coins": 100},
        {"name": "DRAGON WHELP", "emoji": "🐲", "hp": 500, "atk": 55, "def": 22, "xp": 130, "coins": 90},
        {"name": "ELDER DRAGON", "emoji": "🦖", "hp": 800, "atk": 60, "def": 30, "xp": 160, "coins": 120},
        {"name": "UNICORN", "emoji": "🦄", "hp": 550, "atk": 45, "def": 25, "xp": 145, "coins": 105,
         "drop": {"item": "unicornhorn", "chance": 0.04}},
    ],
    6: [
        {"name": "SHADOW WOLF", "emoji": "🌑", "hp": 900, "atk": 70, "def": 35, "xp": 200, "coins": 140},
        {"name": "DARK ELF", "emoji": "🧝", "hp": 750, "atk": 80, "def": 28, "xp": 210, "coins": 150},
        {"name": "UNICORN", "emoji": "🦄", "hp": 700, "atk": 60, "def": 30, "xp": 180, "coins": 130,
         "drop": {"item": "unicornhorn", "chance": 0.04}},
    ],
    7: [
        {"name": "ICE ELEMENTAL", "emoji": "❄️", "hp": 1400, "atk": 90, "def": 50, "xp": 280, "coins": 200},
        {"name": "YETI", "emoji": "🏔️", "hp": 1800, "atk": 75, "def": 60, "xp": 320, "coins": 230},
        {"name": "MERMAID", "emoji": "🧜‍♀️", "hp": 1300, "atk": 100, "def": 45, "xp": 290, "coins": 210,
         "drop": {"item": "mermaid_hair", "chance": 0.04}},
    ],
    8: [
        {"name": "DEATH KNIGHT", "emoji": "⚰️", "hp": 2000, "atk": 110, "def": 60, "xp": 350, "coins": 250},
        {"name": "BANSHEE", "emoji": "😱", "hp": 1500, "atk": 130, "def": 35, "xp": 330, "coins": 240},
        {"name": "MERMAID", "emoji": "🧜‍♀️", "hp": 1600, "atk": 120, "def": 50, "xp": 340, "coins": 245,
         "drop": {"item": "mermaid_hair", "chance": 0.04}},
    ],
    9: [
        {"name": "OBSIDIAN GOLEM", "emoji": "⬛", "hp": 2800, "atk": 140, "def": 80, "xp": 420, "coins": 300},
        {"name": "VOID WALKER", "emoji": "🌀", "hp": 2500, "atk": 150, "def": 65, "xp": 440, "coins": 310},
        {"name": "KILLER ROBOT", "emoji": "🤖", "hp": 2600, "atk": 145, "def": 75, "xp": 430, "coins": 305,
         "drop": {"item": "chip", "chance": 0.04}},
    ],
    10: [
        {"name": "CHRONO SCOUT", "emoji": "⏳", "hp": 3200, "atk": 170, "def": 85, "xp": 500, "coins": 350},
        {"name": "PARADOX DRAGON", "emoji": "💫", "hp": 3500, "atk": 180, "def": 75, "xp": 520, "coins": 360},
        {"name": "KILLER ROBOT", "emoji": "🤖", "hp": 3000, "atk": 165, "def": 80, "xp": 480, "coins": 340,
         "drop": {"item": "chip", "chance": 0.04}},
    ],
    11: [
        {"name": "VOID LORD", "emoji": "🕳️", "hp": 4000, "atk": 200, "def": 100, "xp": 600, "coins": 400},
        {"name": "SCALED DRAGONS", "emoji": "🐉", "hp": 4200, "atk": 210, "def": 95, "xp": 620, "coins": 410,
         "drop": {"item": "dragonscale", "chance": 0.04}},
    ],
    12: [
        {"name": "CELESTIAL GUARD", "emoji": "👼", "hp": 5000, "atk": 250, "def": 120, "xp": 750, "coins": 500},
        {"name": "SCALED DRAGONS", "emoji": "🐉", "hp": 4800, "atk": 240, "def": 110, "xp": 700, "coins": 470,
         "drop": {"item": "dragonscale", "chance": 0.04}},
    ],
    13: [
        {"name": "DIVINE SERPENT", "emoji": "🐍", "hp": 6000, "atk": 300, "def": 150, "xp": 900, "coins": 600},
        {"name": "SCALED DRAGONS", "emoji": "🐉", "hp": 5500, "atk": 280, "def": 135, "xp": 830, "coins": 550,
         "drop": {"item": "dragonscale", "chance": 0.04}},
    ],
    14: [
        {"name": "TIME KEEPER", "emoji": "🕰️", "hp": 8000, "atk": 350, "def": 180, "xp": 1100, "coins": 750},
        {"name": "SCALED DRAGONS", "emoji": "🐉", "hp": 7200, "atk": 330, "def": 165, "xp": 1000, "coins": 700,
         "drop": {"item": "dragonscale", "chance": 0.04}},
    ],
    15: [
        {"name": "GOD OF TIME", "emoji": "🌌", "hp": 10000, "atk": 400, "def": 200, "xp": 1500, "coins": 1000},
        {"name": "SCALED DRAGONS", "emoji": "🐉", "hp": 9000, "atk": 380, "def": 190, "xp": 1350, "coins": 900,
         "drop": {"item": "dragonscale", "chance": 0.04}},
    ],
}

# --- Gambling ---
GAMBLING_MIN_BET = 10
GAMBLING_MAX_BET = 100000

# --- Daily/Weekly rewards ---
DAILY_REWARD_BASE = 100
# Wiki weekly reward table: area -> (coins, lootbox_type)
WEEKLY_REWARD_TABLE = {
    1:  (750, "common_lootbox"),
    2:  (6000, "common_lootbox"),
    3:  (20250, "uncommon_lootbox"),
    4:  (48000, "uncommon_lootbox"),
    5:  (93750, "rare_lootbox"),
    6:  (162000, "rare_lootbox"),
    7:  (257250, "epic_lootbox"),
    8:  (384000, "epic_lootbox"),
    9:  (546750, "edgy_lootbox"),
    10: (750000, "edgy_lootbox"),
    11: (998250, "edgy_lootbox"),
    12: (1296000, "edgy_lootbox"),
    13: (1647750, "edgy_lootbox"),
    14: (2058000, "edgy_lootbox"),
    15: (2531250, "edgy_lootbox"),
    16: (10444800, "edgy_lootbox"),  # TOP
}
WEEKLY_TIME_COOKIES = (1, 3)  # random 1-3 time cookies
WEEKLY_FLASKS = 2
WEEKLY_COOLDOWN = 604800  # 7 days in seconds
# Wiki: daily coins and life potions by max_area (coins affected by horse tier)
DAILY_BY_AREA = {
    1:  (2, 175),       # life_potions, coins
    2:  (4, 1400),
    3:  (6, 4725),
    4:  (8, 11200),
    5:  (10, 21875),
    6:  (12, 37800),
    7:  (14, 60025),
    8:  (16, 89600),
    9:  (18, 127575),
    10: (20, 175000),
    11: (22, 232925),
    12: (24, 302400),
    13: (26, 384475),
    14: (28, 480200),
    15: (30, 590625),
}
DAILY_COOLDOWN = 85800  # 23h 50m in seconds
DAILY_STREAK_BONUS = 7  # streak >= 7: epic coin + flask

# --- Arena ---
ARENA_REWARD_BASE = 500

# --- Vote rewards (wiki) ---
VOTE_COOLDOWN = 43200  # 12 hours
VOTE_STREAK_MAX = 7
# Wiki: coins scale with level and streak
VOTE_COINS_BASE = 250
VOTE_COINS_PER_TT = 50
VOTE_COINS_STREAK_MULT = 0.25  # +25% per streak level
# Wiki: lootbox by streak
VOTE_LOOTBOX_TABLE = {
    0: "rare_lootbox",
    1: "epic_lootbox",
    # 2-7: edgy_lootbox
}
VOTE_STREAK_7_COOKIES = 25  # arena cookies at streak 7
VOTE_STREAK_7_FLASKS = 1
VOTE_STREAK_7_EPIC_COIN = 1

# --- Horse ---
HORSE_TYPES = {
    "normal": {"speed": 10, "strength": 10, "endurance": 10, "cost": 0},
    "fast": {"speed": 20, "strength": 8, "endurance": 12, "cost": 5000},
    "strong": {"speed": 8, "strength": 20, "endurance": 12, "cost": 5000},
    "epic": {"speed": 15, "strength": 15, "endurance": 15, "cost": 10000},
}

# --- Title thresholds ---
TITLES = {
    "coolness_10": {"name": "Novice", "req": "coolness", "value": 10},
    "coolness_50": {"name": "Adventurer", "req": "coolness", "value": 50},
    "coolness_200": {"name": "Veteran", "req": "coolness", "value": 200},
    "coolness_500": {"name": "Legendary", "req": "coolness", "value": 500},
    "level_10": {"name": "Warrior", "req": "level", "value": 10},
    "level_30": {"name": "Champion", "req": "level", "value": 30},
    "level_50": {"name": "Hero", "req": "level", "value": 50},
    "level_100": {"name": "Ascended", "req": "level", "value": 100},
    "area_5": {"name": "Explorer", "req": "area", "value": 5},
    "area_10": {"name": "Pathfinder", "req": "area", "value": 10},
    "area_15": {"name": "Voidwalker", "req": "area", "value": 15},
    "tt_1": {"name": "Time Traveler", "req": "tt", "value": 1},
    "tt_5": {"name": "Chrono Master", "req": "tt", "value": 5},
    "tt_10": {"name": "Eternal", "req": "tt", "value": 10},
}

# --- Achievement definitions ---
ACHIEVEMENTS = {
    "first_hunt": {"name": "First Blood", "desc": "Убить первого моба", "emoji": "⚔️"},
    "hunt_100": {"name": "Monster Slayer", "desc": "Убить 100 мобов", "emoji": "🗡️"},
    "hunt_500": {"name": "Legendary Slayer", "desc": "Убить 500 мобов", "emoji": "💀"},
    "dungeon_10": {"name": "Dungeon Master", "desc": "Пройти 10 подземелий", "emoji": "🏰"},
    "coins_100k": {"name": "Rich", "desc": "Накопить 100,000 монет", "emoji": "💰"},
    "coins_1m": {"name": "Millionaire", "desc": "Накопить 1,000,000 монет", "emoji": "💎"},
    "level_50": {"name": "Half Century", "desc": "Достичь уровня 50", "emoji": "⭐"},
    "level_100": {"name": "Century", "desc": "Достичь уровня 100", "emoji": "🌟"},
    "area_5": {"name": "Dragon Hunter", "desc": "Добраться до Area 5", "emoji": "🐉"},
    "area_10": {"name": "Time Walker", "desc": "Добраться до Area 10", "emoji": "⏳"},
    "area_15": {"name": "Void Master", "desc": "Добраться до Area 15", "emoji": "🌌"},
    "tt_1": {"name": "First Reset", "desc": "Сделать первый Time Travel", "emoji": "🔄"},
    "tt_5": {"name": "Time Lord", "desc": "Сделать 5 Time Travel", "emoji": "⏰"},
    "craft_5": {"name": "Blacksmith", "desc": "Скрафтить 5 предметов", "emoji": "⚒️"},
    "pet_5": {"name": "Beast Tamer", "desc": "Поймать 5 питомцев", "emoji": "🐾"},
    "guild_create": {"name": "Guild Leader", "desc": "Создать гильдию", "emoji": "🏰"},
    "lottery_win": {"name": "Lucky One", "desc": "Выиграть в лотерее", "emoji": "🎰"},
    "blackjack_10": {"name": "Card Shark", "desc": "Выиграть 10 рук блэкджека", "emoji": "🃏"},
    "slots_10": {"name": "Slot Master", "desc": "Выиграть 10 раз на слотах", "emoji": "🎰"},
}

# --- Shop items ---
LOOTBOX_PRICES = {
    "common_lootbox": 800,
    "uncommon_lootbox": 6000,
    "rare_lootbox": 40000,
    "epic_lootbox": 150000,
    "edgy_lootbox": 420666,
}

# --- Transmutation ---
TRANSMUTE_RATE = 5

# --- Enchant ---
ENCHANT_COST_COINS = 500
ENCHANT_DURATION = 300  # seconds
ENCHANT_BONUS_MULT = 0.25

# --- Training ---
TRAINING_COOLDOWN = 900  # 15 min in seconds
# Wiki: XP ~100-200 in Area 2, +300-500 per area
TRAINING_XP_BASE = 100
TRAINING_XP_PER_AREA = 400  # rough average of 300-500 per area
# Pet spawn: 4% base, 10% tier IX, 20% tier X horse
TRAINING_PET_CHANCE_BASE = 0.04
TRAINING_PET_CHANCE_TIER9 = 0.10
TRAINING_PET_CHANCE_TIER10 = 0.20

# --- Ultraining (Area 12+) ---
ULTRAINING_COOLDOWN = 900  # 15 min
ULTRAINING_COOLNESS = 2
ULTRAINING_DOUBLE_COOLNESS = 4
ULTRAINING_DOUBLE_CHANCE = 0.25  # 25% chance for double stage

# --- Farm ---
FARM_COST_COINS = 1000
FARM_DURATION = 3600  # 1 hour
FARM_WOOD_PER_HOUR = 50
FARM_STONE_PER_HOUR = 30

# --- Greenhouse ---
GREENHOUSE_COST = 2000
GREENHOUSE_DURATION = 7200  # 2 hours
GREENHOUSE_YIELD = {
    "wooden_log": 30, "epic_log": 15, "super_log": 5,
    "apple": 20, "potato": 10,
}

# --- Cook (real Epic RPG) ---
# Stat buff recipes (permanent until TT)
COOK_RECIPES = {
    "baked_fish": {"materials": {"golden_fish": 12, "epic_fish": 1, "epic_log": 12}, "buff": "+5 к макс. HP", "area": 5,
                   "coins_mult": 0, "fish_mult": 10, "logs_mult": 0},
    "hairn": {"materials": {"unicornhorn": 1, "mermaid_hair": 2}, "buff": "+1 DEF, +1 ATK", "area": 5,
              "coins_mult": 10, "fish_mult": 10, "logs_mult": 10},
    "fruit_salad": {"materials": {"apple": 25, "banana": 6}, "buff": "+1 к макс. HP", "area": 5,
                    "coins_mult": 0, "fish_mult": 10, "logs_mult": 10},
    "apple_juice": {"materials": {"apple": 8, "hyper_log": 1}, "buff": "+2 DEF, +2 ATK", "area": 5,
                    "coins_mult": 0, "fish_mult": 10, "logs_mult": 10},
    "carrot_bread": {"materials": {"bread": 1, "carrot": 160}, "buff": "+1 уровень", "area": 5,
                     "coins_mult": 0, "fish_mult": 10, "logs_mult": 10},
    "orange_juice": {"materials": {"carrot": 320}, "buff": "+3 DEF, +3 ATK", "area": 5,
                     "coins_mult": 10, "fish_mult": 10, "logs_mult": 10},
    "super_cookie": {"materials": {"arenacookie": 1000}, "buff": "+10 уровней", "area": 5,
                     "coins_mult": 10, "fish_mult": 10, "logs_mult": 10},
    # Coin/loot multiplier recipes
    "cooked_potato": {"materials": {"potato": 10}, "buff": "+2 coins per command", "area": 5,
                      "flat_coins": 2},
    "cooked_watermelon": {"materials": {"Watermelon": 3}, "buff": "+150 coins per command", "area": 5,
                          "flat_coins": 150},
    "pumpkin": {"materials": {"potato": 50, "carrot": 50}, "buff": "+10% coins", "area": 5,
                "coins_mult": 10},
    "bread_cooked": {"materials": {"bread": 3}, "buff": "+10% fish, +10% logs", "area": 5,
                     "fish_mult": 10, "logs_mult": 10},
    "epic_bread": {"materials": {"bread": 5, "epic_log": 3}, "buff": "+10% coins, +10% fish, +10% logs", "area": 5,
                   "coins_mult": 10, "fish_mult": 10, "logs_mult": 10},
    "monster_cookies": {"materials": {"arenacookie": 50, "wolfskin": 3, "zombieeye": 3}, "buff": "+50% coins, +50% fish, +50% logs", "area": 5,
                        "coins_mult": 50, "fish_mult": 50, "logs_mult": 50},
    "chocolate_donuts": {"materials": {"arenacookie": 200, "banana": 20}, "buff": "+200% coins, +200% fish, +200% logs", "area": 5,
                         "coins_mult": 200, "fish_mult": 200, "logs_mult": 200},
    "fruit_cake": {"materials": {"apple": 100, "banana": 50, "bread": 10}, "buff": "+500% coins, +500% fish, +500% logs", "area": 5,
                   "coins_mult": 500, "fish_mult": 500, "logs_mult": 500},
    "christmas_cake": {"materials": {"bread": 20, "apple": 200, "banana": 100, "carrot": 500}, "buff": "+1000% coins, +1000% fish, +1000% logs", "area": 5,
                       "coins_mult": 1000, "fish_mult": 1000, "logs_mult": 1000},
}
COOK_COST_COINS = 500  # 500 coins per cook

# --- Refine ---
REFINE_COST = 5  # 5 lower tier -> 1 higher tier
REFINE_TYPES = [
    ("wooden_log", "epic_log"),
    ("epic_log", "super_log"),
    ("super_log", "mega_log"),
    ("mega_log", "hyper_log"),
    ("hyper_log", "ultra_log"),
    ("ultra_log", "ultimate_log"),
    ("normie_fish", "golden_fish"),
    ("golden_fish", "epic_fish"),
    ("epic_fish", "super_fish"),
    ("super_fish", "mega_fish"),
    ("mega_fish", "hyper_fish"),
    ("apple", "banana"),
]

# --- Forge ---
FORGE_COST = {"ruby": 20, "hyper_log": 10}
FORGE_REWARD = {"artifact_core": 1}

# --- Timetravel rules (wiki-accurate) ---
# Resets: level, xp, area, equipment, materials, cooldowns, cook boosts
# Keeps: coins/bank/epic_coins, horse, pets, professions, arena cookies,
#        dragonessence, timedragonessence, active title, epic shop items
# Quadratic formulas: XP=(99+x)*x/2, Drops=(49+x)*x/2, Items=(49+x)*x/2

# --- Dungeon 10-15 (late game) ---
DUNGEONS_LATE = {
    10: {
        "name": "EDGY Dragon",
        "players": 2,
        "time_limit": 12,
        "requirements": {
            "gear": "edgy",
            "dungeon_key": True,
            "horse_tier": 6,
        },
        "boss_name": "EDGY Dragon",
        "boss_emoji": "🐉",
        "boss_hp": 10,
        "boss_atk": 10,
        "boss_def": 0,
        "time_limit_min": 12,
        "commands": {
            "bite":    {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":    {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":   {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
        },
        "reward_min": 300000,
        "reward_max": 500000,
        "description": "Стратегическое подземелье на 2 игроков. Заряжай Edgy снаряжение!",
    },
    11: {
        "name": "ULTRA-EDGY Dragon",
        "players": 1,
        "time_limit": 12,
        "requirements": {
            "time_travel": 1,
            "gear": "ultra_edgy",
            "dungeon_key": True,
            "horse_tier": 6,
        },
        "boss_name": "ULTRA-EDGY Dragon",
        "boss_emoji": "🐉",
        "boss_hp": 1000,
        "boss_atk": 200,
        "boss_def": 50,
        "time_limit_min": 12,
        "commands": {
            "bite":    {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":    {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":   {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
            "dodge":   {"chance": 0.5,  "type": "counter", "counter_multiplier": 1.5},
        },
        "reward_min": 400000,
        "reward_max": 600000,
        "description": "Соло данжон. Механика: движение, HP и удача.",
    },
    12: {
        "name": "OMEGA Dragon",
        "players": 1,
        "time_limit": 16,
        "requirements": {
            "time_travel": 3,
            "gear": "ultra_edgy",
            "dungeon_key": True,
            "horse_tier": 6,
        },
        "boss_name": "OMEGA Dragon",
        "boss_emoji": "🐉",
        "boss_hp": 2000,
        "boss_atk": 300,
        "boss_def": 80,
        "time_limit_min": 16,
        "commands": {
            "bite":    {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":    {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":   {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
            "dodge":   {"chance": 0.5,  "type": "counter", "counter_multiplier": 1.5},
            "collect orb": {"chance": 0.6, "type": "special", "effect": "orb"},
        },
        "reward_min": 500000,
        "reward_max": 800000,
        "description": "Собери 10 орбов чтобы ослабить дракона!",
    },
    13: {
        "name": "ULTRA-OMEGA Dragon",
        "players": 1,
        "time_limit": 18,
        "requirements": {
            "time_travel": 5,
            "gear": "omega",
            "dungeon_key": True,
            "horse_tier": 6,
        },
        "boss_name": "ULTRA-OMEGA Dragon",
        "boss_emoji": "🐉",
        "boss_hp": 5000,
        "boss_atk": 400,
        "boss_def": 100,
        "time_limit_min": 18,
        "commands": {
            "bite":    {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":    {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":   {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
            "dodge":   {"chance": 0.5,  "type": "counter", "counter_multiplier": 1.5},
            "solve puzzle": {"chance": 0.7, "type": "special", "effect": "puzzle"},
        },
        "reward_min": 700000,
        "reward_max": 1200000,
        "description": "Головоломка + trivia по Epic RPG!",
    },
    14: {
        "name": "GODLY Dragon",
        "players": 1,
        "time_limit": 16,
        "requirements": {
            "time_travel": 10,
            "gear": "omega",
            "dungeon_key": True,
            "horse_tier": 6,
        },
        "boss_name": "GODLY Dragon",
        "boss_emoji": "🐉",
        "boss_hp": 8000,
        "boss_atk": 500,
        "boss_def": 120,
        "time_limit_min": 16,
        "commands": {
            "bite":    {"chance": 1.0,  "type": "attack", "multiplier": 1.2},
            "stab":    {"chance": 0.7,  "type": "attack", "multiplier": 2.0},
            "power":   {"chance": 0.4,  "type": "attack", "multiplier": 4.0},
            "dodge":   {"chance": 0.5,  "type": "counter", "counter_multiplier": 1.5},
        },
        "reward_min": 1000000,
        "reward_max": 2000000,
        "description": "Механика: движение. Два дракона подряд!",
    },
    15: {
        "name": "Dungeon of the End",
        "players": 30,
        "time_limit": 0,  # no time limit
        "requirements": {},
        "boss_name": "TIME Dragon",
        "boss_emoji": "🐉",
        "boss_hp": 0,  # wave-based, see D15_WAVES
        "boss_atk": 0,
        "boss_def": 0,
        "reward_min": 100,
        "reward_max": 300,
        "commands": {
            "attack": {"chance": 1.0, "type": "attack", "multiplier": 1.0},
        },
        "description": "Финальное подземелье! 10 волн + босс. 30 игроков. Фиксированный урон.",
        "wave_based": True,
    },
}

# D15: Dungeon of the End — wave data
# Per wiki: 10 waves, then boss. Each player deals exactly 10 damage per round.
# Boss heals 100 HP per round. 30 players. No time limit.
D15_WAVES = [
    # (name, emoji, HP, base_ATK)  — ATK = 200 + wave*20
    ("Wisp",            "👻", 2000,   220),
    ("Wisp",            "👻", 2000,   240),
    ("Goblin Warrior",  "👺", 3000,   260),
    ("Ogre",            "👹", 4000,   280),
    ("Werewolf",        "🐺", 4000,   300),
    ("Dark Elf",        "🧝", 5000,   320),
    ("Troll",           "🧌", 5000,   340),
    ("Cyclops",         "👁️", 5000,  360),
    ("Spectre",         "💀", 5000,   380),
    ("Golem",           "🗿", 5000,   400),
]
D15_BOSS = {
    "name": "Time Dragon",
    "emoji": "🐉",
    "hp": 30000,
    "atk": 400,
    "heal_per_round": 100,
}
# Rewards: 100-300 arena tokens + random EPIC item
D15_REWARDS = {
    "arena_tokens_min": 100,
    "arena_tokens_max": 300,
    "epic_items": [
        ("unicornhorn", 5, 10),
        ("mermaid_hair", 3, 6),
        ("ruby", 2, 5),
        ("chip", 1, 3),
        ("dragonscale", 1, 3),
    ],
}

# Dungeon gear tiers
DUNGEON_GEAR_TIERS = {
    "edgy": {"weapon_min": 50, "armor_min": 50, "name": "EDGY"},
    "ultra_edgy": {"weapon_min": 50, "armor_min": 50, "tt_min": 1, "name": "ULTRA-EDGY"},
    "omega": {"weapon_min": 50, "armor_min": 50, "tt_min": 3, "name": "OMEGA"},
    "ultra_omega": {"weapon_min": 50, "armor_min": 50, "tt_min": 5, "name": "ULTRA-OMEGA"},
    "godly": {"weapon_min": 50, "armor_min": 50, "tt_min": 10, "name": "GODLY"},
}

# --- Event chance ---
EVENT_CHANCE = 0.05
EVENT_WINDOW = 60
EVENT_MIN_PLAYERS = 3

# --- Pet bait ---
PET_BAIT_SECONDS = 7200

# --- Guild ---
GUILD_CREATE_COST = 500000
GUILD_MAX_MEMBERS = 10

# --- EPIC NPC Trade Rates (wooden_log ⇄ other items) ---
# Format: {area: {give: {"wooden_log": X}, receive: {"item": 1}}}
NPC_TRADE_RATES = {
    1:  {"fish": 1, "apple": 0, "ruby": 0},    # 1:1 fish
    2:  {"fish": 1, "apple": 0, "ruby": 0},    # 1:1 fish
    3:  {"fish": 1, "apple": 3, "ruby": 0},     # 1:1 fish, 3:1 apple
    4:  {"fish": 2, "apple": 4, "ruby": 0},     # 2:1 fish, 4:1 apple
    5:  {"fish": 2, "apple": 4, "ruby": 450},   # 2:1 fish, 4:1 apple, 450:1 ruby
    6:  {"fish": 3, "apple": 15, "ruby": 675},
    7:  {"fish": 3, "apple": 15, "ruby": 675},
    8:  {"fish": 3, "apple": 8, "ruby": 675},
    9:  {"fish": 2, "apple": 12, "ruby": 850},
    10: {"fish": 3, "apple": 12, "ruby": 500},
    11: {"fish": 3, "apple": 8, "ruby": 500},
    12: {"fish": 3, "apple": 8, "ruby": 350},
    13: {"fish": 3, "apple": 8, "ruby": 350},
    14: {"fish": 3, "apple": 8, "ruby": 350},
    15: {"fish": 3, "apple": 8, "ruby": 350},
    16: {"fish": 2, "apple": 4, "ruby": 250},
    17: {"fish": 2, "apple": 4, "ruby": 250},
    18: {"fish": 2, "apple": 4, "ruby": 250},
    19: {"fish": 2, "apple": 4, "ruby": 250},
    20: {"fish": 2, "apple": 4, "ruby": 250},
}

# --- Trade Rates (wiki-accurate, max_area-based) ---
# Each bracket maps to a list of trade options with ID, give/receive items and amounts
TRADE_RATES = {
    # Area 1-2
    1: [
        {"id": "A", "give": ("normie_fish", 1), "receive": ("wooden_log", 1)},
        {"id": "B", "give": ("wooden_log", 1), "receive": ("normie_fish", 1)},
    ],
    # Area 3
    3: [
        {"id": "A", "give": ("normie_fish", 1), "receive": ("wooden_log", 1)},
        {"id": "B", "give": ("wooden_log", 1), "receive": ("normie_fish", 1)},
        {"id": "C", "give": ("apple", 1), "receive": ("wooden_log", 3)},
        {"id": "D", "give": ("wooden_log", 3), "receive": ("apple", 1)},
    ],
    # Area 4-5
    4: [
        {"id": "A", "give": ("normie_fish", 1), "receive": ("wooden_log", 2)},
        {"id": "B", "give": ("wooden_log", 2), "receive": ("normie_fish", 1)},
        {"id": "C", "give": ("apple", 1), "receive": ("wooden_log", 4)},
        {"id": "D", "give": ("wooden_log", 4), "receive": ("apple", 1)},
        {"id": "E", "give": ("ruby", 1), "receive": ("wooden_log", 450)},
        {"id": "F", "give": ("wooden_log", 450), "receive": ("ruby", 1)},
    ],
    # Area 6-7
    6: [
        {"id": "A", "give": ("normie_fish", 1), "receive": ("wooden_log", 3)},
        {"id": "B", "give": ("wooden_log", 3), "receive": ("normie_fish", 1)},
        {"id": "C", "give": ("apple", 1), "receive": ("wooden_log", 15)},
        {"id": "D", "give": ("wooden_log", 15), "receive": ("apple", 1)},
        {"id": "E", "give": ("ruby", 1), "receive": ("wooden_log", 675)},
        {"id": "F", "give": ("wooden_log", 675), "receive": ("ruby", 1)},
    ],
    # Area 8
    8: [
        {"id": "A", "give": ("normie_fish", 1), "receive": ("wooden_log", 3)},
        {"id": "B", "give": ("wooden_log", 3), "receive": ("normie_fish", 1)},
        {"id": "C", "give": ("apple", 1), "receive": ("wooden_log", 8)},
        {"id": "D", "give": ("wooden_log", 8), "receive": ("apple", 1)},
        {"id": "E", "give": ("ruby", 1), "receive": ("wooden_log", 675)},
        {"id": "F", "give": ("wooden_log", 675), "receive": ("ruby", 1)},
    ],
    # Area 9
    9: [
        {"id": "A", "give": ("normie_fish", 1), "receive": ("wooden_log", 2)},
        {"id": "B", "give": ("wooden_log", 2), "receive": ("normie_fish", 1)},
        {"id": "C", "give": ("apple", 1), "receive": ("wooden_log", 12)},
        {"id": "D", "give": ("wooden_log", 12), "receive": ("apple", 1)},
        {"id": "E", "give": ("ruby", 1), "receive": ("wooden_log", 850)},
        {"id": "F", "give": ("wooden_log", 850), "receive": ("ruby", 1)},
    ],
    # Area 10
    10: [
        {"id": "A", "give": ("normie_fish", 1), "receive": ("wooden_log", 3)},
        {"id": "B", "give": ("wooden_log", 3), "receive": ("normie_fish", 1)},
        {"id": "C", "give": ("apple", 1), "receive": ("wooden_log", 12)},
        {"id": "D", "give": ("wooden_log", 12), "receive": ("apple", 1)},
        {"id": "E", "give": ("ruby", 1), "receive": ("wooden_log", 500)},
        {"id": "F", "give": ("wooden_log", 500), "receive": ("ruby", 1)},
    ],
    # Area 11
    11: [
        {"id": "A", "give": ("normie_fish", 1), "receive": ("wooden_log", 3)},
        {"id": "B", "give": ("wooden_log", 3), "receive": ("normie_fish", 1)},
        {"id": "C", "give": ("apple", 1), "receive": ("wooden_log", 8)},
        {"id": "D", "give": ("wooden_log", 8), "receive": ("apple", 1)},
        {"id": "E", "give": ("ruby", 1), "receive": ("wooden_log", 500)},
        {"id": "F", "give": ("wooden_log", 500), "receive": ("ruby", 1)},
    ],
    # Area 12-15
    12: [
        {"id": "A", "give": ("normie_fish", 1), "receive": ("wooden_log", 3)},
        {"id": "B", "give": ("wooden_log", 3), "receive": ("normie_fish", 1)},
        {"id": "C", "give": ("apple", 1), "receive": ("wooden_log", 8)},
        {"id": "D", "give": ("wooden_log", 8), "receive": ("apple", 1)},
        {"id": "E", "give": ("ruby", 1), "receive": ("wooden_log", 350)},
        {"id": "F", "give": ("wooden_log", 350), "receive": ("ruby", 1)},
    ],
    # The TOP (area 16+)
    16: [
        {"id": "A", "give": ("normie_fish", 1), "receive": ("wooden_log", 2)},
        {"id": "B", "give": ("wooden_log", 2), "receive": ("normie_fish", 1)},
        {"id": "C", "give": ("apple", 1), "receive": ("wooden_log", 4)},
        {"id": "D", "give": ("wooden_log", 4), "receive": ("apple", 1)},
        {"id": "E", "give": ("ruby", 1), "receive": ("wooden_log", 250)},
        {"id": "F", "give": ("wooden_log", 250), "receive": ("ruby", 1)},
    ],
}

# --- Returning Event ---
RETURNING_DAYS = 7           # days inactive to trigger event
RETURNING_DURATION = 7       # event lasts 7 days
RETURNING_CD_REDUCTION = 0.33  # 33% cooldown reduction
RETURNING_DROP_MULTIPLIER = 2  # 2x monster drop chance
RETURNING_SMOL_PER_ACTION = (1, 3)  # smol coins per hunt/work/adventure

# Super Daily rewards: day 0-6 -> list of (item_id, amount)
RETURNING_SUPER_DAILY = {
    0: [("omega_lootbox", 1)],
    1: [("edgy_lootbox", 5)],
    2: [("magic_bed", 1)],
    3: [("omega_horse_token", 3)],
    4: [("arenacookie", 250)],
    5: [("edgy_lootbox", 5)],
    6: [("omega_horse_token", 5)],
}

# Returning shop: item_id -> (cost_smol, limit_per_player, display_name)
RETURNING_SHOP = {
    "edgy_lootbox":     (5, 20, "📦 Edgy Lootbox"),
    "arenacookie":      (15, 10, "🍪 Arena Cookie (40)"),
    "dungeon_reset":    (40, 5, "🔑 Dungeon Reset"),
    "random_epic_item": (75, 3, "🎲 Random EPIC Item"),
    "coins":            (1, -1, "🪙 1000 Coins"),  # -1 = unlimited
}

# Quest reward: OMEGA lootbox + 10 arena tokens + 250 arenacookie + 25 epic_coins + 200 smol
RETURNING_QUEST_REWARD = {
    "items": [("omega_lootbox", 1), ("arenacookie", 250), ("smol_coin", 200)],
    "epic_coins": 25,
    "arena_tokens": 10,  # placeholder — not a real material in wiki
}

# --- Quest system (wiki-accurate) ---
QUEST_COOLDOWN = 21600        # 6 hours between quests
QUEST_DECLINE_COOLDOWN = 3600 # 1 hour after declining
QUEST_TYPES_BY_AREA = {
    1: ["hunt", "adventure", "craft", "gambling", "arena", "miniboss", "trading"],
    4: ["guild"],    # unlocked at area 4+
    5: ["cooking"],  # unlocked at area 5+
}

# Quest type -> (target_base, coin_reward_mult, xp_reward_mult, extra_item, extra_item_base_amount)
QUEST_DEFS = {
    "hunt":      {"target": 3,  "coin_mult": 1.0, "xp_mult": 1.0, "item": "uncommon_lootbox", "item_base": 1},
    "adventure": {"target": 1,  "coin_mult": 0.8, "xp_mult": 0.8, "item": "wooden_log",       "item_base": 3},
    "craft":     {"target": 1,  "coin_mult": 0.7, "xp_mult": 0.7, "item": "normie_fish",      "item_base": 2},
    "gambling":  {"target": 500, "coin_mult": 1.5, "xp_mult": 1.0, "item": "epic_lootbox",    "item_base": 1},
    "arena":     {"target": 1,  "coin_mult": 0.6, "xp_mult": 0.8, "item": "arenacookie",      "item_base": 2},
    "miniboss":  {"target": 1,  "coin_mult": 1.2, "xp_mult": 1.2, "item": "epic_log",         "item_base": 2},
    "cooking":   {"target": 3,  "coin_mult": 0.6, "xp_mult": 1.5, "item": "banana",           "item_base": 3},
    "guild":     {"target": 1,  "coin_mult": 1.0, "xp_mult": 1.0, "item": "heart",            "item_base": 1},
    "trading":   {"target": 1,  "coin_mult": 0.8, "xp_mult": 0.8, "item": "golden_fish",      "item_base": 1},
}
