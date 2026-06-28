from aiogram import Router, F
from aiogram.types import Message
from game.guilds import create_guild, join_guild, deposit_to_guild, get_guild_info, leave_guild
from database.crud import get_user

router = Router()


@router.message(F.text.startswith("/guild"))
async def cmd_guild(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    if not user:
        await message.answer("❌ Сначала зарегистрируйтесь: /start")
        return

    args = message.text.split()[1:] if message.text else []

    if not args:
        info = await get_guild_info(user_id)
        if info["success"]:
            text = (
                f"🏰 <b>{info['name']}</b>\n\n"
                f"👑 Лидер: {info['owner']}\n"
                f"📊 Уровень: {info['level']}\n"
                f"⭐ XP: {info['xp']}\n"
                f"👥 Участники: {info['members']}/10\n"
                f"📦 Хранилище: {info['materials']}\n"
                f"🏷️ Ваш ранг: {info['rank']}\n\n"
                f"Команды:\n"
                f"/guild create [имя] — Создать (500,000)\n"
                f"/guild join [имя] — Вступить\n"
                f"/guild deposit [ресурс] [кол-во] — Сдать\n"
                f"/guild leave — Покинуть"
            )
        else:
            text = (
                "🏰 <b>Гильдии</b>\n\n"
                f"{info['message']}\n\n"
                "Команды:\n"
                "/guild create [имя] — Создать (500,000)\n"
                "/guild join [имя] — Вступить"
            )
        await message.answer(text, parse_mode="HTML")
        return

    action = args[0].lower()

    if action == "create" and len(args) > 1:
        name = " ".join(args[1:])
        result = await create_guild(user_id, name)
        await message.answer(result["message"])

    elif action == "join" and len(args) > 1:
        name = " ".join(args[1:])
        result = await join_guild(user_id, name)
        await message.answer(result["message"])

    elif action == "deposit" and len(args) > 2:
        material = args[1]
        try:
            amount = int(args[2])
        except ValueError:
            await message.answer("❌ Неверное количество.")
            return
        result = await deposit_to_guild(user_id, material, amount)
        await message.answer(result["message"])

    elif action == "leave":
        result = await leave_guild(user_id)
        await message.answer(result["message"])

    else:
        await message.answer("❌ Неизвестная команда. /guild create/join/deposit/leave")
