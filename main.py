\
"""Full All-in-One Telegram + Website AI Bot
Owner: Aditya Singh
DO NOT add secrets inside this file. Use environment variables.
Required env vars: BOT_TOKEN, OPENROUTER_API_KEY, OPENWEATHER_API_KEY (optional), RAILWAY_BASE_URL (optional)
"""
import os
import io
import json
import time
import logging
import asyncio
from pathlib import Path
from urllib.parse import quote_plus

import requests
import wikipedia
from gtts import gTTS
from fpdf import FPDF

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

from flask import Flask, request, send_from_directory, render_template, jsonify

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
RAILWAY_BASE_URL = os.getenv("RAILWAY_BASE_URL", "")

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise Exception("Set BOT_TOKEN and OPENROUTER_API_KEY in environment variables.")

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
NOTES_FILE = DATA_DIR / "notes.json"
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
if not NOTES_FILE.exists():
    NOTES_FILE.write_text(json.dumps([]))

# Bot & Flask setup
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
app = Flask(__name__, template_folder="templates", static_folder="static")

# Helpers
def load_notes():
    try:
        return json.loads(NOTES_FILE.read_text(encoding="utf-8"))
    except:
        return []

def save_notes(notes):
    NOTES_FILE.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")

def make_public_file_url(filename, host_url=None):
    base = RAILWAY_BASE_URL.rstrip("/") if RAILWAY_BASE_URL else (host_url.rstrip("/") if host_url else "")
    if not base:
        return f"/files/{filename}"
    return f"{base}/files/{quote_plus(filename)}"

def call_openrouter_ai_sync(prompt):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        payload = {"model":"openai/gpt-3.5-turbo","messages":[{"role":"user","content":prompt}],"max_tokens":800}
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        # defensive checks
        if "choices" in data and len(data["choices"])>0 and "message" in data["choices"][0]:
            return data["choices"][0]["message"].get("content","").strip()
        return str(data)
    except Exception as e:
        logger.exception("OpenRouter error")
        return f"⚠️ AI error: {str(e)}"

async def call_openrouter_ai(prompt):
    return await asyncio.get_event_loop().run_in_executor(None, call_openrouter_ai_sync, prompt)

# Utilities
def generate_image_url(prompt):
    return f"https://image.pollinations.ai/prompt/{quote_plus(prompt)}"

def generate_meme_url(text):
    safe = text.replace(" ", "_")
    return f"https://api.memegen.link/images/custom/_/{safe}.png?background=https://i.imgur.com/8KcYpGf.png"

def text_to_speech_file(text, lang="en"):
    try:
        tts = gTTS(text=text, lang=lang)
        fname = f"{int(time.time())}_tts.mp3"
        path = UPLOADS_DIR / fname
        tts.save(str(path))
        return str(path)
    except Exception as e:
        logger.exception("TTS failed")
        return None

def make_pdf_from_text(text, filename=None):
    try:
        if not filename:
            filename = f"{int(time.time())}_doc.pdf"
        path = DATA_DIR / filename
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", size=12)
        for line in text.split("\n"):
            pdf.multi_cell(0, 6, line)
        pdf.output(str(path))
        return str(path)
    except Exception as e:
        logger.exception("PDF creation failed")
        return None

# Telegram Handlers - Commands
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.reply("👋 Hello! I'm Aditya Singh's All-in-One AI Bot.\nUse commands or chat directly!")

@dp.message_handler(commands=["help"])
async def cmd_help(message: types.Message):
    await message.reply("Commands: /ai, /wiki, /weather, /image, /meme, /tts, /pdf, /note, /notes, or just chat directly.")

@dp.message_handler(commands=["ai"])
async def cmd_ai(message: types.Message):
    query = message.get_args()
    if not query:
        await message.reply("Usage: /ai <your question>")
        return
    await message.reply("⏳ Thinking...")
    res = await call_openrouter_ai(query)
    await message.reply(res)

@dp.message_handler(commands=["wiki"])
async def cmd_wiki(message: types.Message):
    q = message.get_args()
    if not q:
        await message.reply("Usage: /wiki <topic>")
        return
    try:
        s = wikipedia.summary(q, sentences=3)
        await message.reply(s)
    except Exception:
        await message.reply("❌ Couldn't find on Wikipedia.")

@dp.message_handler(commands=["weather"])
async def cmd_weather(message: types.Message):
    city = message.get_args()
    if not city:
        await message.reply("Usage: /weather <city>")
        return
    if not OPENWEATHER_API_KEY:
        await message.reply("Weather API key not configured.")
        return
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={quote_plus(city)}&appid={OPENWEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=10).json()
        if r.get("cod") != 200:
            await message.reply("City not found.")
            return
        text = f"🌤 Weather in {city}:\n🌡 {r['main']['temp']}°C\n💧 Humidity: {r['main']['humidity']}%\n{r['weather'][0]['description']}"
        await message.reply(text)
    except Exception as e:
        logger.exception("Weather error")
        await message.reply("Weather fetch error.")

@dp.message_handler(commands=["image"])
async def cmd_image(message: types.Message):
    prompt = message.get_args()
    if not prompt:
        await message.reply("Usage: /image <prompt>")
        return
    url = generate_image_url(prompt)
    await message.reply_photo(url, caption=f"Image for: {prompt}")

@dp.message_handler(commands=["meme"])
async def cmd_meme(message: types.Message):
    text = message.get_args()
    if not text:
        await message.reply("Usage: /meme <text>")
        return
    url = generate_meme_url(text)
    await message.reply_photo(url, caption=f"Meme: {text}")

@dp.message_handler(commands=["tts"])
async def cmd_tts(message: types.Message):
    text = message.get_args()
    if not text:
        await message.reply("Usage: /tts <text>")
        return
    path = await asyncio.get_event_loop().run_in_executor(None, text_to_speech_file, text)
    if path:
        await message.reply_audio(open(path, "rb"))
        try:
            os.remove(path)
        except: pass
    else:
        await message.reply("TTS failed.")

@dp.message_handler(commands=["pdf"])
async def cmd_pdf(message: types.Message):
    text = message.get_args()
    if not text:
        await message.reply("Usage: /pdf <text to convert to pdf>")
        return
    path = await asyncio.get_event_loop().run_in_executor(None, make_pdf_from_text, text)
    if path:
        await message.reply_document(open(path, "rb"))
        try: os.remove(path)
        except: pass
    else:
        await message.reply("PDF creation failed.")

@dp.message_handler(commands=["note"])
async def cmd_note(message: types.Message):
    args = message.get_args()
    notes = load_notes()
    if not args:
        if not notes:
            await message.reply("No notes yet.")
        else:
            msg = "\n".join([f"{i+1}. {t}" for i,t in enumerate(notes)])
            await message.reply(msg)
        return
    notes.append(args)
    save_notes(notes)
    await message.reply("✅ Note saved.")

@dp.message_handler(commands=["notes"])
async def cmd_notes(message: types.Message):
    notes = load_notes()
    if not notes:
        await message.reply("No notes yet.")
        return
    msg = "\n".join([f"{i+1}. {t}" for i,t in enumerate(notes)])
    await message.reply(msg)

# Photo upload handler
@dp.message_handler(content_types=['photo'])
async def handle_photo(message: types.Message):
    try:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        data = await bot.download_file(file.file_path)
        fname = f"{int(time.time())}_tg.jpg"
        path = UPLOADS_DIR / fname
        with open(path, "wb") as f:
            f.write(data.read())
        await message.reply(f"Image received and saved. To ask about it, type:\nimg:{fname} <your question>\n(example: img:{fname} What is in this picture?)")
    except Exception as e:
        logger.exception("photo save error")
        await message.reply("Failed to save image.")

# Text handler - image questions and direct chat
@dp.message_handler()
async def handle_text(message: types.Message):
    text = message.text.strip()
    if text.startswith("/"):
        return
    if text.startswith("img:"):
        parts = text.split(maxsplit=1)
        fname = parts[0][4:]
        question = parts[1] if len(parts)>1 else ""
        if not question:
            await message.reply("Please add your question after image filename.")
            return
        host = ""  # host not available here; web uses host_url
        image_url = make_public_file_url(fname, host_url=host)
        prompt = f"User question about image: {question}\nImage URL: {image_url}\nPlease describe and answer based on the image."
        await message.reply("⏳ Analyzing the image and answering...")
        resp = await call_openrouter_ai(prompt)
        await message.reply(resp)
        return
    await message.reply("⏳ Thinking...")
    resp = await call_openrouter_ai(text)
    await message.reply(resp)

# Set commands (so slash menu shows)
async def set_commands():
    cmds = [
        types.BotCommand("start","Start the bot"),
        types.BotCommand("help","Help"),
        types.BotCommand("ai","Chat with AI"),
        types.BotCommand("wiki","Search Wikipedia"),
        types.BotCommand("weather","Weather info"),
        types.BotCommand("image","Generate Image"),
        types.BotCommand("meme","Make Meme"),
        types.BotCommand("tts","Text to Speech"),
        types.BotCommand("pdf","Text -> PDF"),
        types.BotCommand("note","Save Note"),
        types.BotCommand("notes","Show Notes")
    ]
    await bot.set_my_commands(cmds)

# Flask web UI (templates/static provided)
CHAT_HTML = None  # use template file

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/webchat", methods=["POST"])
def webchat():
    data = request.get_json(silent=True) or {}
    text = data.get("text","").strip()
    if not text:
        return jsonify({"reply":"Send some text."})
    if text.startswith("img:"):
        parts = text.split(maxsplit=1)
        fname = parts[0][4:]
        question = parts[1] if len(parts)>1 else ""
        if not question:
            return jsonify({"reply":"Please include question after image filename."})
        host = request.host_url.rstrip("/")
        image_url = make_public_file_url(fname, host_url=host)
        prompt = f"User asks about image: {question}\nImage URL: {image_url}\nDescribe and answer based on image."
        reply = call_openrouter_ai_sync(prompt)
        return jsonify({"reply": reply})
    reply = call_openrouter_ai_sync(text)
    return jsonify({"reply": reply})

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"ok":False,"error":"No file"})
    f = request.files['file']
    fname = f"{int(time.time())}_{f.filename}"
    path = UPLOADS_DIR / fname
    f.save(path)
    host = request.host_url.rstrip("/")
    public = make_public_file_url(fname, host_url=host)
    return jsonify({"ok":True,"filename": fname, "url": public})

@app.route("/files/<path:filename>")
def serve_file(filename):
    return send_from_directory(str(UPLOADS_DIR), filename, as_attachment=False)

# Run both Flask and Telegram bot
def start_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_commands())
    import threading
    t = threading.Thread(target=start_flask, daemon=True)
    t.start()
    executor.start_polling(dp, skip_updates=True)
