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

history = {}


def compress_text(msg):
    return msg.replace("    ", "\t").replace(" +\n", "\n")


def should_answer_message(message):
    # We do not want the bot to reply to itself
    if message.author == client.user:
        return

    if not message.content.trim().startswith("!"):
        return False

    return True


async def answer_query(message, edits=None):
    # Extract data from the discord message
    input = message.content
    extra = {"author": [message.author.name]}

    if message.attachments:
        name = message.attachments[0].filename
        data = await message.attachments[0].read()
        extra["file"] = name, data

    if edits:
        extra["edits"] = edits

    # Process the message
    answer = bot.handle_message(input, extra)

    # Prepare an answer with the result
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

        edit_info = answer.get("edits", {})

        return [], {"embed": embed}, edit_info

    args = []
    extras = {}
    if answer.get("table", None):
        rows, col_names = answer["table"]
        rows = table.prepare(rows)
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

    if "usage" in answer:
        usage = answer["usage"]

        embed.title = usage["usage"]
        embed.description = usage["description"]

        embed.add_field(name="syntax", value="```%s```" % usage["syntax"], inline=False)

        examples = usage["examples"]
        if examples:
            ex = "```%s```" % "\n".join(examples)
            embed.add_field(name="examples", value=ex, inline=False)

    for key in answer:
        if key in ["link", "file", "title", "table", "edits", "usage", "notes"]:
            continue

        value = table.prepare_value(answer[key]) or "Empty"
        embed.add_field(name=key, value=value, inline=True)

    if "notes" in answer:
        value = "\n".join(note for id, note in answer["notes"])

        embed.add_field(
            name="notes", value=value, inline=False,
        )

    if embed.fields:
        extras["embed"] = embed

    edit_info = answer["edits"]

    return args, extras, edit_info


# Send minimal message to inform the user of a critical failure
async def send_fail_message(channel, exception):
    title = "critical error"
    description = "Something went terribly wrong and the program blew up. This is a bug and it will be fixed ASAP."
    message = repr(exception)

    embed = discord.Embed(title=title, description=description, color=colors["error"])
    embed.add_field(name="error message", value=message, inline=True)

    await channel.send(embed=embed)


@client.event
async def on_message(message):
    try:
        if not should_answer_message(message):
            return

        args, extras, edit_info = await answer_query(message)
        msg = await message.channel.send(*map(compress_text, args), **extras)

        # Save some info so that what to edit later
        history[message.id] = (edit_info, msg)

    except Exception as e:
        await send_fail_message(message.channel, e)


@client.event
async def on_message_edit(before, after):
    try:
        if not should_answer_message(after):
            return

        if not before.id in history:
            print("Message has been edited, but it is not in cache - ignored.")
            return

        (edits, old_answer) = history[before.id]

        # This usually happens when the answer was an error
        if not edits:
            edits = {"type": "no-type"}

        args, extras, edit_info = await answer_query(after, edits)

        if args:
            extras["content"] = compress_text(args[0])
        else:
            extras["content"] = ""

        if extras.get("file", None):
            extras["file"] = None

        extras["embed"] = extras.get("embed", None)

        await old_answer.edit(**extras)
        history[after.id] = (edit_info, old_answer)

    except Exception as e:
        await send_fail_message(old_answer.channel, e)


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
