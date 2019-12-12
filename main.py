import os
import io
import archive_bot
import archive
import discord

# Get secret token from an environment variable
token = os.getenv("BOT_TOKEN")
assert token, "Environment variable BOT_TOKEN must be defined"

arc = archive.Archive("test.db")
bot = archive_bot.ArchiveBot(arc)
client = discord.Client()

colors = {"error": 0xFF0000}


@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    input = message.content
    extra = {}

    if message.attachments:
        name = message.attachments[0].filename
        data = await message.attachments[0].read()
        extra["file"] = name, data

    answer = bot.handle_message(input, extra)

    if "error" in answer:
        embed = discord.Embed(
            title="error", description=answer["error"], color=colors["error"]
        )

        return await message.channel.send(embed=embed)

    args = []
    extras = {}
    if answer.get("file", None):
        name, data = answer["file"]

        extras["file"] = discord.File(io.BytesIO(data), filename=name)

    embed_extras = {}
    if answer.get("link", None):
        args.append(answer["link"])

    if answer.get("name", None):
        embed_extras["title"] = answer["name"]

    embed = discord.Embed(**embed_extras)

    for key in answer:
        if key in ["link", "file", "title"]:
            continue

        embed.add_field(name=key, value=str(answer[key]), inline=True)

    extras["embed"] = embed
    return await message.channel.send(*args, **extras)


@client.event
async def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------")


# Start the bot. We can comment this out to run commands manually
client.run(token)

# Run commands manually
# bot.handle_message(arc, "!add examplelink tags:[id, tags, link]")
# print("ENTRY: ", bot.handle_message(arc, "!get 1 [id, link, tags]"))
