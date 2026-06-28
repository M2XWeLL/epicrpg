"""
Gambling game logic — wiki-accurate.
Coinflip, Dice, Cups, Blackjack, Slots, Lottery, Wheel, Big Dice.
"""
import random
import config

# Global pot for Big Dice — never resets
BIG_DICE_POT = 0


def roll_dice(sides: int = 6) -> int:
    return random.randint(1, sides)


# --- Coinflip ---
# Wiki: 45% win (100% of bet), 54% fail (100% of bet lost),
#        1% side (500% of bet won), EXTREMELY low chance lose 1 coin

def coinflip(bet: int, choice: str) -> dict:
    roll = random.random()
    choice = choice.lower()

    if roll < 0.01:
        # 1% side — coin lands in next area, win 500%
        return {"won": True, "result": "side", "winnings": int(bet * 5), "side": True}
    elif roll < 0.46:
        # 45% — win 100% of bet
        # Real coinflip: if you picked correctly
        result = choice
        return {"won": True, "result": result, "winnings": bet, "side": False}
    else:
        # 54% — lose
        result = "tails" if choice == "heads" else "heads"
        return {"won": False, "result": result, "winnings": -bet, "side": False}


# --- Dice ---
# Wiki: Roll 1=lose all, 2=lose half, 3=lose quarter,
#        4=win quarter, 5=win half, 6=win all, 7=win 10x

def dice_game(bet: int, player_roll: int = None) -> dict:
    if player_roll is None:
        player_roll = roll_dice(6)
    # Special: very low chance of rolling 7
    if random.random() < 0.02:
        player_roll = 7

    if player_roll == 1:
        winnings = -bet
    elif player_roll == 2:
        winnings = -(bet // 2)
    elif player_roll == 3:
        winnings = -(bet // 4)
    elif player_roll == 4:
        winnings = bet // 4
    elif player_roll == 5:
        winnings = bet // 2
    elif player_roll == 6:
        winnings = bet
    elif player_roll == 7:
        winnings = bet * 10
    else:
        winnings = 0

    return {
        "won": winnings > 0,
        "player": player_roll,
        "bot": 0,
        "winnings": winnings,
    }


# --- Cups ---
# Wiki: 3 cups, correct = 175% of bet won, wrong = 100% lost

def cups_game(bet: int, choice: int) -> dict:
    cup = random.randint(1, 3)
    if choice == cup:
        return {"won": True, "cup": cup, "winnings": int(bet * 1.75)}
    return {"won": False, "cup": cup, "winnings": -bet}


# --- Blackjack ---
# Wiki: Natural 21 = instant win (2.5x), higher than bot wins (2x),
#        bust (>21) = loss, dealer may bust.
#        Special: 7 card charlie — 7 cards without busting = win

def blackjack(bet: int) -> dict:
    def card_value(hand):
        val = sum(c[0] for c in hand)
        aces = sum(1 for c in hand if c[1] == "A")
        while val > 21 and aces:
            val -= 10
            aces -= 1
        return val

    def card_name(card):
        val, suit = card
        names = {11: "A", 10: "10", 9: "9", 8: "8", 7: "7", 6: "6",
                 5: "5", 4: "4", 3: "3", 2: "2"}
        return f"{names.get(val, str(val))}"

    ranks = [(i, "suit") for i in range(2, 11) for _ in range(4)]
    ranks += [(10, "J")] * 4 + [(10, "Q")] * 4 + [(10, "K")] * 4 + [(11, "A")] * 4
    random.shuffle(ranks)

    player_hand = [ranks.pop(), ranks.pop()]
    dealer_hand = [ranks.pop(), ranks.pop()]

    player_val = card_value(player_hand)
    dealer_val = card_value(dealer_hand)

    # Natural blackjack
    if player_val == 21:
        return {"player": player_hand, "dealer": dealer_hand,
                "player_val": 21, "dealer_val": dealer_val,
                "won": True, "winnings": int(bet * 2.5), "blackjack": True}

    # Player draws cards (simulated — always stand at 17+)
    while player_val < 17 and len(player_hand) < 7:
        player_hand.append(ranks.pop())
        player_val = card_value(player_hand)

    # 7 Card Charlie
    if len(player_hand) >= 7 and player_val <= 21:
        return {"player": player_hand, "dealer": dealer_hand,
                "player_val": player_val, "dealer_val": dealer_val,
                "won": True, "winnings": bet * 2, "blackjack": False, "charlie": True}

    # Dealer draws
    while dealer_val < 17:
        dealer_hand.append(ranks.pop())
        dealer_val = card_value(dealer_hand)

    if player_val > 21:
        won = False
    elif dealer_val > 21:
        won = True
    elif player_val > dealer_val:
        won = True
    else:
        won = False

    winnings = bet * 2 if won else -bet
    return {"player": player_hand, "dealer": dealer_hand,
            "player_val": player_val, "dealer_val": dealer_val,
            "won": won, "winnings": winnings, "blackjack": False}


# --- Slots ---
# Wiki: 5 reels, symbols: Diamond, 100, Clover, Gift, Sparkle
# 5 in a row: Diamond 20x, 100 17.5x, Clover 15x, Gift 12.5x, Sparkle 10x
# 4 in a row: Diamond 5.5x, 100 4.8125x, Clover 4.125x, Gift 3.4375x, Sparkle 2.75x
# 3 in a row: Diamond 2.0x, 100 1.75x, Clover 1.5x, Gift 1.25x, Sparkle 1.0x

SLOT_SYMBOLS = ["💎", "💯", "🍀", "🎁", "✨"]
SLOT_WEIGHTS = [5, 10, 20, 25, 40]  # Diamond rarest, Sparkle most common

# Multipliers: {count: {symbol: mult}}
SLOT_MULTS = {
    5: {"💎": 20, "💯": 17.5, "🍀": 15, "🎁": 12.5, "✨": 10},
    4: {"💎": 5.5, "💯": 4.8125, "🍀": 4.125, "🎁": 3.4375, "✨": 2.75},
    3: {"💎": 2.0, "💯": 1.75, "🍀": 1.5, "🎁": 1.25, "✨": 1.0},
}


def slots_game(bet: int) -> dict:
    reels = random.choices(SLOT_SYMBOLS, weights=SLOT_WEIGHTS, k=5)

    # Find longest consecutive run from left
    best_count = 1
    best_symbol = reels[0]
    current_count = 1
    for i in range(1, 5):
        if reels[i] == reels[i - 1]:
            current_count += 1
        else:
            if current_count > best_count:
                best_count = current_count
                best_symbol = reels[i - 1]
            current_count = 1
    if current_count > best_count:
        best_count = current_count
        best_symbol = reels[-1]

    mult = 0
    if best_count >= 3 and best_symbol in SLOT_MULTS.get(best_count, {}):
        mult = SLOT_MULTS[best_count][best_symbol]

    winnings = int(bet * mult)
    return {"reels": reels, "winnings": winnings, "mult": mult,
            "match_count": best_count, "match_symbol": best_symbol}


# --- Lottery ---
# Wiki: Pick numbers, winners every 12h, pot is 2.5x ticket price, max 200 tickets

def buy_lottery_ticket(user_id: int, numbers: list) -> dict:
    if len(numbers) != 3:
        return {"success": False, "message": "Нужно выбрать 3 числа от 1 до 50."}
    for n in numbers:
        if not 1 <= n <= 50:
            return {"success": False, "message": "Числа должны быть от 1 до 50."}
    return {"success": True, "numbers": sorted(numbers)}


def draw_lottery(winners: list) -> dict:
    winning = sorted([random.randint(1, 50) for _ in range(3)])
    prize = 0
    winners_list = []

    for entry in winners:
        numbers = sorted(entry["numbers"])
        matches = len(set(numbers) & set(winning))
        if matches == 3:
            prize = 50000
            winners_list.append((entry["user_id"], prize))
        elif matches == 2:
            prize = 5000
            winners_list.append((entry["user_id"], prize))

    return {"winning_numbers": winning, "winners": winners_list, "prize_per_winner": prize}


# --- Wheel ---
# Wiki: 16 tiles (4 blue, 4 brown, 4 orange, 1 purple, 1 red, 1 green, 1 yellow)
# Blue: lose 100%, Brown: lose 90%, Orange: lose 75%
# Red: lose 100% + 1 life potion, Yellow: lose 100% + 1 lottery ticket
# Green: win 100%, Purple: win 10x

WHEEL_COLORS = (
    ["blue"] * 4 + ["brown"] * 4 + ["orange"] * 4 +
    ["purple"] * 1 + ["red"] * 1 + ["green"] * 1 + ["yellow"] * 1
)

WHEEL_OUTCOMES = {
    "blue":   {"mult": -1.0, "item": None, "emoji": "🔵"},
    "brown":  {"mult": -0.9, "item": None, "emoji": "🟤"},
    "orange": {"mult": -0.75, "item": None, "emoji": "🟠"},
    "red":    {"mult": -1.0, "item": "life_potion", "emoji": "🔴"},
    "yellow": {"mult": -1.0, "item": "lotteryticket", "emoji": "🟡"},
    "green":  {"mult": 1.0, "item": None, "emoji": "🟢"},
    "purple": {"mult": 10.0, "item": None, "emoji": "🟣"},
}


def wheel_game(bet: int) -> dict:
    color = random.choice(WHEEL_COLORS)
    outcome = WHEEL_OUTCOMES[color]
    winnings = int(bet * outcome["mult"])

    return {
        "color": color,
        "emoji": outcome["emoji"],
        "winnings": winnings,
        "item": outcome["item"],
    }


# --- Big Dice ---
# Wiki: Area 14+, global pot. Roll 1-6 = win pot, 7+ = lose.
# Half of lost bets go to pot. Pot never resets.
# More gambling = fewer sides on dice. Higher pot = more sides.

def big_dice_game(bet: int, total_gambled: int = 0) -> dict:
    global BIG_DICE_POT

    # Base sides: 20. Reduced by gambling volume, increased by pot size
    base_sides = 20
    gamble_reduction = min(total_gambled // 1000000, 10)  # -1 per 1M gambled, max -10
    pot_increase = min(BIG_DICE_POT // 1000000000, 20)    # +1 per 1B in pot, max +20
    sides = max(7, base_sides - gamble_reduction + pot_increase)

    roll = random.randint(1, sides)

    # Add half of bet to pot
    BIG_DICE_POT += bet // 2

    if roll <= 6:
        # Win the pot
        pot_won = BIG_DICE_POT
        winnings = pot_won - bet  # You still lose your bet, but win the pot
        return {"won": True, "roll": roll, "sides": sides,
                "pot_won": pot_won, "winnings": winnings, "lost_bet": bet}
    else:
        return {"won": False, "roll": roll, "sides": sides,
                "pot_won": 0, "winnings": -bet, "lost_bet": bet}
