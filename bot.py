from telegram.ext import Application, CommandHandler
import requests

TOKEN = "8404307247:AAE3zP7rhltmTmNiG_yCNELAIGxVYIWRXRk"

# Flask endpoints mapping
APPS = {
    "app1": "http://fi9.bot-hosting.net:21504/",
    "app2": "fi3.bot-hosting.net:22825",
    "app3": "http://fi3.bot-hosting.net:21833/",
    "app4": "http://65.108.103.151:22688/",
    "app5": "SOON",
}

async def start(update, context):
    await update.message.reply_text("Hello! Use /app1, /app2, /app3, /app4, /app5")

async def call_api(update, context, app_key):
    try:
        url = APPS[app_key]
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            await update.message.reply_text(f"{data}")
        else:
            await update.message.reply_text("❌ Flask se error aayi")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# wrappers for commands
async def app1(update, context): await call_api(update, context, "app1")
async def app2(update, context): await call_api(update, context, "app2")
async def app3(update, context): await call_api(update, context, "app3")
async def app4(update, context): await call_api(update, context, "app4")
async def app5(update, context): await call_api(update, context, "app5")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("app1", app1))
    app.add_handler(CommandHandler("app2", app2))
    app.add_handler(CommandHandler("app3", app3))
    app.add_handler(CommandHandler("app4", app4))
    app.add_handler(CommandHandler("app5", app5))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
