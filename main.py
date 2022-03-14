from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext, InlineQueryHandler
from metaculus import MetaculusForecaster, MetaculusIDNotFound
from dotenv import load_dotenv
from uuid import uuid4
import sys
import os

load_dotenv()

telegram_token = os.getenv("TOKEN")
if not telegram_token:
    sys.exit("No Telegram Token Provided")

about_text = "Привет! Я та, что видит будущее... Ну, или по крайней мере, просто тырит инфу с инетика, ня."

forecaster = MetaculusForecaster()
updater = Updater(telegram_token)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(about_text)

def current(update: Update, context: CallbackContext):
    cmd = update.message.text.split()
    if len(cmd) != 2:
        update.message.reply_markdown_v2("Повторите команду в формате `/current <id вопроса на метакулусе>`")
        return
    try:
        report = forecaster.format_as_html(forecaster.get_prediction(int(cmd[1])))
    except ValueError:
        update.message.reply_text("ID не похож на вопрос. Повторите команду в формате `/current <id вопроса на "
                                  "метакулусе>`")
    except MetaculusIDNotFound:
        update.message.reply_markdown_v2("ID не найден(")
    else:
        update.message.reply_html(report)


def inline_query(update: Update, context: CallbackContext) -> None:
    """Handle the inline query."""
    query = update.inline_query.query
    results = []
    try:
        data = forecaster.get_prediction(int(query))
        report = forecaster.format_as_html(data)

        results.append(InlineQueryResultArticle(
            id=str(uuid4()),
            title=data.question_title,
            description=f'Медиана - {data.community_prediction.full.q2}%',
            input_message_content=InputTextMessageContent(report, parse_mode=ParseMode.HTML)
        ))
    except MetaculusIDNotFound:
        stop_taxi = True

        results.append(InlineQueryResultArticle(
            id=str(uuid4()),
            title="404",
            description="ID не найден",
            input_message_content=InputTextMessageContent("❌")
        ))

    except ValueError:
        for result in forecaster.search(query, display_popular=True):
            try:
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid4()),
                        title=result.question_title,
                        description=f'Медиана - {result.community_prediction.full.q2}%',
                        input_message_content=InputTextMessageContent(
                            forecaster.format_as_html(result), parse_mode=ParseMode.HTML
                        )
                    )
                )
            except Exception as e:
                print(e)



    update.inline_query.answer(results)


updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('current', current))
updater.dispatcher.add_handler(InlineQueryHandler(inline_query))

updater.start_polling()
updater.idle()
