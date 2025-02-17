import os
from datetime import datetime
from pathlib import Path

import requests

from ..Config import Config
from ..utils import load_module, remove_plugin
from . import (
    CMD_HELP,
    CMD_LIST,
    SUDO_LIST,
    catub,
    edit_delete,
    edit_or_reply,
    hmention,
    reply_id,
)

plugin_category = "tools"

DELETE_TIMEOUT = 5
thumb_image_path = os.path.join(Config.TMP_DOWNLOAD_DIRECTORY, "thumb_image.jpg")


@catub.cat_cmd(
    pattern="(install|i)$",
    command=("install", plugin_category),
    info={
        "header": "To install an external plugin.",
        "description": "Reply to any external plugin(supported by cat) to install it in your bot.",
        "usage": "{tr}install\n{tr}i",
    },
)
async def install(event):
    "To install an external plugin."
    if event.reply_to_msg_id:
        try:
            downloaded_file_name = await event.client.download_media(
                await event.get_reply_message(),
                "userbot/plugins/",
            )
            if "(" not in downloaded_file_name:
                path1 = Path(downloaded_file_name)
                shortname = path1.stem
                load_module(shortname.replace(".py", ""))
                await edit_delete(
                    event,
                    f"**Iɴsᴛᴀʟʟᴇᴅ Pʟᴜɢɪɴ** `{os.path.basename(downloaded_file_name)}`",
                    10,
                )
            else:
                os.remove(downloaded_file_name)
                await edit_delete(
                    event, "Errors! This plugin is already installed/pre-installed.", 10
                )
        except Exception as e:
            await edit_delete(event, f"**Error :**\n`{e}`", 10)
            os.remove(downloaded_file_name)


@catub.cat_cmd(
    pattern="load ([\s\S]*)",
    command=("load", plugin_category),
    info={
        "header": "To load a plugin again. if you have unloaded it",
        "description": "To load a plugin again which you unloaded by {tr}unload",
        "usage": "{tr}load <plugin name>",
        "examples": "{tr}load markdown",
    },
)
async def load(event):
    "To load a plugin again. if you have unloaded it"
    shortname = event.pattern_match.group(1)
    try:
        try:
            remove_plugin(shortname)
        except BaseException:
            pass
        load_module(shortname)
        await edit_delete(event, f"`Successfully loaded {shortname}`", 10)
    except Exception as e:
        await edit_delete(
            event,
            f"Could not load {shortname} because of the following error.\n{e}",
            10,
        )


@catub.cat_cmd(
    pattern="send ([\s\S]*)",
    command=("send", plugin_category),
    info={
        "header": "To upload a plugin file to telegram chat",
        "usage": "{tr}send <plugin name>",
        "examples": "{tr}send markdown",
    },
)
async def send(event):
    "To uplaod a plugin file to telegram chat"
    reply_to_id = await reply_id(event)
    thumb = thumb_image_path if os.path.exists(thumb_image_path) else None
    input_str = event.pattern_match.group(1)
    the_plugin_file = f"./userbot/plugins/{input_str}.py"
    repo_link = os.environ.get("UPSTREAM_REPO")
    if repo_link == "goodcat":
        repo_link = "https://github.com/sandy1709/catuserbot"
    if repo_link == "badcat":
        repo_link = "https://github.com/Jisan09/catuserbot"
    repo_branch = os.environ.get("UPSTREAM_REPO_BRANCH") or "master"
    git_link = f"<a href= {repo_link}/blob/{repo_branch}/userbot/plugins/{input_str}.py>GitHub</a>"
    raw_link = (
        f"<a href= {repo_link}/raw/{repo_branch}/userbot/plugins/{input_str}.py>Raw</a>"
    )
    if os.path.exists(the_plugin_file):
        datetime.now()
        caat = await event.client.send_file(
            event.chat_id,
            the_plugin_file,
            force_document=True,
            allow_cache=False,
            reply_to=reply_to_id,
            thumb=thumb,
            parse_mode="html",
            caption=f"""
<b>〣 Plugin Name:- {input_str}
〣 Raw Text:- {raw_link} | {git_link}
〣 Uploaded by {hmention}</b>""",
        )
        await event.delete()

    else:
        await edit_delete(event, "**404: File Not Found**")


@catub.cat_cmd(
    pattern="unload ([\s\S]*)",
    command=("unload", plugin_category),
    info={
        "header": "To unload a plugin temporarily.",
        "description": "You can load this unloaded plugin by restarting or using {tr}load cmd. Useful for cases like seting notes in rose bot({tr}unload markdown).",
        "usage": "{tr}unload <plugin name>",
        "examples": "{tr}unload markdown",
    },
)
async def unload(event):
    "To unload a plugin temporarily."
    shortname = event.pattern_match.group(1)
    path = Path(f"userbot/plugins/{shortname}.py")
    if not os.path.exists(path):
        return await edit_delete(event, f"**There's no such Plugin**")
    try:
        remove_plugin(shortname)
        await edit_delete(event, f"**Uɴʟᴏᴀᴅᴇᴅ** `{shortname}` **Sᴜᴄᴄᴇssғᴜʟʟʏ.**", 10)
    except Exception as e:
        await edit_delete(event, f"Error with {shortname}: \n`{e}`", 10)


@catub.cat_cmd(
    pattern="(uninstall|ui) ([\s\S]*)",
    command=("uninstall", plugin_category),
    info={
        "header": "To uninstall a plugin temporarily.",
        "description": "To stop functioning of that plugin and remove that plugin from bot.",
        "note": "To unload a plugin permanently from bot set NO_LOAD var in heroku with that plugin name, give space between plugin names if more than 1.",
        "usage": "{tr}uninstall <plugin name>\n{tr}ui <plugin name>",
        "examples": "{tr}uninstall markdown",
    },
)
async def unload(event):
    "To uninstall a plugin."
    shortname = event.pattern_match.group(2)
    path = Path(f"userbot/plugins/{shortname}.py")
    if not os.path.exists(path):
        return await edit_delete(
            event, f"There is no plugin with path {path} to uninstall it"
        )
    os.remove(path)
    if shortname in CMD_LIST:
        CMD_LIST.pop(shortname)
    if shortname in SUDO_LIST:
        SUDO_LIST.pop(shortname)
    if shortname in CMD_HELP:
        CMD_HELP.pop(shortname)
    try:
        remove_plugin(shortname)
        await edit_delete(event, f"**{shortname} Is Uɴɪɴsᴛᴀʟʟᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ**", 10)
    except Exception as e:
        await edit_delete(event, f"Error bruh :\n`{e}`", 10)


@catub.cat_cmd(
    pattern="getad ([\s\S]*)",
    command=("getad", plugin_category),
    info={
        "header": "To install a plugin from github raw link.",
        "description": "Install plugin from github raw link. ",
        "usage": "{tr}getad <raw link>",
    },
)
async def get_the_addons(event):
    link = event.pattern_match.group(1)
    xx = await edit_or_reply(event, "`Processing...`")
    msg = "`Give raw link or Die!`"
    if link is None:
        return await edit_delete(xx, msg)
    split_link = link.split("/")
    if "raw" not in link:
        return await edit_delete(xx, msg)
    name = split_link[(len(split_link) - 1)]
    plug = requests.get(link).text
    fil = f"userbot/plugins/{name}"
    with open(fil, "w", encoding="utf-8") as pepe:
        pepe.write(plug)
    shortname = name.split(".")[0]
    try:
        load_module(shortname)
        await edit_delete(xx, "**Sᴜᴄᴄᴇssғᴜʟʟʏ Lᴏᴀᴅᴇᴅ** `{}`".format(shortname), 10)
    except Exception:
        await edit_delete(xx, "Error with {shortname}\n`{e}`")
