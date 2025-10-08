import os
import discord
from discord.ext import commands
import asyncio
import tempfile
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from obfuscator.lua_obfuscator import LuaObfuscator
from obfuscator.python_obfuscator import PythonObfuscator
from obfuscator.utils import safe_read_file, is_rate_limited, should_restart

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
WEB_SERVER_URL = os.getenv('WEB_SERVER_URL', '
https://web-production-1e3ff.up.railway.app')
STATUS_CHANNEL_ID = os.getenv('STATUS_CHANNEL_ID', '').strip()
if STATUS_CHANNEL_ID.isdigit():
    STATUS_CHANNEL_ID = int(STATUS_CHANNEL_ID)
else:
    STATUS_CHANNEL_ID = None

pending_verifications = {}

THINKING_GIF = "https://i.imgur.com/8KmK5eL.gif"
CONFETTI_GIF = "https://i.imgur.com/5KkR0aP.gif"
WARNING_GIF = "https://i.imgur.com/3Kk0e4d.gif"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

def log_request(user_id, filename, status):
    try:
        with open("obfuscation_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "filename": filename,
                "status": status
            }) + "\n")
    except:
        pass

def detect_language_from_content(code: str) -> str:
    code_sample = code[:1000].lower()
    if any(kw in code_sample for kw in ['game:', 'workspace.', 'script.', 'players.', 'replicatedstorage']):
        return '.lua'
    elif any(kw in code_sample for kw in ['import ', 'from ', 'def ', 'class ', 'print(']):
        return '.py'
    else:
        return '.lua'

async def simulate_progress(message, steps=4):
    emojis = ["🔄", "🌀", "⏳", "🛡️"]
    embed = discord.Embed(
        title=f"{emojis[0]} Obfuscating...",
        description="Preparing your protected script...",
        color=0x5865F2
    )
    embed.set_image(url=THINKING_GIF)
    progress_msg = await message.channel.send(embed=embed)
    
    for i in range(1, steps):
        await asyncio.sleep(0.8)
        new_embed = discord.Embed(
            title=f"{emojis[i % len(emojis)]} Obfuscating...",
            description="Adding anti-debug, junk code, and encryption...",
            color=0x5865F2
        )
        new_embed.set_image(url=THINKING_GIF)
        await progress_msg.edit(embed=new_embed)
    
    return progress_msg

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online with hCaptcha verification!")
    if should_restart():
        print("🔄 Weekly auto-restart triggered.")

@bot.command(name='help')
async def help_command(ctx):
    if not isinstance(ctx.channel, discord.DMChannel):
        return
    embed = discord.Embed(
        title="🛡️ KoalaHub Obfuscator — Free & Open",
        description="Protect your scripts from skids with MoonSec V3-style obfuscation.",
        color=0x5865F2
    )
    embed.add_field(
        name="📥 How to Use",
        value="1. Attach a `.lua`, `.py`, or `.txt` file\n"
              "2. Click the verification link\n"
              "3. Complete captcha → reply `done`\n"
              "4. Get your protected file!",
        inline=False
    )
    embed.add_field(
        name="✨ Features",
        value="• Roblox & Termux compatible\n"
              "• Real hCaptcha verification\n"
              "• Polymorphic, anti-debug, anti-tamper\n"
              "• No user restrictions — for everyone!",
        inline=False
    )
    embed.set_footer(text="Made with ❤️ — no greed, just great protection.")
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        return

    if message.content.startswith('!help'):
        await bot.process_commands(message)
        return

    if message.content.strip().lower() == "done":
        user_id = message.author.id
        if user_id not in pending_verifications:
            embed = discord.Embed(
                title="❌ No Active Verification",
                description="Complete the captcha first, then reply with `done`.",
                color=0xED4245
            )
            await message.channel.send(embed=embed)
            return

        attachment, filename, level, ext = pending_verifications.pop(user_id)
        progress_msg = await simulate_progress(message)

        temp_in = temp_out = None
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                temp_in = tmp.name
                await attachment.save(tmp.name)

            code = safe_read_file(temp_in)

            loop = asyncio.get_event_loop()
            if ext == '.lua':
                obfuscated = await loop.run_in_executor(None, LuaObfuscator(code, level).obfuscate)
            else:
                obfuscated = await loop.run_in_executor(None, PythonObfuscator(code, level).obfuscate)

            output_name = f"KoalaObf_{filename}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_out:
                temp_out = tmp_out.name
                tmp_out.write(obfuscated.encode('utf-8'))

            success_embed = discord.Embed(
                title="✅ Obfuscation Complete!",
                description=f"Protected with **{level}** mode.\n✅ Ready for Roblox/Termux.",
                color=0x57F287
            )
            success_embed.set_image(url=CONFETTI_GIF)
            await progress_msg.edit(embed=success_embed)
            await message.channel.send(file=discord.File(temp_out, filename=output_name))
            log_request(user_id, filename, f"SUCCESS_{level.upper()}")

        except Exception as e:
            error_embed = discord.Embed(
                title="⚠️ Error",
                description=f"```{str(e)[:500]}```",
                color=0xED4245
            )
            error_embed.set_image(url=WARNING_GIF)
            await progress_msg.edit(embed=error_embed)
            log_request(user_id, filename, "ERROR")
        finally:
            for f in [temp_in, temp_out]:
                if f and os.path.exists(f):
                    try: os.unlink(f)
                    except: pass
        return

    has_file = len(message.attachments) > 0
    if not has_file:
        embed = discord.Embed(
            title="📎 Attach a File",
            description="Please attach a `.lua`, `.py`, or `.txt` file.\nType `!help` for instructions.",
            color=0xFEE75C
        )
        await message.channel.send(embed=embed)
        return

    att = message.attachments[0]
    filename = att.filename.lower()
    if not (filename.endswith('.lua') or filename.endswith('.py') or filename.endswith('.txt')):
        embed = discord.Embed(
            title="❌ Unsupported File",
            description="Only `.lua`, `.py`, and `.txt` files are supported.",
            color=0xED4245
        )
        await message.channel.send(embed=embed)
        log_request(message.author.id, filename, "INVALID_EXTENSION")
        return

    if is_rate_limited(message.author.id, 5):
        embed = discord.Embed(
            title="⏳ Rate Limited",
            description="Max 5 requests/hour to keep the bot fair for everyone. Thanks for understanding! ❤️",
            color=0xFEE75C
        )
        await message.channel.send(embed=embed)
        return

    content_msg = message.content.lower()
    level = "hard" if "hard" in content_msg else ("easy" if "easy" in content_msg else "hard")
    
    ext = os.path.splitext(filename)[1]
    if ext == '.txt':
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                temp_path = tmp.name
                await att.save(tmp.name)
            code_sample = safe_read_file(temp_path)[:2000]
            ext = detect_language_from_content(code_sample)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

    verify_url = f"{WEB_SERVER_URL}/verify/{message.author.id}"
    embed = discord.Embed(
        title="🔒 Human Verification Required",
        description="To prevent abuse, please verify you're not a bot:",
        color=0x5865F2
    )
    embed.add_field(
        name="✅ How to Verify",
        value=f"[Click here to verify]({verify_url})\nAfter completing, reply with **`done`**.",
        inline=False
    )
    embed.set_image(url=THINKING_GIF)
    embed.set_footer(text="Verification expires in 2 minutes.")
    await message.channel.send(embed=embed)

    pending_verifications[message.author.id] = (att, filename, level, ext)

    async def cleanup():
        await asyncio.sleep(120)
        if message.author.id in pending_verifications:
            del pending_verifications[message.author.id]
    bot.loop.create_task(cleanup())

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("❌ DISCORD_TOKEN missing in .env")

    bot.run(TOKEN)

