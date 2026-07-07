import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
import live_price_api_tele
from live_price_api_tele import PriceManager
from coin_dic import coins
from telebot_currency_database import BotDatabase


tracker_tool = PriceManager()
db = BotDatabase()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


get_crypto_name ,get_another_name = range(2)
ALERT_COIN ,ALERT_PRICE = range(2, 4)
async def start_command(update : Update, context: ContextTypes.DEFAULT_TYPE) :
    print("start command executed")
    await update.message.reply_text("🔥 Welcome حاجی! اینجا منوی ربات هوشمند تریدینگ توست:\n\n"
        "📈 /crypto - دریافت قیمت زنده هر ارزی\n"
        "⏰ /setalert - ثبت هشدار قیمت جدید\n"
        "❌ /cancel - لغو عملیات فعلی"
)
#==============================SET ALERT
async def setalert_command(update : Update, context: ContextTypes.DEFAULT_TYPE) :
    await update.message.reply_text("GREAT! Please Enter The Crypto Name For The Alert :")
    return ALERT_COIN

async def alert_receive_coin(update : Update, context: ContextTypes.DEFAULT_TYPE) :
    coin_input = update.message.text.strip().lower()
    result_alert = tracker_tool.get_crypto_price(coin_input)
    if not result_alert["success"]:
        await update.message.reply_text(f"Error :{result_alert['error']}\nPlease Enter A Valid Name")
        return ALERT_COIN

    context.user_data["alert_symbol"] = coin_input
    context.user_data["alert_price"] = result_alert["crypto_price"]

    await update.message.reply_text(f"💰 Current price of {result_alert['crypto_symbol']} is {result_alert['crypto_price']:,} $\n\n"
        f"Now, enter your Target Price in USD (Numbers only):"
    )

    return ALERT_PRICE



async def alert_receive_price(update : Update, context: ContextTypes.DEFAULT_TYPE) :
  try :
       target_price = float(update.message.text)
  except ValueError :
        await update.message.reply_text("Please Enter A Valid Target Price:")
        return ALERT_PRICE

  chat_id = update.effective_chat.id
  symbol_alert = context.user_data["alert_symbol"]
  alert_price = context.user_data["alert_price"]

  if target_price >= alert_price :
      condition = "above"
      cond_text = "goes above"
  else :
    condition = "below"
    cond_text = "goes below"

  db.add_alerts(chat_id,symbol_alert,target_price,condition)

  await update.message.reply_text(
      f"✅ Alert registered successfully!\n"
      f"🔔 We will notify you when **{symbol_alert}** {cond_text} **{target_price:,} $**."
  )

  context.user_data.clear()
  return ConversationHandler.END





#===================================================Job Queue

async def check_alert_job(context : ContextTypes.DEFAULT_TYPE) :


    active_alerts = db.get_all_alerts()

    if not active_alerts:
        return
    print(f"🔄 Checking {len(active_alerts)} active alerts from database...")

    for alert in active_alerts:
        alert_id = alert["id"]
        symbol = alert["symbol"]
        target = alert["target_price"]
        condition = alert["condition"]
        chat_id = alert["chat_id"]

        res = tracker_tool.get_crypto_price(symbol)

        if not res["success"]:
            continue

        live_price = res["crypto_price"]



        db.update_price(symbol, live_price)

        trigger = False

        if condition == "above" and live_price >= target:
            trigger = True
        elif condition == "below" and live_price <= target:
            trigger = True

        if trigger:
            message = (
                f"🚨🚨 **PRICE ALERT TRIGGERED** 🚨🚨\n\n"
                f"🪙 Coin: {symbol.upper()}\n"
                f"🎯 Target Price: {target:,} $\n"
                f"💵 Current Live Price: {live_price:,} $\n\n"
                f"Time to check your charts! 📈📉"
            )
            try:
                await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
                db.delete_alert(alert_id)
            except Exception as e:
                print(f"Failed to send message to {chat_id} : {e}")


#=====================================================CRYPTO TRACKER

async def crypto_command(update : Update, context:ContextTypes.DEFAULT_TYPE) :
    print("crypto command executed")
    await update.message.reply_text("""Please Insert Crypto Name (e.g bitcoin or btc) :\n
All Currencies Are In USDT    
    """)
    return get_crypto_name

async def crypto_tracker(update : Update, context:ContextTypes.DEFAULT_TYPE):
    user_demand_tracker = update.message.text.strip().lower()
    symbol = coins.get(user_demand_tracker)
    if symbol is None:
        await update.message.reply_text("❌ Coin not found. Try BITCOIN,ETHEREUM,...")
        return get_crypto_name
    await update.message.reply_text("GETTING DATA...")
    result = tracker_tool.get_crypto_price(user_demand_tracker)

    if result["success"]  :

            db.update_price(result["crypto_symbol"], result["crypto_price"])
            text = (
                f"Crypto Name : {user_demand_tracker.upper()}\n"
                f"Crypto Symbol : {result['crypto_symbol']} $ \n"
                f"Crypto Price : {result['crypto_price']}\n"
            )

            await update.message.reply_text(text)
            keyboard = [
                [
                    InlineKeyboardButton("Yes", callback_data="yes"),
                    InlineKeyboardButton("No", callback_data="no"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text("Do You Need Another Currency ?",
                                            reply_markup=reply_markup)
            return get_another_name

    else :
            await update.message.reply_text(f"Error While Fetching Data ; {result['error']}")
            return get_crypto_name
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    answer = query.data

    if answer == "yes":
        await query.message.reply_text("Please Type In The Coin Name")
        return get_crypto_name

    elif answer == "no":
        await query.message.reply_text("Come Back AnyTime!")
        return ConversationHandler.END
    else:
        await query.message.reply_text("Invalid option")
        return get_another_name

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Process Cancelled")
    return ConversationHandler.END

#===============================================INIT

if __name__ == '__main__':
    print("The Bot is running")
    MY_TOKEN = "---"
    app =ApplicationBuilder().token(MY_TOKEN).build()
    job_queue = app.job_queue
    job_queue.run_repeating(check_alert_job, interval=20, first=10)
    alert_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("SetAlert", setalert_command)],
        states={
            ALERT_COIN:[MessageHandler(filters.TEXT & ~filters.COMMAND, alert_receive_coin)],
            ALERT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, alert_receive_price)]

        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )
    crypto_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('crypto', crypto_command)],
        states={
            get_crypto_name: [MessageHandler(filters.TEXT & ~filters.COMMAND, crypto_tracker)

            ],

            get_another_name: [CallbackQueryHandler(button_handler)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(alert_conv_handler)
    app.add_handler(crypto_conv_handler)
    app.run_polling()










