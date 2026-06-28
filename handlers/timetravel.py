"""
Time Travel commands: /timetravel, /timetravel confirm.
Shows TT info, bonus table, and executes the reset.
"""
from aiogram import Router, F
from aiogram.types import Message
from game.timetravel import (
    can_timetravel, do_timetravel, get_tt_table_row,
    get_tt_title, get_max_dungeon, can_trade_coins,
    calc_stt_score, can_super_timetravel, do_super_timetravel,
    STT_REWARDS,
)

router = Router()


@router.message(F.text == "/timetravel")
@router.message(F.text.startswith("/timetravel "))
async def cmd_timetravel(message: Message):
    user_id = message.from_user.id
    args = message.text.split()

    # /timetravel confirm
    if len(args) > 1 and args[1] == "confirm":
        result = await do_timetravel(user_id)
        await message.answer(result["message"], parse_mode="HTML")
        return

    # /timetravel table — show full TT bonus table
    if len(args) > 1 and args[1] == "table":
        text = "⏳ <b>Time Travel Bonus Table</b>\n\n"
        text += "TT# | +XP | +Duel XP | +Drops | +Items\n"
        text += "────┼─────┼──────────┼────────┼───────\n"
        for tt in range(0, 26):
            row = get_tt_table_row(tt)
            text += f"  {tt:2d} | {row['exp']:5.0f}% | {row['duel_exp']:7.0f}%  | {row['drops']:5.0f}% | {row['items']:5.0f}%\n"
        await message.answer(text, parse_mode="HTML")
        return

    check = await can_timetravel(user_id)
    if not check["can"]:
        await message.answer(check["message"])
        return

    from database.crud import get_user
    user = await get_user(user_id)
    tt = user.tt_count
    next_tt = tt + 1
    title = get_tt_title(next_tt)
    max_dung = get_max_dungeon(next_tt)

    row = get_tt_table_row(next_tt)

    text = (
        f"⏳ <b>Time Travel</b>\n\n"
        f"Текущий TT: <b>{tt}</b>\n"
        f"Следующий: TT{next_tt}\n"
        f"Требуемый уровень: {check['required_level']}\n"
        f"Текущий уровень: {user.level}\n\n"
        f"📊 Бонусы на TT{next_tt}:\n"
        f"  • XP: +{row['exp']:.0f}%\n"
        f"  • Duel XP: +{row['duel_exp']:.0f}%\n"
        f"  • Drops: +{row['drops']:.0f}%\n"
        f"  • Items: +{row['items']:.0f}%\n"
    )

    if title:
        text += f"\n🏆 Новый титул: <b>{title}</b>\n"

    text += (
        f"\n🏰 Макс. данжон: D{max_dung}\n\n"
        f"⚠️ <b>Сброс:</b>\n"
        f"  • Уровень → 1\n"
        f"  • Локация → Area 1\n"
        f"  • Снаряжение → Тир 1\n"
        f"  • Материалы → очищены\n\n"
        f"🔒 <b>Сохраняется:</b>\n"
        f"  Монеты, банк, EPIC монеты, лошадь,\n"
        f"  питомцы, профессии, печенье арены,\n"
        f"  эссенции\n\n"
        f"Подтвердить: <code>/timetravel confirm</code>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "/super_timetravel")
@router.message(F.text.startswith("/super_timetravel "))
async def cmd_super_timetravel(message: Message):
    user_id = message.from_user.id
    args = message.text.split()

    # /super_timetravel score — show STT score
    if len(args) > 1 and args[1] == "score":
        from database.crud import get_user, get_inventory
        user = await get_user(user_id)
        if not user:
            await message.answer("❌ Сначала зарегистрируйтесь: /start")
            return
        inv = await get_inventory(user_id)
        score = calc_stt_score(user, inv)
        text = f"⏳ <b>Super Time Travel Score</b>\n\n"
        text += f"Ваши очки: <b>{score}</b>\n\n"
        text += "Награды:\n"
        for rid, r in STT_REWARDS.items():
            status = "✅" if score >= r["cost"] else "❌"
            text += f"  {status} {r['name']} — {r['cost']} очков\n"
        text += "\nВыбрать: <code>/super_timetravel [reward_id]</code>"
        await message.answer(text, parse_mode="HTML")
        return

    # /super_timetravel [reward_id] — choose a reward
    if len(args) > 1 and args[1] != "confirm":
        reward_id = args[1]
        result = await do_super_timetravel(user_id, reward_id)
        await message.answer(result["message"], parse_mode="HTML")
        return

    check = await can_super_timetravel(user_id)
    if not check["can"]:
        await message.answer(check["message"])
        return

    await message.answer(
        f"⏳ <b>Super Time Travel</b>\n\n"
        f"Текущий TT: {check['tt_count']}\n\n"
        f"Super Time Travel жертвует предметами за Score, затем выбираешь награду.\n\n"
        f"Посмотреть Score: <code>/super_timetravel score</code>\n"
        f"Выбрать награду: <code>/super_timetravel [reward_id]</code>",
        parse_mode="HTML"
    )
