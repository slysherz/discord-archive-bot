import os
import io
import archive_bot
import archive
import discord
import table

# Get secret token from an environment variable
token = os.getenv("BOT_TOKEN")
assert token, "Environment variable BOT_TOKEN must be defined"

arc = archive.Archive("test.db")
bot = archive_bot.ArchiveBot(arc)
client = discord.Client()

colors = {"error": 0xFF0000}


# This has a really big bug
def corresponding_answer(message):
    cached = client.cached_messages

    for i in range(len(cached) - 1, -1, -1):
        if message == cached[i] and i + 1 < len(cached):
            answer = cached[i + 1]

            if answer.author != client.user:
                return

            return answer


async def answer_query(message, edits=None):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    input = message.content
    extra = {}

    if message.attachments:
        name = message.attachments[0].filename
        data = await message.attachments[0].read()
        extra["file"] = name, data

    if edits:
        extra["edits"] = edits.content

    answer = bot.handle_message(input, extra)

    if "error" in answer:
        embed = discord.Embed(
            title="error", description=answer["error"], color=colors["error"]
        )

        if "usage" in answer:
            usage = answer["usage"]

            embed.add_field(name="syntax", value=usage["syntax"], inline=False)

            examples = usage["examples"]
            if examples:
                ex = "```%s```" % "\n".join(examples)
                embed.add_field(name="examples", value=ex, inline=False)

        return [], {"extras": embed}

    args = []
    extras = {}
    if answer.get("table", None):
        rows, col_names = answer["table"]
        args.append("```%s```" % table.tabulate(rows, 150, col_names))

    if answer.get("file", None):
        name, data = answer["file"]

        extras["file"] = discord.File(io.BytesIO(data), filename=name)

    if answer.get("link", None):
        args.append(answer["link"])

    embed_extras = {}
    if answer.get("name", None):
        embed_extras["title"] = answer["name"]

    embed = discord.Embed(**embed_extras)

    for key in answer:
        if key in ["link", "file", "title", "table"]:
            continue

        embed.add_field(name=key, value=str(answer[key]), inline=True)

    if embed.fields:
    extras["embed"] = embed

    return args, extras


@client.event
async def on_message(message):
    answer = await answer_query(message)

    if answer:
        args, extras = answer
        await message.channel.send(*args, **extras)


@client.event
async def on_message_edit(before, after):
    print("message update: ", before, after)
    old_answer = corresponding_answer(after)

    if not old_answer:
        return

    answer = await answer_query(after)

    if answer:
        args, extras = answer

        if args:
            extras["content"] = args[0]
        else:
            extras["content"] = ""

        if extras.get("file", None):
            extras["file"] = None

        await old_answer.edit(**extras)


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
