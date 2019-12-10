import os
import io
import bot
import archive
import discord

# Get secret token from an environment variable
token = os.getenv("BOT_TOKEN")
assert token, "Environment variable BOT_TOKEN must be defined"

arc = archive.Archive("test.db")
client = discord.Client()


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

    answer = bot.handle_message(arc, input, extra)

    if isinstance(answer, tuple):
        text, extra = answer

        assert "file" in extra
        name, data = extra["file"]

        attach = discord.File(io.BytesIO(data), filename=name)

        await message.channel.send(text, file=attach)

    elif answer:
        print("ANSWER:", answer)
        await message.channel.send(answer)


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
