# Modified by @sandeep and @kirito6969

import html
import os
import re
import textwrap
from datetime import datetime
from urllib.parse import quote_plus

import aiohttp
import bs4
import jikanpy
import requests
from jikanpy import Jikan
from jikanpy.exceptions import APIException
from pySmartDL import SmartDL
from telegraph import exceptions, upload_file

from userbot import catub

from ..core.managers import edit_delete, edit_or_reply
from ..helpers import media_type, readable_time, time_formatter
from ..helpers.functions import (
    airing_query,
    anilist_user,
    callAPI,
    formatJSON,
    get_anime_manga,
    get_anime_schedule,
    get_filler_episodes,
    get_poster,
    getBannerLink,
    memory_file,
    replace_text,
    search_in_animefiller,
    weekdays,
)
from ..helpers.tools import post_to_telegraph
from ..helpers.utils import _cattools, reply_id

jikan = Jikan()

anilistapiurl = "https://graphql.anilist.co"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36"
}

ppath = os.path.join(os.getcwd(), "temp", "anilistuser.jpg")
anime_path = os.path.join(os.getcwd(), "temp", "animeresult.jpg")

plugin_category = "extra"


@catub.cat_cmd(
    pattern="aq$",
    command=("aq", plugin_category),
    info={
        "header": "Get random Anime quotes.",
        "usage": "{tr}aq",
        "examples": "{tr}aq",
    },
)
async def anime_quote(event):
    "Get random anime quotes"
    data = requests.get("https://animechan.vercel.app/api/random").json()
    anime = data["anime"]
    character = data["character"]
    quote = data["quote"]
    await edit_or_reply(
        event,
        f"❅ <b><u>Anime:</b></u>\n ➥ <code>{anime}</code>\n\n❅ <b><u>Character:</b></u>\n ➥ <code>{character}</code>\n\n❅ <b><u>Quote:</u></b>\n ➥ <code>{quote}</code>",
        parse_mode="html",
    )


@catub.cat_cmd(
    pattern="aluser(?:\s|$)([\s\S]*)",
    command=("aluser", plugin_category),
    info={
        "header": "Search User profiles in anilist.",
        "usage": "{tr}aluser <username>",
        "examples": "{tr}aluser Infinity20998",
    },
)
async def anilist_usersearch(event):
    "Search user profiles of Anilist."
    search_query = event.pattern_match.group(1)
    reply_to = await reply_id(event)
    reply = await event.get_reply_message()
    if not search_query:
        if reply and reply.text:
            search_query = reply.text
        else:
            return await edit_delete(event, "__Whom should i search.__")
    catevent = await edit_or_reply(event, "`Searching user profile in anilist...`")
    searchresult = await anilist_user(search_query)
    if len(searchresult) == 1:
        return await edit_or_reply(
            catevent, f"**Error while searching user profile:**\n{searchresult[0]}"
        )
    downloader = SmartDL(searchresult[1], ppath, progress_bar=False)
    downloader.start(blocking=False)
    while not downloader.isFinished():
        pass
    await event.client.send_file(
        event.chat_id,
        ppath,
        caption=searchresult[0],
        reply_to=reply_to,
    )
    os.remove(ppath)
    await catevent.delete()


@catub.cat_cmd(
    pattern="mal(?:\s|$)([\s\S]*)",
    command=("mal", plugin_category),
    info={
        "header": "Search profiles of MAL.",
        "usage": "{tr}mal <username>",
        "examples": "{tr}mal Infinity20998",
    },
)
async def user(event):
    "Search profiles of MAL."
    search_query = event.pattern_match.group(1)
    replyto = await reply_id(event)
    reply = await event.get_reply_message()
    if not search_query and reply and reply.text:
        search_query = reply.text
    elif not search_query:
        return await edit_delete(event, "__Whom should i search.__")
    try:
        user = jikan.user(search_query)
    except APIException:
        return await edit_delete(event, "__No User found with given username__", 5)
    date_format = "%Y-%m-%d"
    img = user["image_url"] or "https://telegra.ph//file/9b4205e1b1cc68a4ffd5e.jpg"
    try:
        user_birthday = datetime.fromisoformat(user["birthday"])
        user_birthday_formatted = user_birthday.strftime(date_format)
    except BaseException:
        user_birthday_formatted = "Unknown"
    user_joined_date = datetime.fromisoformat(user["joined"])
    user_joined_date_formatted = user_joined_date.strftime(date_format)
    user_last_online = datetime.fromisoformat(user["last_online"])
    user_last_online_formatted = user_last_online.strftime(date_format)
    for entity in user:
        if user[entity] is None:
            user[entity] = "Unknown"
    about = user["about"].split(" ", 60)
    try:
        about.pop(60)
    except IndexError:
        pass
    about_string = " ".join(about)
    about_string = about_string.replace("<br>", "").strip().replace("\r\n", "\n")
    caption = ""
    caption += textwrap.dedent(
        f"""
    **Username:** [{user['username']}]({user['url']})
    **Gender:** `{user['gender']}`
    **MAL ID:** `{user['user_id']}`
    **Birthday:** `{user_birthday_formatted}`
    **Joined:** `{user_joined_date_formatted}`
    **Last Online:** `{user_last_online_formatted}`
    
    **Days wasted watching Anime:** `{user['anime_stats']['days_watched']} days`
    **No of completed Animes:** `{user['anime_stats']['completed']}`
    **Total No of episodes Watched:** `{user['anime_stats']['episodes_watched']}`
    **Days wasted reading Manga:** `{user['manga_stats']['days_read']}`
    """
    )

    caption += f"**About:** __{about_string}__"
    await event.client.send_file(
        event.chat_id, file=img, caption=caption, reply_to=replyto
    )
    await event.delete()


@catub.cat_cmd(
    pattern="airing(?:\s|$)([\s\S]*)",
    command=("airing", plugin_category),
    info={
        "header": "Shows you the time left for the new episode of current running anime show.",
        "usage": "{tr}airing",
        "examples": "{tr}airing one piece",
    },
)
async def anilist(event):
    "Get airing date & time of any anime"
    search = event.pattern_match.group(1)
    if not search:
        return await edit_delete(event, "__which anime results should i fetch__")
    variables = {"search": search}
    response = requests.post(
        anilistapiurl, json={"query": airing_query, "variables": variables}
    ).json()["data"]["Media"]
    if response is None:
        return await edit_delete(event, "__Unable to find the anime.__")
    ms_g = f"**Name**: **{response['title']['romaji']}**(`{response['title']['native']}`)\n**ID**: `{response['id']}`"
    if response["nextAiringEpisode"]:
        airing_time = response["nextAiringEpisode"]["timeUntilAiring"]
        airing_time_final = time_formatter(airing_time)
        airing_at = response["nextAiringEpisode"]["airingAt"]
        ms_g += f"\n**Episode**: `{response['nextAiringEpisode']['episode']}`\n**Airing In**: `{airing_time_final}`\n**Time: **`{datetime.fromtimestamp(airing_at)}`"
    else:
        ms_g += f"\n**Episode**:{response['episodes']}\n**Status**: `N/A`"
    await edit_or_reply(event, ms_g)


@catub.cat_cmd(
    pattern="ianime(?:\s|$)([\s\S]*)",
    command=("ianime", plugin_category),
    info={
        "header": "Shows you the details of the anime.",
        "description": "Fectchs anime information from anilist",
        "usage": "{tr}ianime <name of anime>",
        "examples": "{tr}ianime fairy tail",
    },
)
async def anilist(event):
    "Get info on any anime."
    input_str = event.pattern_match.group(1)
    if not input_str:
        return await edit_delete(
            event, "__What should i search ? Gib me Something to Search__"
        )
    event = await edit_or_reply(event, "`Searching...`")
    result = await callAPI(input_str)
    msg = await formatJSON(result)
    await event.edit(msg, link_preview=True)


@catub.cat_cmd(
    pattern="manga(?:\s|$)([\s\S]*)",
    command=("manga", plugin_category),
    info={
        "header": "Search your favourite manga.",
        "usage": "{tr}manga <manga name",
        "examples": "{tr}manga fairy tail",
    },
)
async def get_manga(event):
    "searches for manga."
    reply_to = await reply_id(event)
    input_str = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not input_str:
        if reply:
            input_str = reply.text
        else:
            return await edit_delete(
                event, "__What should i search ? Gib me Something to Search__"
            )
    catevent = await edit_or_reply(event, "`Searching Manga..`")
    jikan = jikanpy.jikan.Jikan()
    search_result = jikan.search("manga", input_str)
    first_mal_id = search_result["results"][0]["mal_id"]
    caption, image = await get_anime_manga(first_mal_id, "anime_manga", event.chat_id)
    await catevent.delete()
    await event.client.send_file(
        event.chat_id, file=image, caption=caption, parse_mode="html", reply_to=reply_to
    )


@catub.cat_cmd(
    pattern="fillers(?:\s|$)([\s\S]*)",
    command=("fillers", plugin_category),
    info={
        "header": "To get list of filler episodes.",
        "flags": {
            "-n": "If more than one name have same common word then to select required anime"
        },
        "usage": ["{tr}fillers <anime name>", "{tr}fillers -n<number> <anime name>"],
        "examples": [
            "{tr}fillers one piece",
            "{tr}fillers -n5 naruto",
        ],
    },
)
async def get_anime(event):
    "to get list of filler episodes."
    input_str = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not input_str:
        if reply:
            input_str = reply.text
        else:
            return await edit_delete(
                event, "__What should i search ? Gib me Something to Search__"
            )
    anime = re.findall(r"-n\d+", input_str)
    try:
        anime = anime[0]
        anime = anime.replace("-n", "")
        input_str = input_str.replace("-n" + anime, "")
        anime = int(anime)
    except IndexError:
        anime = 0
    input_str = input_str.strip()
    result = await search_in_animefiller(input_str)
    if result == {}:
        return await edit_or_reply(
            event, f"**No filler episodes for the given anime**` {input_str}`"
        )
    if len(result) == 1:
        response = await get_filler_episodes(result[list(result.keys())[0]])
        msg = ""
        msg += f"**Fillers for anime** `{list(result.keys())[0]}`**"
        msg += "\n\n• Manga Canon episodes:**`\n"
        msg += str(response.get("total_ep"))
        msg += "\n\n`**• Mixed/Canon fillers:**`\n"
        msg += str(response.get("mixed_ep"))
        msg += "\n\n`**• Fillers:**\n`"
        msg += str(response.get("filler_episodes"))
        if response.get("anime_canon_episodes") is not None:
            msg += "\n\n`**• Anime Canon episodes:**\n`"
            msg += str(response.get("anime_canon_episodes"))
        msg += "`"
        return await edit_or_reply(event, msg)
    if anime == 0:
        msg = f"**More than 1 result found for {input_str}. so try as** `{Config.COMMAND_HAND_LER}fillers -n<number> {input_str}`\n\n"
        for i, an in enumerate(list(result.keys()), start=1):
            msg += f"{i}. {an}\n"
        return await edit_or_reply(event, msg)
    try:
        response = await get_filler_episodes(result[list(result.keys())[anime - 1]])
    except IndexError:
        msg = f"**Given index for {input_str} is wrong check again for correct index and then try** `{Config.COMMAND_HAND_LER}fillers -n<index> {input_str}`\n\n"
        for i, an in enumerate(list(result.keys()), start=1):
            msg += f"{i}. {an}\n"
        return await edit_or_reply(event, msg)
    msg = ""
    msg += f"**Fillers for anime** `{list(result.keys())[anime-1]}`**"
    msg += "\n\n• Manga Canon episodes:**`\n"
    msg += str(response.get("total_ep"))
    msg += "\n\n`**• Mixed/Canon fillers:**`\n"
    msg += str(response.get("mixed_ep"))
    msg += "\n\n`**• Fillers:**\n`"
    msg += str(response.get("filler_episodes"))
    if response.get("anime_canon_episodes") is not None:
        msg += "\n\n`**• Anime Canon episodes:**\n`"
        msg += str(response.get("anime_canon_episodes"))
    msg += "`"
    await edit_or_reply(event, msg)


@catub.cat_cmd(
    pattern="sanime(?:\s|$)([\s\S]*)",
    command=("sanime", plugin_category),
    info={
        "header": "Searches for anime.",
        "usage": "{tr}sanime <anime name",
        "examples": "{tr}sanime black clover",
    },
)
async def get_anime(event):
    "searches for anime."
    reply_to = await reply_id(event)
    input_str = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not input_str:
        if reply:
            input_str = reply.text
        else:
            return await edit_delete(
                event, "__What should i search ? Gib me Something to Search__"
            )
    catevent = await edit_or_reply(event, "`Searching Anime..`")
    jikan = jikanpy.jikan.Jikan()
    search_result = jikan.search("anime", input_str)
    first_mal_id = search_result["results"][0]["mal_id"]
    caption, image = await get_anime_manga(first_mal_id, "anime_anime", event.chat_id)
    try:
        downloader = SmartDL(image, anime_path, progress_bar=False)
        downloader.start(blocking=False)
        while not downloader.isFinished():
            pass
        await event.client.send_file(
            event.chat_id,
            file=anime_path,
            caption=caption,
            parse_mode="html",
            reply_to=reply_to,
        )
        await catevent.delete()
        os.remove(anime_path)
    except BaseException:
        image = getBannerLink(first_mal_id, True)
        await event.client.send_file(
            event.chat_id,
            file=image,
            caption=caption,
            parse_mode="html",
            reply_to=reply_to,
        )


@catub.cat_cmd(
    pattern="char(?:\s|$)([\s\S]*)",
    command=("char", plugin_category),
    info={
        "header": "Shows you character infomation.",
        "usage": "{tr}char <char name>",
        "examples": "{tr}char Shota Nagisa",
    },
)
async def character(event):
    "Character information."
    reply_to = await reply_id(event)
    search_query = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not search_query:
        if reply:
            search_query = reply.text
        else:
            return await edit_delete(
                event, "__What should i search ? Gib me Something to Search__"
            )
    catevent = await edit_or_reply(event, "`Searching Character...`")
    try:
        search_result = jikan.search("character", search_query)
    except APIException:
        return await edit_delete(catevent, "`Character not found.`")
    first_mal_id = search_result["results"][0]["mal_id"]
    character = jikan.character(first_mal_id)
    caption = f"🇯🇵 [{character['name']}]({character['url']})"
    if character["name_kanji"] != "Japanese":
        caption += f" • `{character['name_kanji']}`\n"
    else:
        caption += "\n"
    if character["nicknames"]:
        nicknames_string = ", ".join(character["nicknames"])
        caption += f"\n**Nicknames** : `{nicknames_string}`"
    about = character["about"].split(" ", 60)
    try:
        about.pop(60)
    except IndexError:
        pass
    about_string = " ".join(about)
    mal_url = search_result["results"][0]["url"]
    for entity in character:
        if character[entity] is None:
            character[entity] = "Unknown"
    caption += f"\n\n🔰**Extracted Character Data**🔰\n\n{about_string}"
    caption += f" [Read More]({mal_url})..."
    await catevent.delete()
    await event.client.send_file(
        event.chat_id,
        file=character["image_url"],
        caption=replace_text(caption),
        reply_to=reply_to,
    )


@catub.cat_cmd(
    pattern="a(kaizoku|kayo|indi)(?: |$)([\S\s]*)",
    command=("akaizoku", plugin_category),
    info={
        "header": "Shows you anime download link.",
        "usage": [
            "{tr}akaizoku <anime name>",
            "{tr}akayo <anime name>",
            "{tr}aindi <anime name>",
        ],
        "examples": [
            "{tr}akaizoku one piece",
            "{tr}akayo tokyo revengers",
            "{tr}aindi Spirited Away",
        ],
    },
)
async def anime_download(event):  # sourcery no-metrics
    "Anime download links."
    search_query = event.pattern_match.group(2)
    input_str = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not search_query and reply:
        search_query = reply.text
    elif not search_query:
        return await edit_delete(
            event, "__What should i search ? Gib me Something to Search__"
        )
    catevent = await edit_or_reply(event, "`Searching anime...`")
    search_query = search_query.replace(" ", "+")
    if input_str == "kaizoku":
        search_url = f"https://animekaizoku.com/?s={search_query}"
        html_text = requests.get(search_url, headers=headers).text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h2", {"class": "post-title"})
        if search_result:
            result = f"<a href={search_url}>Click Here For More Results</a> <b>of</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKaizoku</code>: \n\n"
            for entry in search_result:
                post_link = "https://animekaizoku.com/" + entry.a["href"]
                post_name = html.escape(entry.text)
                result += f"• <a href={post_link}>{post_name}</a>\n"
        else:
            result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKaizoku</code>"
    elif input_str == "kayo":
        search_url = f"https://animekayo.com/?s={search_query}"
        html_text = requests.get(search_url, headers=headers).text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h2", {"class": "title"})
        result = f"<a href={search_url}>Click Here For More Results</a> <b>of</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKayo</code>: \n\n"
        if search_result:
            for entry in search_result:
                if entry.text.strip() == "Nothing Found":
                    result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKayo</code>"
                    break
                post_link = entry.a["href"]
                post_name = html.escape(entry.text.strip())
                result += f"• <a href={post_link}>{post_name}</a>\n"
        else:
            result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKayo</code>"
    elif input_str == "indi":
        search_url = f"https://indianime.com/?s={search_query}"
        html_text = requests.get(search_url, headers=headers).text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h1", {"class": "elementor-post__title"})
        result = f"<a href={search_url}>Click Here For More Results</a> <b>of</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>indianime</code>: \n\n"
        if search_result:
            for entry in search_result:
                if entry.text.strip() == "Nothing Found":
                    result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>Indianime</code>.\n<b>You can request anime <a href='https://indianime.com/request-anime'>here</a></b>"
                    break
                post_link = entry.a["href"]
                post_name = html.escape(entry.text.strip())
                result += f"• <a href={post_link}>{post_name}</a>\n"
        else:
            result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>IndiAnime</code>"
    await catevent.edit(result, parse_mode="html")


@catub.cat_cmd(
    pattern="upcoming$",
    command=("upcoming", plugin_category),
    info={
        "header": "Shows you upcoming anime's.",
        "usage": "{tr}upcoming",
    },
)
async def upcoming(event):
    "Shows you Upcoming anime's."
    rep = "<b>Upcoming anime</b>\n"
    later = jikan.season_later()
    anime = later.get("anime")
    for new in anime:
        name = new.get("title")
        a_url = new.get("url")
        rep += f"• <a href='{a_url}'>{name}</a>\n"
        if len(rep) > 1000:
            break
    await edit_or_reply(event, rep, parse_mode="html")


@catub.cat_cmd(
    pattern="aschedule(?: |$)([\S\s]*)",
    command=("aschedule", plugin_category),
    info={
        "header": "Shows you animes to be aired on that day.",
        "description": "To get list of animes to be aired on that day use can also use 0 for monday , 1 for tuesday.... 6 for sunday.",
        "usage": "{tr}aschedule <weekdays/[0-6]>",
        "example": ["{tr}aschedule sunday", "{tr}aschedule 5"],
    },
)
async def aschedule_fetch(event):
    "To get list of animes scheduled on that day"
    input_str = event.pattern_match.group(1) or datetime.now().weekday()
    input_str = weekdays.get(input_str)
    try:
        input_str = int(input_str)
    except ValueError:
        return await edit_delete(event, "`You have given and invalid weekday`", 7)
    if input_str not in [0, 1, 2, 3, 4, 5, 6]:
        return await edit_delete(event, "`You have given and invalid weekday`", 7)
    result = await get_anime_schedule(input_str)
    await edit_or_reply(event, result[0])


@catub.cat_cmd(
    pattern="w(hat)?a$",
    command=("wa", plugin_category),
    info={
        "header": "Reverse search of anime.",
        "usage": [
            "{tr}whata reply to photo/gif/video",
            "{tr}wa reply to photo/gif/video",
        ],
    },
)
async def whatanime(event):
    "Reverse search of anime."
    reply = await event.get_reply_message()
    if not reply:
        return await edit_delete(
            event, "__reply to media to reverse search that anime__."
        )
    mediatype = media_type(reply)
    if mediatype not in ["Photo", "Video", "Gif", "Sticker"]:
        return await edit_delete(
            event,
            f"__Reply to proper media that is expecting photo/video/gif/sticker. not {mediatype}__.",
        )
    output = await _cattools.media_to_pic(event, reply)
    if output[1] is None:
        return await edit_delete(
            output[0], "__Unable to extract image from the replied message.__"
        )
    file = memory_file("anime.jpg", output[1])
    try:
        response = upload_file(file)
    except exceptions.TelegraphException as exc:
        try:
            response = upload_file(output[1])
        except exceptions.TelegraphException as exc:
            return await edit_delete(output[0], f"**Error :**\n__{exc}__")
    cat = f"https://telegra.ph{response[0]}"
    await output[0].edit("`Searching for result..`")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://api.trace.moe/search?anilistInfo&url={quote_plus(cat)}"
        ) as raw_resp0:
            resp0 = await raw_resp0.json()
        framecount = resp0["frameCount"]
        error = resp0["error"]
        if error != "":
            return await edit_delete(output[0], f"**Error:**\n__{error}__")
        js0 = resp0["result"]
        if not js0:
            return await output[0].edit("`No results found.`")
        js0 = js0[0]
        text = (
            f'**Titile Romaji : **`{html.escape(js0["anilist"]["title"]["romaji"])}`\n'
        )
        text += (
            f'**Titile Native :** `{html.escape(js0["anilist"]["title"]["native"])}`\n'
        )
        text += (
            f'**Titile English :** `{html.escape(js0["anilist"]["title"]["english"])}`\n'
            if js0["anilist"]["title"]["english"] is not None
            else ""
        )
        text += f'**Is Adult :** __{js0["anilist"]["isAdult"]}__\n'
        #         text += f'**File name :** __{js0["filename"]}__\n'
        text += f'**Episode :** __{html.escape(str(js0["episode"]))}__\n'
        text += f'**From :** __{readable_time(js0["from"])}__\n'
        text += f'**To :** __{readable_time(js0["to"])}__\n'
        percent = round(js0["similarity"] * 100, 2)
        text += f"**Similarity :** __{percent}%__\n"
        result = (
            f"**Searched {framecount} frames and found this as best result :**\n\n"
            + text
        )
        msg = await output[0].edit(result)
        try:
            await msg.reply(
                f'{readable_time(js0["from"])} - {readable_time(js0["to"])}',
                file=js0["video"],
            )
        except Exception:
            await msg.reply(
                f'{readable_time(js0["from"])} - {readable_time(js0["to"])}',
                file=js0["image"],
            )


@catub.cat_cmd(
    pattern="imanga(?: |$)(.*)",
    command=("imanga", plugin_category),
    info={
        "header": "Shows you details about a manga.",
        "usage": "{tr}imanga <manga name>",
        "examples": "{tr}imanga fairy tail",
    },
)
async def manga(event):
    "Search Manga"
    query = event.pattern_match.group(1)
    await edit_or_reply(event, "`Searching Manga...`")
    if not query:
        await edit_delete(event, "`Bruh.. Gib me Something to Search`", 5)
        return
    res = ""
    manga = ""
    try:
        res = jikan.search("manga", query).get("results")[0].get("mal_id")
    except APIException:
        await edit_delete(event, "Error connecting to the API. Please try again!", 5)
        return ""
    if res:
        try:
            manga = jikan.manga(res)
        except APIException:
            await edit_delete(
                event, "Error connecting to the API. Please try again!", 5
            )
            return ""
        title = manga.get("title")
        japanese = manga.get("title_japanese")
        type = manga.get("type")
        status = manga.get("status")
        score = manga.get("score")
        volumes = manga.get("volumes")
        chapters = manga.get("chapters")
        genre_lst = manga.get("genres")
        genres = ""
        for genre in genre_lst:
            genres += genre.get("name") + ", "
        genres = genres[:-2]
        synopsis = manga.get("synopsis")
        image = manga.get("image_url")
        url = manga.get("url")
        rep = f"<b>{title} ({japanese})</b>\n"
        rep += f"<b>Type:</b> <code>{type}</code>\n"
        rep += f"<b>Status:</b> <code>{status}</code>\n"
        rep += f"<b>Genres:</b> <code>{genres}</code>\n"
        rep += f"<b>Score:</b> <code>{score}</code>\n"
        rep += f"<b>Volumes:</b> <code>{volumes}</code>\n"
        rep += f"<b>Chapters:</b> <code>{chapters}</code>\n\n"
        rep += f"<a href='{image}'>\u200c</a>"
        rep += f"📖 <b>Synopsis</b>: <i>{synopsis}</i>\n"
        rep += f'<b>Read More:</b> <a href="{url}">MyAnimeList</a>'
        await edit_or_reply(event, rep, parse_mode="HTML", link_preview=True)


@catub.cat_cmd(
    pattern="anime ?(.*)",
    command=("anime", plugin_category),
    info={
        "header": "Search anime in a noice format.",
        "usage": "{tr}anime <anime name>",
        "examples": "{tr}anime boku no pico",
    },
)
async def get_anime(message):
    "Anime Search in Different Template"
    try:
        query = message.pattern_match.group(1)
    except IndexError:
        if message.reply_to_msg_id:
            query = await message.get_reply_message().text
        else:
            await edit_delete(
                message,
                "You gave nothing to search. (｡ì _ í｡)\n `Usage: .anime <anime name>`",
                5,
            )
            return
    except Exception as err:
        await edit_delete(message, f"**Encountered an Unknown Exception**: \n{err}", 5)
        return

    p_rm = await edit_or_reply(message, "`Searching Anime...`")
    f_mal_id = ""
    try:
        jikan = jikanpy.AioJikan()
        search_res = await jikan.search("anime", query)
        f_mal_id = search_res["results"][0]["mal_id"]
    except IndexError:
        await p_rm.edit(f"No Results Found for {query}")
        return
    except Exception as err:
        await p_rm.edit(f"**Encountered an Unknown Exception**: \n{err}")
        return

    results_ = await jikan.anime(f_mal_id)
    await jikan.close()

    # Get All Info of anime
    anime_title = results_["title"]
    id = results_["mal_id"]
    jap_title = results_["title_japanese"]
    eng_title = results_["title_english"]
    type_ = results_["type"]
    results_["source"]
    episodes = results_["episodes"]
    status = results_["status"]
    results_["aired"].get("string")
    duration = results_["duration"]
    rating = results_["rating"]
    score = results_["score"]
    synopsis = results_["synopsis"]
    results_["background"]
    producer_list = results_["producers"]
    studios_list = results_["studios"]
    genres_list = results_["genres"]

    # Info for Buttons
    mal_dir_link = results_["url"]
    trailer_link = results_["trailer_url"]
    if trailer_link:
        trailer_link = f"[🎬 Trailer]({trailer_link})"
    else:
        trailer_link = "**No Trailer**"

    main_poster = ""
    telegraph_poster = ""
    # Poster Links Search
    try:
        main_poster = get_poster(anime_title)
    except BaseException:
        pass
    try:
        telegraph_poster = getBannerLink(f_mal_id)
    except BaseException:
        pass
    # if not main_poster:
    main_poster = telegraph_poster
    if not telegraph_poster:
        telegraph_poster = main_poster

    genress_md = ""
    producer_md = ""
    studio_md = ""
    for i in genres_list:
        genress_md += f"{i['name']} "
    for i in producer_list:
        producer_md += f"[{i['name']}]({i['url']}) "
    for i in studios_list:
        studio_md += f"[{i['name']}]({i['url']}) "

    # Build synopsis telegraph post
    html_enc = ""
    html_enc += f"<img src = '{telegraph_poster}' title = {anime_title}/>"
    html_enc += "<br><b>» Synopsis: </b></br>"
    html_enc += f"<br><em>{synopsis}</em></br>"
    synopsis_link = await post_to_telegraph(anime_title, html_enc)

    # Build captions:
    captions = f"""📺 **{anime_title}** ({eng_title}) - `{jap_title}`

**🆎 Type:** `{type_}`
**🆔 ID:** `{id}`
**🎭 Genre:** `{genress_md}`
**🔢 Episodes:** `{episodes}`
**⏰ Duration:** `{duration}`
**💯 Score:** `{score}/10`
**🔞 Rating:** `{rating}`
**📡 Status:** `{status}`

{trailer_link}

[📖 Synopsis]({synopsis_link}) **✘** [📚 More Info]({mal_dir_link})

©️ @LazyAF_Pepe"""

    await p_rm.delete()
    await message.client.send_file(message.chat_id, file=main_poster, caption=captions)
    await message.delete()
