import os
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

    answer = bot.handle_message(arc, input)

    if answer:
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
