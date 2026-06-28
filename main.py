"""
Epic RPG Telegram Bot
"""
import asyncio
import logging

import aiohttp.resolver
aiohttp.resolver.DefaultResolver = aiohttp.resolver.ThreadedResolver

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message
from config import BOT_TOKEN, LOG_LEVEL
from database.engine import init_db
from data.ru_aliases import RU_COMMANDS, RU_ITEMS

# English compound commands: "hunt alone" -> "hunt_alone"
# Allows typing with spaces instead of underscores
EN_COMPOUND = {
    "hunt alone": "hunt_alone",
    "hunt together": "hunt_together",
    "hunt hardmode": "hunt_hardmode",
    "epic quest": "epic_quest",
    "epic shop": "epic_shop",
    "super timetravel": "super_timetravel",
    "big dice": "big_dice",
    "big arena": "big_arena",
    "adventure hardmode": "adventure_hardmode",
    "profession rewards": "profession_rewards",
    "profession claim": "profession_claim",
    "cd": "cooldowns",
}


class RpgPrefixMiddleware(BaseMiddleware):
    """Convert Russian commands and RPG prefix to English equivalents.
    Both /hunt and /охота and rpg hunt and рпг охота all work.
    English compound commands are joined with underscores:
    'rpg hunt alone' -> '/hunt_alone', '/epic quest' -> '/epic_quest'"""

    async def __call__(self, handler, event, data):
        if isinstance(event, Message) and event.text:
            text = event.text
            lower = text.lower()
            new_text = None  # will hold transformed text if any

            # 1. "рпг команда ..." or "rpg command ..." → "/english_command ..."
            # Support both "rpg command" and "rpgcommand" (no space) prefixes
            rpg_prefix = False
            rest_text = None
            if lower.startswith("рпг ") or lower.startswith("rpg "):
                rest_text = text[4:]  # after "рпг " or "rpg "
                rpg_prefix = True
            elif lower.startswith("рпг") or lower.startswith("rpg"):
                rest_text = text[3:].lstrip()  # after "рпг" or "rpg" without space
                rpg_prefix = True

            if rpg_prefix and rest_text is not None:
                rest_words = rest_text.split()
                matched = False
                # Try 3-word, 2-word, 1-word compound (longest first)
                for n in range(min(3, len(rest_words)), 0, -1):
                    candidate = " ".join(rest_words[:n]).lower()
                    if candidate in RU_COMMANDS:
                        remainder = rest_text[len(candidate):].strip()
                        cmd = "/" + RU_COMMANDS[candidate]
                        new_text = (cmd + " " + remainder).rstrip()
                        matched = True
                        break
                if not matched and rest_words:
                    # Try English compound: "rpg hunt alone" → "/hunt_alone"
                    for n in range(min(3, len(rest_words)), 0, -1):
                        candidate = " ".join(rest_words[:n]).lower()
                        if candidate in EN_COMPOUND:
                            remainder = rest_text[len(candidate):].strip()
                            cmd = "/" + EN_COMPOUND[candidate]
                            new_text = (cmd + " " + remainder).rstrip()
                            matched = True
                            break
                if not matched and rest_words:
                    # Unknown command — pass through
                    new_text = "/" + rest_text

            # 2. "/русскаякоманда ..." → "/english ..."
            elif lower.startswith("/") and len(lower) > 1:
                parts = text[1:].split(None, 1)
                cmd_part = parts[0].lower()
                if cmd_part in RU_COMMANDS:
                    rest = " " + parts[1] if len(parts) > 1 else ""
                    new_text = "/" + RU_COMMANDS[cmd_part] + rest
                else:
                    # Try English compound: "/hunt alone" → "/hunt_alone"
                    rest_text = text[1:]  # after "/"
                    rest_words = rest_text.split()
                    for n in range(min(3, len(rest_words)), 0, -1):
                        candidate = " ".join(rest_words[:n]).lower()
                        if candidate in EN_COMPOUND:
                            remainder = rest_text[len(candidate):].strip()
                            new_text = "/" + EN_COMPOUND[candidate]
                            if remainder:
                                new_text += " " + remainder
                            break

            # 3. Bare Russian command: "охота", "большие кубики", "купить лутбокс"
            elif lower.split()[0] in RU_COMMANDS or " ".join(lower.split()[:3]) in RU_COMMANDS or " ".join(lower.split()[:2]) in RU_COMMANDS:
                words = text.split()
                matched = False
                # Try 3-word, 2-word, 1-word compound (longest first)
                for n in range(min(3, len(words)), 0, -1):
                    candidate = " ".join(words[:n]).lower()
                    if candidate in RU_COMMANDS:
                        remainder = text[len(candidate):].strip()
                        cmd = "/" + RU_COMMANDS[candidate]
                        new_text = (cmd + " " + remainder).rstrip()
                        matched = True
                        break

            # Message is frozen in aiogram 3.29+, so create a copy with updated text
            if new_text is not None:
                event = event.model_copy(update={"text": new_text})

        return await handler(event, data)


async def main():
    logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))

    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.message.middleware(RpgPrefixMiddleware())

    from handlers import (
        start, profile, help, cooldowns,
        hunt, work, craft, shop,
        dungeon, timetravel,
        guild, pet, event,
        gambling, economy, area_cmds,
        fighting, progress, npc, horse, professions,
        bank, marriage, misc, cosmetic,
        returning, trade, tutorial,
    )

    dp.include_routers(
        start.router,
        profile.router,
        help.router,
        cooldowns.router,
        hunt.router,
        work.router,
        craft.router,
        shop.router,
        dungeon.router,
        timetravel.router,
        guild.router,
        pet.router,
        event.router,
        gambling.router,
        economy.router,
        area_cmds.router,
        fighting.router,
        progress.router,
        npc.router,
        horse.router,
        professions.router,
        bank.router,
        marriage.router,
        misc.router,
        cosmetic.router,
        returning.router,
        trade.router,
        tutorial.router,
    )

    logging.info("Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
