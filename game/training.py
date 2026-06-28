"""
Training system — wiki-accurate 6 training types.
Each training presents a mini-game puzzle. Success = XP + chance at pet spawn.
"""
import random
import config
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# --- Training puzzle generators ---

def gen_forest_puzzle() -> dict:
    """Forest Training: show 5 logs, ask how many are a certain type."""
    log_types = ["🪵 wooden", "🪵 epic", "🪵 super"]
    chosen_type = random.choice(log_types)
    logs = []
    for _ in range(5):
        roll = random.random()
        if roll < 0.4:
            logs.append("🪵 wooden")
        elif roll < 0.7:
            logs.append("🪵 epic")
        else:
            logs.append("🪵 super")

    # Count of chosen type in the logs
    correct_answer = sum(1 for l in logs if l == chosen_type)

    display = " ".join(logs)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"train:{i}") for i in range(3)],
        [InlineKeyboardButton(text=str(i), callback_data=f"train:{i}") for i in range(3, 6)],
    ])

    return {
        "type": "forest",
        "message": (
            f"🌲 <b>Forest Training</b>\n\n"
            f"Логи: {display}\n\n"
            f"Сколько логов типа <b>{chosen_type}</b>?"
        ),
        "answer": str(correct_answer),
        "keyboard": keyboard,
    }


def gen_river_puzzle() -> dict:
    """River Training: show a fish, answer 1/2/3."""
    fish = random.choice([
        ("🐟", "Normie Fish", "1"),
        ("🐟", "Golden Fish", "2"),
        ("🐟", "EPIC Fish", "3"),
    ])
    emoji, name, correct = fish

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 - Normie", callback_data="train:1"),
            InlineKeyboardButton(text="2 - Golden", callback_data="train:2"),
            InlineKeyboardButton(text="3 - EPIC", callback_data="train:3"),
        ],
    ])

    return {
        "type": "river",
        "message": (
            f"🌊 <b>River Training</b>\n\n"
            f"Вы видите: {emoji} <b>{name}</b>\n\n"
            f"Введите номер: 1 (Normie), 2 (Golden), 3 (EPIC)"
        ),
        "answer": correct,
        "keyboard": keyboard,
    }


def gen_field_puzzle() -> dict:
    """Field Training: ask what letter is Nth of Banana or Apple."""
    words = [("Banana", "B"), ("Apple", "A")]
    word, first_letter = random.choice(words)
    position = random.randint(1, 6)

    if word == "Banana":
        letters = list("Banana")
    else:
        letters = list("Apple")

    if position <= len(letters):
        correct = letters[position - 1].upper()
    else:
        correct = "N/A"

    return {
        "type": "field",
        "message": (
            f"🌾 <b>Field Training</b>\n\n"
            f"Какая буква <b>{position}</b>-я в слове <b>{word}</b>?\n\n"
            f"Ответьте следующим сообщением."
        ),
        "answer": correct,
        "keyboard": None,  # uses next message
    }


def gen_casino_puzzle() -> dict:
    """Casino Training: match picture + word. Yes/No."""
    items = [
        ("🍎", "Apple", True),
        ("🐟", "Fish", True),
        ("💎", "Ruby", True),
        ("🍎", "Fish", False),
        ("🐟", "Apple", False),
        ("💎", "Apple", False),
        ("🍎", "Ruby", False),
        ("🐟", "Ruby", False),
        ("💎", "Fish", False),
    ]
    emoji, word, matches = random.choice(items)
    correct = "yes" if matches else "no"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Yes", callback_data="train:yes"),
            InlineKeyboardButton(text="No", callback_data="train:no"),
        ],
    ])

    return {
        "type": "casino",
        "message": (
            f"🎰 <b>Casino Training</b>\n\n"
            f"Картинка: {emoji}\n"
            f"Слово: <b>{word}</b>\n\n"
            f"Они совпадают?"
        ),
        "answer": correct,
        "keyboard": keyboard,
    }


def gen_void_puzzle(max_area: int) -> dict:
    """Void Training: ask how many days left for area to get sealed."""
    # Wiki: days left for the area the player is currently sitting on
    # Simulated: random answer 1-30
    correct = random.randint(1, 30)

    return {
        "type": "void",
        "message": (
            f"🕳️ <b>Void Training</b>\n\n"
            f"Сколько дней осталось до密封 Area {max_area}?\n\n"
            f"Ответ: число от 1 до 30"
        ),
        "answer": str(correct),
        "keyboard": None,  # uses next message
    }


def gen_mine_puzzle(ruby_count: int) -> dict:
    """Mine Training (Area 5+): ask if player has at least X rubies.
    X is ±5 from actual, never equal."""
    offset = random.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5])
    asked = max(0, ruby_count + offset)
    # Correct answer: "yes" if ruby_count >= asked
    correct = "yes" if ruby_count >= asked else "no"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Yes", callback_data="train:yes"),
            InlineKeyboardButton(text="No", callback_data="train:no"),
        ],
    ])

    return {
        "type": "mine",
        "message": (
            f"⛏️ <b>Mine Training</b>\n\n"
            f"У вас есть хотя бы <b>{asked}</b> рубинов?\n\n"
            f"Ответьте Yes или No."
        ),
        "answer": correct,
        "keyboard": keyboard,
    }


def generate_training(max_area: int, ruby_count: int = 0) -> dict:
    """Generate a random training puzzle based on area."""
    # Pool of available training types based on area
    types = ["forest", "river", "field", "casino", "void"]
    if max_area >= 5:
        types.append("mine")

    chosen = random.choice(types)

    if chosen == "forest":
        return gen_forest_puzzle()
    elif chosen == "river":
        return gen_river_puzzle()
    elif chosen == "field":
        return gen_field_puzzle()
    elif chosen == "casino":
        return gen_casino_puzzle()
    elif chosen == "void":
        return gen_void_puzzle(max_area)
    elif chosen == "mine":
        return gen_mine_puzzle(ruby_count)
    else:
        return gen_forest_puzzle()


def calc_training_xp(max_area: int, tt_count: int) -> int:
    """Wiki: XP ~100-200 in Area 2, +300-500 per area. Affected by TT boost."""
    area_offset = max(0, max_area - 2)
    base = config.TRAINING_XP_BASE + area_offset * config.TRAINING_XP_PER_AREA
    # Add variance
    base = int(base * random.uniform(0.8, 1.2))
    # Apply TT boost
    from game.player import get_tt_xp_bonus
    tt_mult = 1 + get_tt_xp_bonus(tt_count)
    return int(base * tt_mult)


def get_pet_spawn_chance(tt_count: int, horse_tier: int) -> float:
    """Wiki: 4% base, 10% tier IX, 20% tier X. Requires TT2+."""
    if tt_count < 2:
        return 0.0
    if horse_tier >= 10:
        return config.TRAINING_PET_CHANCE_TIER10
    elif horse_tier >= 9:
        return config.TRAINING_PET_CHANCE_TIER9
    else:
        return config.TRAINING_PET_CHANCE_BASE
