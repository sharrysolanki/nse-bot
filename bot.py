import os
import threading
import asyncio
from flask import Flask
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN nahi mila Environment me!")

# Flask app for Render to keep alive
app = Flask(__name__)

@app.route('/')
def home():
    return "NSE Bot is LIVE! - https://nse-bot-142m.onrender.com"

# --- Telegram Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🟢 **NSE Live Bot is LIVE!**\n\n"
        "Koi bhi NSE stock ka naam bhejo:\n"
        "Ex: TCS, RELIANCE, ONGC, INFY\n\n"
        "/help - help ke liye"
    )
    await update.message.reply_text(msg)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bas stock ka naam likho, mai live price bata dunga!\nEx: TCS")

async def get_stock_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper().strip()
    if len(symbol) > 10 or " " in symbol or symbol.startswith("/"):
        return

    try:
        await update.message.reply_text(f"🔍 {symbol} ka live data la raha hu...")

        # yfinance ko alag thread me chalao - yahi tera crash fix hai
        def fetch_data():
            ticker = yf.Ticker(symbol + ".NS")
            return ticker.history(period="1d")

        hist = await asyncio.to_thread(fetch_data)
        
        if hist.empty:
            await update.message.reply_text(f"❌ {symbol} NSE pe nahi mila. Sahi symbol likho.")
            return

        price = hist['Close'].iloc[-1]
        open_p = hist['Open'].iloc[-1]
        high = hist['High'].iloc[-1]
        low = hist['Low'].iloc[-1]

        change = price - open_p
        perc = (change / open_p) * 100 if open_p != 0 else 0
        emoji = "📈" if change >= 0 else "📉"

        report = (
            f"🎯 **{symbol} - REAL LIVE REPORT**\n"
            f"--------------------------\n"
            f"{emoji} Live Price: Rs {price:.2f}\n"
            f"Change: {change:.2f} ({perc:.2f}%)\n"
            f"Open: {open_p:.2f} | High: {high:.2f} | Low: {low:.2f}\n"
            f"--------------------------\n"
            f"Source: NSE via Yahoo"
        )
        await update.message.reply_text(report)

    except Exception as e:
        print(f"Error for {symbol}: {e}")
        await update.message.reply_text(f"⚠️ {symbol} ka data abhi nahi la paya, thodi der baad try karo.")

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Flask ko background thread me
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("Flask started in background thread")

    # Bot ko MAIN thread me chalao - tabhi Render pe chalega
    print("Bot starting in MAIN thread...")
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_stock_price))
    
    print("Bot polling started...")
    application.run_polling()
