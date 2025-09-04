# Aditya Singh - Telegram AI Bot (All-in-one)

This repo contains an All-in-One Telegram Bot + Web Chat UI.
Owner: Aditya Singh

## Features (All included)
- AI Chat (OpenRouter)
- Wikipedia search
- Weather (OpenWeather)
- Notes save/list
- Text-to-Speech (gTTS)
- PDF generator (fpdf)
- Image generation (Pollinations)
- Meme generator (memegen.link)
- Image upload + ask about image (Telegram + Web)
- Web Chat UI (Flask) using same AI backend
- Commands menu for Telegram (slash command list)

## Setup (Railway)
1. Upload this ZIP to Railway (New Project -> Upload ZIP) or push to GitHub and deploy.
2. Add Railway Variables (Secrets):
   - BOT_TOKEN
   - OPENROUTER_API_KEY
   - OPENWEATHER_API_KEY (optional)
   - RAILWAY_BASE_URL (optional)
3. Deploy and check logs.
4. Visit the Railway app URL for the web chat UI, and use the Telegram bot token to chat on Telegram.

## Notes
- Keep API keys secret. Do not commit actual .env.
- If you see `executor` import errors, ensure aiogram==2.25.1 in requirements.txt.
