import os, requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "TERA_TOKEN_YAHA_DAALO")

MAP = {
    "AIRTEL": "BHARTIARTL", "BHARTI": "BHARTIARTL",
    "RELIANCE": "RELIANCE", "TCS": "TCS", "INFY": "INFY", "ONGC": "ONGC",
    "HDFCBANK": "HDFCBANK", "ICICI": "ICICIBANK", "ICICIBANK": "ICICIBANK",
    "SBIN": "SBIN", "SBI": "SBIN", "ITC": "ITC", "LT": "LT",
}

def get_live_price_moneycontrol(symbol):
    try:
        for url in [f"https://priceapi.moneycontrol.com/pricefeed/nse/equitycash/{symbol}", f"https://priceapi.moneycontrol.com/pricefeed/bse/equitycash/{symbol}"]:
            try:
                r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
                if r.status_code == 200:
                    j = r.json()
                    data = j.get('data', j)
                    price = float(data.get('pricecurrent') or data.get('price') or 0)
                    if price > 0:
                        prev = float(data.get('priceprevclose') or price*0.99)
                        chg = ((price-prev)/prev*100)
                        return {"price": price, "prev": prev, "change": chg, "source": "MONEYCONTROL LIVE"}
            except: continue
    except: pass
    return None

def get_live_price_yahoo(symbol):
    try:
        sess = requests.Session()
        sess.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        sess.get("https://finance.yahoo.com", timeout=5)
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}.NS"
        r = sess.get(url, params={"interval": "1d", "range": "1d"}, timeout=8)
        if r.status_code == 200:
            meta = r.json()['chart']['result'][0]['meta']
            price = meta['regularMarketPrice']
            prev = meta.get('previousClose') or price
            chg = ((price-prev)/prev*100) if prev else 0
            return {"price": price, "prev": prev, "change": chg, "source": "YAHOO LIVE"}
    except: pass
    return None

def get_real_price(raw):
    s = raw.upper().strip()
    s = MAP.get(s, s)
    if s in ["LIVE", "4", "HI", "HELLO"]: return None
    data = get_live_price_moneycontrol(s)
    if not data: data = get_live_price_yahoo(s)
    if not data:
        try:
            sess = requests.Session()
            sess.headers.update({"User-Agent": "Mozilla/5.0"})
            sess.get("https://www.nseindia.com", timeout=5)
            url = f"https://www.nseindia.com/api/quote-equity?symbol={s}"
            r = sess.get(url, headers={"Referer": f"https://www.nseindia.com/get-quotes/equity?symbol={s}"}, timeout=5)
            if r.status_code == 200:
                j = r.json()
                price = j['priceInfo']['lastPrice']
                prev = j['priceInfo']['previousClose']
                chg = ((price-prev)/prev*100)
                data = {"price": price, "prev": prev, "change": chg, "source": "NSE LIVE"}
        except: pass
    return data

def make_report(symbol, data):
    if not data: return f"❌ {symbol} stock nahi hai\nSahi bhejo: RELIANCE, TCS, ONGC, AIRTEL, INFY"
    price, chg, prev, src = data['price'], data['change'], data['prev'], data['source']
    if chg > 2.5: advice, act = "🔴 Tez badha - ruk jao", "AVOID/WAIT"
    elif chg > 0.3: advice, act = "🟢 Badh raha - momentum accha", "HOLD / SIP"
    elif chg > -1.5: advice, act = "🟡 Stable - long term accha", "BUY / SIP"
    else: advice, act = "🔵 Gira hai - DIP mauka", "DIP BUY"
    txt = f"🎯 {symbol} - REAL LIVE REPORT\nSource: {src}\n━━━━━━━━━━━━━━━\nLive Price: Rs {price:.2f}\nPrev Close: Rs {prev:.2f}\nChange: {chg:+.2f}%\n\nADVICE: {advice}\nACTION: {act}\nKaha Lagana: SIP - Rs 2k x 5 baar\n\n✅ 100% real live price!\n"
    return txt

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🙏 Real Live Bot 24x7 Ready!\nAIRTEL, TCS, RELIANCE, ONGC bhejo - real price ayega!")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper().strip().split()[0].replace(".NS","")
    if len(text) < 2: return
    orig = text
    text = MAP.get(text, text)
    await update.message.reply_text(f"⏳ {orig} ka REAL LIVE price la raha hu...")
    data = get_real_price(text)
    report = make_report(orig, data)
    await update.message.reply_text(report)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Stock bhejo: AIRTEL, TCS, ONGC, RELIANCE")

if __name__ == "__main__":
    print("Starting FINAL REAL bot...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("✅ REAL LIVE READY")
    app.run_polling(drop_pending_updates=True)
