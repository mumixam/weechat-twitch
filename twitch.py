# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# This script checks stream status of any channel on the 'twitch' server
# when you switch to its buffer and displays it in topic/title bar.
# It also displays stream title in channel when change is detected.
# Force status update by issuing /twitch in buffer

import weechat
import json
from calendar import timegm
from datetime import datetime, timedelta
import time
import string
import re

SCRIPT_NAME = "twitch"
SCRIPT_AUTHOR = "mumixam"
SCRIPT_VERSION = "0.1"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC = "Display stream status in title bar of buffer"

process_output = ""


def days_hours_minutes(td):
    age = ''
    hours = td.seconds // 3600
    min = td.seconds // 60 % 60
    if not td.days == 0:
        age += str(td.days) + 'd '
    if not hours == 0:
        age += str(hours) + 'h '
    if not min == 0:
        age += str(min) + 'm'
    return age.strip()


def twitch_main(data, buffer, args):
    if not args == 'bs':
        weechat.buffer_set(buffer, 'localvar_set_tstatus', '')
    username = weechat.buffer_get_string(buffer, 'short_name').replace('#', '')
    server = weechat.buffer_get_string(buffer, 'localvar_server')
    type = weechat.buffer_get_string(buffer, 'localvar_type')
    if not (server == 'twitch' and type == 'channel'):
        return weechat.WEECHAT_RC_OK
    url = 'https://api.twitch.tv/kraken/streams/' + username
    url_hook_process = weechat.hook_process(
        "curl " + url, 7 * 1000, "stream_api", buffer)
    return weechat.WEECHAT_RC_OK


gamelist = [
    "Counter-Strike: Global Offensive;CSGO",
    "World of Warcraft: Warlords of Draenor;WOW"
]


def gameshort(game):
    global gamelist
    for games in gamelist:
        gamelong = games.split(';')[0]
        if gamelong.lower() == game.lower():
            return('<' + games.split(';')[-1] + '>')
        else:
            return '<' + game + '>'

cleantitle = lambda title: ''.join(
    filter(string.printable.__contains__, title))


def channel_api(data, command, rc, stdout, stderr):
    global name
    try:
        jsonDict = json.loads(stdout.strip())
    except Exception as e:
        weechat.prnt(data, 'TWITCH: Error with twitch API')
        return weechat.WEECHAT_RC_OK
    currentbuf = weechat.current_buffer()
    pcolor = weechat.color('chat_prefix_network')
    ccolor = weechat.color('chat')
    dcolor = weechat.color('chat_delimiters')
    ncolor = weechat.color('chat_nick')
    ul = weechat.color("underline")
    rul = weechat.color("-underline")
    pformat = weechat.config_string(
        weechat.config_get("weechat.look.prefix_network"))

    if len(jsonDict) == 22:
        name = jsonDict['display_name']
        create = jsonDict['created_at'].split('T')[0]
        status = jsonDict['status']
        follows = jsonDict['followers']
        partner = str(jsonDict['partner'])
        output = '%s%s %s[%s%s%s]%s %sAccount Created%s: %s' % (
            pcolor, pformat, dcolor, ncolor, name, dcolor, ccolor, ul, rul, create)
        if status:
            output += '\n%s%s %s[%s%s%s]%s %sStatus%s: %s' % (
                pcolor, pformat, dcolor, ncolor, name, dcolor, ccolor, ul, rul, cleantitle(status))
        output += '\n%s%s %s[%s%s%s]%s %sPartnered%s: %s %sFollowers%s: %s' % (
            pcolor, pformat, dcolor, ncolor, name, dcolor, ccolor, ul, rul, partner, ul, rul, follows)
        weechat.prnt(data, output)
        url = 'https://api.twitch.tv/kraken/users/' + \
            name.lower() + '/follows/channels'
        urlh = weechat.hook_process(
            "curl " + url, 7 * 1000, "channel_api", currentbuf)

    if len(jsonDict) == 18:
        name = jsonDict['display_name']
        s64id = jsonDict['steam_id']
        if s64id:
            sid3 = int(s64id) - 76561197960265728
            highaid = "{0:b}".format(sid3).zfill(32)[:31]
            lowaid = "{0:b}".format(sid3).zfill(32)[31:]
            id32bit = "STEAM_0:%s:%s" % (lowaid, int(highaid, 2))

            output = '%s%s %s[%s%s%s]%s %ssteamID64%s: %s %ssteamID3%s: %s %ssteamID%s: %s' % (
                pcolor, pformat, dcolor, ncolor, name, dcolor, ccolor, ul, rul, s64id, ul, rul, sid3, ul, rul, id32bit)
            weechat.prnt(data, output)

    if len(jsonDict) == 3:
        if 'status' in jsonDict.keys():
            if jsonDict['status'] == 404 or jsonDict['status'] == 422:
                user = jsonDict['message'].split()[1].replace("'", "")
                weechat.prnt(data, '%s%s %s[%s%s%s]%s No such user' % (
                    pcolor, pformat, dcolor, ncolor, user, dcolor, ccolor))
        else:
            url = 'https://api.twitch.tv/api/channels/' + name.lower()
            urlh = weechat.hook_process(
                "curl " + url, 7 * 1000, "channel_api", currentbuf)
            count = jsonDict['_total']
            if count:
                output = '%s%s %s[%s%s%s]%s %sFollowing%s: %s' % (
                    pcolor, pformat, dcolor, ncolor, name, dcolor, ccolor, ul, rul, count)
                weechat.prnt(data, output)
    return weechat.WEECHAT_RC_OK


def stream_api(data, command, rc, stdout, stderr):
    try:
        jsonDict = json.loads(stdout.strip())
    except Exception as e:
        weechat.prnt(data, 'TWITCH: Error with twitch API')
        return weechat.WEECHAT_RC_OK
    currentbuf = weechat.current_buffer()
    title_fg = weechat.color(
        weechat.config_color(weechat.config_get("weechat.bar.title.color_fg")))
    title_bg = weechat.color(
        weechat.config_color(weechat.config_get("weechat.bar.title.color_bg")))
    pcolor = weechat.color('chat_prefix_network')
    ccolor = weechat.color('chat')
    red = weechat.color('red')
    blue = weechat.color('blue')
    green = weechat.color('green')
    ptime = time.strftime("%H:%M:%S")
    subs = weechat.buffer_get_string(data, 'localvar_subs')
    r9k = weechat.buffer_get_string(data, 'localvar_r9k')
    slow = weechat.buffer_get_string(data, 'localvar_slow')
    if not 'stream' in jsonDict.keys():
        weechat.prnt(data, 'TWITCH: Error with twitch API')
        return weechat.WEECHAT_RC_OK
    if not jsonDict['stream']:
        line = "STREAM: %sOFFLINE%s %sCHECKED AT: %s" % (
            red, title_fg, blue, ptime)
        if subs:
            line += " %s[SUBS]" % title_fg
        if r9k:
            line += " %s[R9K]" % title_fg
        if slow:
            line += " %s[SLOW@%s]" % (title_fg, slow)
        weechat.buffer_set(data, "title", line)
    else:
        currenttime = time.time()
        output = 'STREAM: %sLIVE%s' % (green, title_fg)
        if 'game' in jsonDict['stream']:
            if jsonDict['stream']['game']:
                game = gameshort(jsonDict['stream']['game'])
                output += ' %s with' % game
        if 'viewers' in jsonDict['stream']:
            viewers = jsonDict['stream']['viewers']
            output += ' %s viewers started' % viewers
        if 'created_at' in jsonDict['stream']:
            createtime = jsonDict['stream']['created_at'].replace('Z', 'GMT')
            starttime = timegm(
                time.strptime(createtime, '%Y-%m-%dT%H:%M:%S%Z'))
            dur = timedelta(seconds=currenttime - starttime)
            uptime = days_hours_minutes(dur)
            output += ' %s ago' % uptime
        if 'channel' in jsonDict['stream']:
            if 'followers' in jsonDict['stream']['channel']:
                followers = jsonDict['stream']['channel']['followers']
                output += ' [%s followers]' % followers
            if 'status' in jsonDict['stream']['channel']:
                title = cleantitle(jsonDict['stream']['channel']['status'])
                oldtitle = weechat.buffer_get_string(data, 'localvar_tstatus')
                if not oldtitle == title:
                    weechat.prnt(data, '%s--%s Title is "%s"' %
                                 (pcolor, ccolor, title))
                    weechat.buffer_set(data, 'localvar_set_tstatus', title)
            if 'updated_at' in jsonDict['stream']['channel']:
                updateat = jsonDict['stream']['channel'][
                    'updated_at'].replace('Z', 'GMT')
                updatetime = timegm(
                    time.strptime(updateat, '%Y-%m-%dT%H:%M:%S%Z'))
                udur = timedelta(seconds=currenttime - updatetime)
                titleage = days_hours_minutes(udur)

        output += ' %s' % ptime
        if subs:
            output += " %s[SUBS]" % title_fg
        if r9k:
            output += " %s[R9K]" % title_fg
        if slow:
            output += " %s[SLOW@%s]" % (title_fg, slow)
        weechat.buffer_set(data, "title", output)
    return weechat.WEECHAT_RC_OK


def twitch_clearchat(data, modifier, modifier_data, string):
    string = string.split(" ")
    channel = string[2]
    server = modifier_data
    user = ""
    if len(string) == 4:
        user = string[3].replace(":", "")
    if not channel.startswith("#"):
        return ""
    buffer = weechat.buffer_search("irc", "%s.%s" % (server, channel))
    if buffer:
        pcolor = weechat.color('chat_prefix_network')
        ccolor = weechat.color('chat')
        if user:
            weechat.prnt(
                buffer, "%s--%s %s's Chat Cleared By Moderator" % (pcolor, ccolor, user))
        else:
            weechat.prnt(
                buffer, "%s--%s Entire Chat Cleared By Moderator" % (pcolor, ccolor))
    return ""


def twitch_suppress(data, modifier, modifier_data, string):
    return ""


def twitch_reconnect(data, modifier, modifier_data, string):
    server = modifier_data
    buffer = weechat.buffer_search("irc", "server.%s" % server)
    if buffer:
        pcolor = weechat.color('chat_prefix_network')
        ccolor = weechat.color('chat')
        weechat.prnt(
            buffer, "%s--%s Server sent reconnect request. Issuing /reconnect" % (pcolor, ccolor))
        weechat.command(buffer, "/reconnect")
    return ""


def twitch_buffer_switch(data, signal, signal_data):
    server = weechat.buffer_get_string(signal_data, 'localvar_server')
    type = weechat.buffer_get_string(signal_data, 'localvar_type')
    if not (server == 'twitch' and type == 'channel'):
        return weechat.WEECHAT_RC_OK
    twitch_main('', signal_data, 'bs')
    return weechat.WEECHAT_RC_OK


def twitch_roomstate(data, modifier, server, string):
    message = weechat.info_get_hashtable(
        'irc_message_parse', {"message": string})
    buffer = weechat.buffer_search(
        "irc", "%s.%s" % (server, message['channel']))
    for tag in message['tags'].split(';'):
        if tag == 'subs-only=0':
            weechat.buffer_set(buffer, 'localvar_set_subs', '')
        if tag == 'subs-only=1':
            weechat.buffer_set(buffer, 'localvar_set_subs', '1')
        if tag == 'r9k=0':
            weechat.buffer_set(buffer, 'localvar_set_r9k', '')
        if tag == 'r9k=1':
            weechat.buffer_set(buffer, 'localvar_set_r9k', '1')
        if tag.startswith('slow='):
            value = tag.split('=')[-1]
            if value == '0':
                weechat.buffer_set(buffer, 'localvar_set_slow', '')
            if value > '0':
                weechat.buffer_set(buffer, 'localvar_set_slow', value)
        twitch_main('', buffer, 'bs')
    return ''


def twitch_whisper(data, modifier, modifier_data, string):
    liststr = string.split()
    if len(liststr) > 3:
        if liststr[2] == "WHISPER":
            liststr[2] = "PRIVMSG"
        if liststr[1] == "WHISPER":
            liststr[1] = "PRIVMSG"
    return ' '.join(liststr)


def twitch_privmsg(data, modifier, server_name, string):
    if not server_name == 'twitch':
        return string
    match = re.match(r"^PRIVMSG (.*?) :(.*)", string)
    if not match:
        return string
    if match.group(1).startswith('#'):
        return string
    newmsg = 'PRIVMSG jtv :.w ' + match.group(1) + ' ' + match.group(2)
    return newmsg


def twitch_in_privmsg(data, modifier, server_name, string, prefix=''):
    if not server_name == 'twitch':
        return string

    mp = weechat.info_get_hashtable("irc_message_parse", {"message": string})

    if not mp['tags']:
        return string
    if '#' + mp['nick'] == mp['channel']:
        return mp['message_without_tags'].replace(mp['nick'], '~' + mp['nick'], 1)

    tags = dict([s.split('=') for s in mp['tags'].split(';')])
    if tags['user-type'] == 'mod':
        prefix += '@'
    if tags['subscriber'] == '1':
        prefix += '%'
    if prefix:
        msg = mp['message_without_tags'].replace(
            mp['nick'], prefix + mp['nick'], 1)
        return '@' + mp['tags'] + ' ' + msg
    else:
        return string


def twitch_whois(data, modifier, server_name, string):
    if not server_name == 'twitch':
        return string
    match = re.match(r"^WHOIS (\S+)", string)
    currentbuf = weechat.current_buffer()
    username = match.group(1)
    if not match:
        return string
    url = 'https://api.twitch.tv/kraken/channels/' + username
    url_hook = weechat.hook_process(
        "curl " + url, 7 * 1000, "channel_api", currentbuf)
    return ""


if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE,
                    SCRIPT_DESC, "", ""):
    weechat.hook_command("twitch", SCRIPT_DESC, "", "", "", "twitch_main", "")
    weechat.hook_signal('buffer_switch', 'twitch_buffer_switch', '')
    weechat.hook_modifier("irc_in_CLEARCHAT", "twitch_clearchat", "")
    weechat.hook_modifier("irc_in_RECONNECT", "twitch_reconnect", "")
    weechat.hook_modifier("irc_in_USERSTATE", "twitch_suppress", "")
    weechat.hook_modifier("irc_in_HOSTTARGET", "twitch_suppress", "")
    weechat.hook_modifier("irc_in_ROOMSTATE", "twitch_roomstate", "")
    weechat.hook_modifier("irc_in_WHISPER", "twitch_whisper", "")
    weechat.hook_modifier("irc_out_PRIVMSG", "twitch_privmsg", "")
    weechat.hook_modifier("irc_out_WHOIS", "twitch_whois", "")
    weechat.hook_modifier("irc_in_PRIVMSG", "twitch_in_privmsg", "")
