import nekos

from userbot import catub

from ..core.managers import edit_or_reply

plugin_category = "fun"


@catub.cat_cmd(
    pattern="tcat$",
    command=("tcat", plugin_category),
    info={
        "header": "Some random cat facial text art",
        "usage": "{tr}tcat",
    },
)
async def hmm(cat):
    "Some random cat facial text art"
    reactcat = nekos.textcat()
    await edit_or_reply(cat, reactcat)


@catub.cat_cmd(
    pattern="why$",
    command=("why", plugin_category),
    info={
        "header": "Sends you some random Funny questions",
        "usage": "{tr}why",
    },
)
async def hmm(cat):
    "Some random Funny questions"
    whycat = nekos.why()
    await edit_or_reply(cat, whycat)


@catub.cat_cmd(
    pattern="fact$",
    command=("fact", plugin_category),
    info={
        "header": "Sends you some random facts",
        "usage": "{tr}fact",
    },
)
async def hmm(cat):
    "Some random facts"
    factcat = nekos.fact()
    await edit_or_reply(cat, f"`{factcat}`")


@catub.cat_cmd(
    pattern="uwu ?(.*)",
    command=("uwu", plugin_category),
    info={
        "header": "OwOify text",
        "usage": "{tr}uwu <text>",
    },
)
async def uwu(cat):
    "UwU"
    textx = await cat.get_reply_message()
    message = cat.pattern_match.group(1)
    if message:
        pass
    elif textx:
        message = textx.text
    else:
        await edit_or_reply(cat, "`Give some text to owoify`")
        return
    kk = nekos.owoify(f"{message}")
    await edit_or_reply(cat, f"`{kk}`")
