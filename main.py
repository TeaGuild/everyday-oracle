from telegram import (
    Update,
    InlineQueryResultArticle,
    InputTextMessageContent,
    ParseMode,
)
from telegram.ext import Updater, CommandHandler, CallbackContext, InlineQueryHandler
from metaforecasting.metaculus import MetaculusForecaster, MetaculusIDNotFound
from dotenv import load_dotenv
from uuid import uuid4
import sys
import os

from loguru import logger
from metaforecasting.models import ForecastMetaculusData

logger.info("Starting up...")
load_dotenv()

logger.add("bot.log", rotation=os.getenv("ROTATION"))

telegram_token = os.getenv("TOKEN")
if not telegram_token:
    logger.info("No Telegram Token Provided, exiting now")
    sys.exit("No Telegram Token Provided")

about_text = "Привет! Я та, что видит будущее... Ну, или по крайней мере, просто тырит инфу с инетика, ня."

forecaster = MetaculusForecaster()
updater = Updater(telegram_token)

logger.info("Init done.")

TIME_FORMAT = "%d.%m.%Y %H:%M"


def format_metaculus_as_html(data: ForecastMetaculusData) -> str:
    return (
        f"<b>{data.question_title}</b> (ID: {data.id_on_platform})\n"
        f'<a href="{data.question_url}">Ссылка</a>\n\n'
        f"🔮 Текущие вероятности (q1, q2, q3): \n<b>"
        f"{data.community_prediction.full.q1}%, {data.community_prediction.full.q2}%, "
        f"{data.community_prediction.full.q3}% </b>\n\n"
        f"⏱ Время закрытия вопроса: <b>{data.close_time.strftime(TIME_FORMAT)}</b>\n"
        f"🔔 Время завершения события: <b>{data.resolve_time.strftime(TIME_FORMAT)}</b>\n"
        f"👤 Всего предсказаний сообщества: <b>{data.total_predictions}</b>"
    )


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(about_text)


def current(update: Update, context: CallbackContext):
    cmd = update.message.text.split()
    logger.info(
        f"{cmd} from {update.effective_user.id}:{update.effective_user.name} in {update.message.chat_id}"
    )
    if len(cmd) != 2:
        update.message.reply_markdown_v2(
            "Повторите команду в формате `/current <id вопроса на метакулусе>`"
        )
        logger.debug("Malformed command, rejecting")
        return
    try:
        data = forecaster.get_prediction(int(cmd[1]))
        report = format_metaculus_as_html(data)
    except ValueError:
        update.message.reply_text(
            "ID не похож на вопрос. Повторите команду в формате `/current <id вопроса на "
            "метакулусе>`"
        )
        logger.debug("Malformed command, not int, rejecting")
    except MetaculusIDNotFound:
        update.message.reply_markdown_v2("ID не найден\\(")
        logger.debug("Entry not found, 404, rejecting")
    else:
        logger.debug(f"Everything is fine, sending report of {data.question_title}")
        update.message.reply_html(report)


def inline_query(update: Update, context: CallbackContext) -> None:
    """Handle the inline query."""
    query = update.inline_query.query
    results = []
    logger.info(
        f"Incoming inline query '{query}' from {update.effective_user.id}:{update.effective_user.name}"
    )

    try:
        data = forecaster.get_prediction(int(query))
        report = format_metaculus_as_html(data)
        logger.debug(f"Report formed, ready to send. {data.question_title}")

        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=data.question_title,
                description=f"Медиана - {data.community_prediction.full.q2}%",
                input_message_content=InputTextMessageContent(
                    report, parse_mode=ParseMode.HTML
                ),
            )
        )
    except MetaculusIDNotFound:
        logger.debug(f"Rejected, 404, ready to send.")

        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="404",
                description="ID не найден",
                input_message_content=InputTextMessageContent("❌"),
            )
        )

    except ValueError:
        for result in forecaster.search(query, display_popular=True):
            try:
                if result is None:
                    continue
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid4()),
                        title=result.question_title,
                        description=f"Медиана - {result.community_prediction.full.q2}%",
                        input_message_content=InputTextMessageContent(
                            format_metaculus_as_html(result), parse_mode=ParseMode.HTML
                        ),
                    )
                )
            except Exception as e:
                logger.debug(f"Exception during search, '{query}', '{e}'")
        logger.debug(f"Search report formed, ready to send, '{query}'")

    update.inline_query.answer(results, cache_time=60, is_personal=True)


logger.debug("Adding handlers...")
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("current", current))
updater.dispatcher.add_handler(InlineQueryHandler(inline_query))
logger.debug("Handlers loaded.")

updater.start_polling()
logger.info("Running bot.")
updater.idle()
