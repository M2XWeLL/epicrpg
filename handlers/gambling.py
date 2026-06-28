"""
Gambling commands: dice, cups, blackjack, slots, cf (coinflip), lottery, wheel, big_dice.
"""
from aiogram import Router, F
from aiogram.types import Message
from database.crud import get_user, get_cooldowns
from game.gambling import dice_game, cups_game, coinflip, slots_game, blackjack, buy_lottery_ticket, wheel_game, big_dice_game
from game.player import add_coins, remove_coins
from game.quest import on_gambling_win
import config

router = Router()


@router.message(F.text.startswith("/dice"))
async def cmd_dice(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    bet = int(args[0]) if args else 0
    if bet < config.GAMBLING_MIN_BET:
        await message.answer(f"❌ Минимум ставка: {config.GAMBLING_MIN_BET} монет.")
        return
    if bet > config.GAMBLING_MAX_BET:
        await message.answer(f"❌ Максимум ставка: {config.GAMBLING_MAX_BET} монет.")
        return
    if user.coins < bet:
        await message.answer("❌ Недостаточно монет.")
        return

    await remove_coins(message.from_user.id, bet)
    result = dice_game(bet)

    roll = result["player"]
    emoji_map = {1: "💀", 2: "😰", 3: "😐", 4: "🙂", 5: "😊", 6: "🤑", 7: "🎰"}
    emoji = emoji_map.get(roll, "🎲")

    if result["won"]:
        await add_coins(message.from_user.id, result["winnings"])
        await on_gambling_win(message.from_user.id, result["winnings"])
        text = f"🎲 <b>Dice</b>\n\nВыпало: {emoji} {roll}\n\n🎉 Выигрыш: +{result['winnings']:,} монет!"
    else:
        text = f"🎲 <b>Dice</b>\n\nВыпало: {emoji} {roll}\n\n💀 Проигрыш: {result['winnings']:,} монет."

    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/cups"))
async def cmd_cups(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    if len(args) < 2:
        await message.answer("Формат: /cups [ставка] [1/2/3]", parse_mode="HTML")
        return

    bet = int(args[0])
    choice = int(args[1])
    if bet < config.GAMBLING_MIN_BET or bet > config.GAMBLING_MAX_BET:
        await message.answer(f"❌ Ставка от {config.GAMBLING_MIN_BET} до {config.GAMBLING_MAX_BET}.")
        return
    if choice not in (1, 2, 3):
        await message.answer("Выберите 1, 2 или 3.")
        return
    if user.coins < bet:
        await message.answer("❌ Недостаточно монет.")
        return

    await remove_coins(message.from_user.id, bet)
    result = cups_game(bet, choice)

    cups = ["🥤", "🥤", "🥤"]
    cups[result["cup"] - 1] = "🏆"

    if result["won"]:
        await add_coins(message.from_user.id, result["winnings"])
        await on_gambling_win(message.from_user.id, result["winnings"])
        text = f"🥤 <b>Cups</b>\n\n[{cups[0]}] [{cups[1]}] [{cups[2]}]\n\n🎉 Кубок найден! +{result['winnings']:,} монет (x1.75)!"
    else:
        text = f"🥤 <b>Cups</b>\n\n[{cups[0]}] [{cups[1]}] [{cups[2]}]\n\n💀 Кубок был в чашке {result['cup']}. -{bet:,} монет."

    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/cf"))
async def cmd_cf(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    if len(args) < 2:
        await message.answer("Формат: /cf [ставка] [h/t]\nПример: /cf 100 h", parse_mode="HTML")
        return

    bet = int(args[0])
    choice = "heads" if args[1].lower() in ("h", "heads") else "tails"
    if bet < config.GAMBLING_MIN_BET or bet > config.GAMBLING_MAX_BET:
        await message.answer(f"❌ Ставка от {config.GAMBLING_MIN_BET} до {config.GAMBLING_MAX_BET}.")
        return
    if user.coins < bet:
        await message.answer("❌ Недостаточно монет.")
        return

    await remove_coins(message.from_user.id, bet)
    result = coinflip(bet, choice)

    if result.get("side"):
        # 1% side — coin lands in next area
        await add_coins(message.from_user.id, result["winnings"])
        await on_gambling_win(message.from_user.id, result["winnings"])
        text = f"🪙 <b>Coinflip</b>\n\n🌀 Монета улетела в следующую область!\n\n🎉 Выигрыш: +{result['winnings']:,} монет (x5)!"
    elif result["won"]:
        await add_coins(message.from_user.id, result["winnings"])
        await on_gambling_win(message.from_user.id, result["winnings"])
        emoji = "🟡" if result["result"] == "heads" else "🟡"
        text = f"🪙 <b>Coinflip</b>\n\n{emoji} {result['result'].upper()}\n\n🎉 Угадали! +{result['winnings']:,} монет!"
    else:
        emoji = "🪙" if result["result"] == "heads" else "🟡"
        text = f"🪙 <b>Coinflip</b>\n\n{emoji} {result['result'].upper()}\n\n💀 Не угадали! -{bet:,} монет."

    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/slots"))
async def cmd_slots(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    bet = int(args[0]) if args else 0
    if bet < config.GAMBLING_MIN_BET:
        await message.answer(f"❌ Минимум ставка: {config.GAMBLING_MIN_BET} монет.")
        return
    if bet > config.GAMBLING_MAX_BET:
        await message.answer(f"❌ Максимум ставка: {config.GAMBLING_MAX_BET} монет.")
        return
    if user.coins < bet:
        await message.answer("❌ Недостаточно монет.")
        return

    await remove_coins(message.from_user.id, bet)
    result = slots_game(bet)

    reels_str = " | ".join(result["reels"])

    if result["winnings"] > 0:
        await add_coins(message.from_user.id, result["winnings"])
        await on_gambling_win(message.from_user.id, result["winnings"])
        match = result["match_count"]
        text = (
            f"🎰 <b>Slots</b>\n\n"
            f"[{reels_str}]\n\n"
            f"🎉 {match}x {result['match_symbol']} — Выигрыш: +{result['winnings']:,} монет (x{result['mult']})!"
        )
    else:
        text = (
            f"🎰 <b>Slots</b>\n\n"
            f"[{reels_str}]\n\n"
            f"💀 Проигрыш: -{bet:,} монет."
        )

    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/blackjack"))
@router.message(F.text.startswith("/bj"))
async def cmd_blackjack(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    bet = int(args[0]) if args else 0
    if bet < config.GAMBLING_MIN_BET:
        await message.answer(f"❌ Минимум ставка: {config.GAMBLING_MIN_BET} монет.")
        return
    if bet > config.GAMBLING_MAX_BET:
        await message.answer(f"❌ Максимум ставка: {config.GAMBLING_MAX_BET} монет.")
        return
    if user.coins < bet:
        await message.answer("❌ Недостаточно монет.")
        return

    await remove_coins(message.from_user.id, bet)
    result = blackjack(bet)

    def fmt_card(card):
        return f"[{card[1]}]"

    player_cards = " ".join(fmt_card(c) for c in result["player"])
    dealer_cards = " ".join(fmt_card(c) for c in result["dealer"])

    if result["won"]:
        await add_coins(message.from_user.id, result["winnings"])
        await on_gambling_win(message.from_user.id, result["winnings"])
        text = (
            f"🃏 <b>Blackjack</b>\n\n"
            f"Ваши: {player_cards} ({result['player_val']})\n"
            f"Дилер: {dealer_cards} ({result['dealer_val']})\n\n"
            f"🎉 Выигрыш: +{result['winnings']:,} монет!"
        )
    else:
        text = (
            f"🃏 <b>Blackjack</b>\n\n"
            f"Ваши: {player_cards} ({result['player_val']})\n"
            f"Дилер: {dealer_cards} ({result['dealer_val']})\n\n"
            f"💀 Проигрыш: -{bet:,} монет."
        )

    if result.get("blackjack"):
        text += "\n\n🎰 BLACKJACK! x2.5"
    elif result.get("charlie"):
        text += "\n\n🎰 7 CARD CHARLIE! x2"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/wheel"))
async def cmd_wheel(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    if user.area < 8:
        await message.answer("❌ Wheel доступен с Area 8.")
        return

    bet = int(args[0]) if args else 0
    if bet < 25000:
        await message.answer("❌ Минимум ставка: 25,000 монет.")
        return
    if bet > config.GAMBLING_MAX_BET:
        await message.answer(f"❌ Максимум ставка: {config.GAMBLING_MAX_BET:,} монет.")
        return
    if user.coins < bet:
        await message.answer("❌ Недостаточно монет.")
        return

    await remove_coins(message.from_user.id, bet)
    result = wheel_game(bet)

    from database.crud import add_materials

    item_msg = ""
    if result["item"]:
        await add_materials(message.from_user.id, result["item"], 1)
        item_names = {"life_potion": "🧪 Life Potion", "lotteryticket": "🎟 Lottery Ticket"}
        item_msg = f"\n🎁 +1 {item_names.get(result['item'], result['item'])}"

    if result["winnings"] > 0:
        await add_coins(message.from_user.id, result["winnings"])
        await on_gambling_win(message.from_user.id, result["winnings"])
        text = (
            f"🎡 <b>Wheel</b>\n\n"
            f"Выпало: {result['emoji']} {result['color'].upper()}\n\n"
            f"🎉 Выигрыш: +{result['winnings']:,} монет!{item_msg}"
        )
    else:
        text = (
            f"🎡 <b>Wheel</b>\n\n"
            f"Выпало: {result['emoji']} {result['color'].upper()}\n\n"
            f"💀 Проигрыш: {result['winnings']:,} монет.{item_msg}"
        )

    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/big_dice"))
@router.message(F.text.startswith("/big dice"))
async def cmd_big_dice(message: Message):
    args = message.text.split()
    # Remove "big" and "dice" from args if present
    args = [a for a in args if a.lower() not in ("big", "dice", "/big_dice", "/big")]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    if user.area < 14:
        await message.answer("❌ Big Dice доступен с Area 14.")
        return

    bet = int(args[0]) if args else 0
    if bet < config.GAMBLING_MIN_BET:
        await message.answer(f"❌ Минимум ставка: {config.GAMBLING_MIN_BET} монет.")
        return
    if bet > config.GAMBLING_MAX_BET:
        await message.answer(f"❌ Максимум ставка: {config.GAMBLING_MAX_BET:,} монет.")
        return
    if user.coins < bet:
        await message.answer("❌ Недостаточно монет.")
        return

    await remove_coins(message.from_user.id, bet)
    result = big_dice_game(bet)

    from game.gambling import BIG_DICE_POT

    if result["won"]:
        # Win the pot (bet was already removed, pot winnings go on top)
        await add_coins(message.from_user.id, result["pot_won"])
        await on_gambling_win(message.from_user.id, result["pot_won"])
        text = (
            f"🎲 <b>Big Dice</b>\n\n"
            f"Выпало: {result['roll']} из {result['sides']}\n"
            f"🏦 Банк: {result['pot_won']:,}\n\n"
            f"🎉 ВЫ ВЫИГРАЛИ БАНК! +{result['pot_won']:,} монет!"
        )
    else:
        text = (
            f"🎲 <b>Big Dice</b>\n\n"
            f"Выпало: {result['roll']} из {result['sides']}\n"
            f"🏦 Банк: {BIG_DICE_POT:,}\n\n"
            f"💀 Проигрыш: -{bet:,} монет."
        )

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/lottery")
@router.message(F.text.startswith("/lottery"))
async def cmd_lottery(message: Message):
    args = message.text.split()[1:]
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    if not args:
        await message.answer(
            "🎰 <b>Лотерея</b>\n\n"
            "Купить билет: /lottery [число1] [число2] [число3]\n"
            "Числа от 1 до 50. Стоимость: 100 монет.\n"
            "Максимум: 200 билетов\n\n"
            "3 совпадения = 50,000\n"
            "2 совпадения = 5,000",
            parse_mode="HTML"
        )
        return

    if user.coins < 100:
        await message.answer("❌ Нужно 100 монет на билет.")
        return

    try:
        numbers = [int(a) for a in args[:3]]
    except ValueError:
        await message.answer("❌ Введите числа от 1 до 50.")
        return

    result = buy_lottery_ticket(message.from_user.id, numbers)
    if not result["success"]:
        await message.answer(result["message"])
        return

    await remove_coins(message.from_user.id, 100)
    nums = " ".join(str(n) for n in result["numbers"])
    await message.answer(
        f"🎰 Билет куплен!\n"
        f"Ваши числа: <b>{nums}</b>\n\n"
        f"Розыгрыш каждые 12 часов.",
        parse_mode="HTML"
    )
