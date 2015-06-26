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
        "curl %s" % url, 7 * 1000, "process_complete", buffer)
    return weechat.WEECHAT_RC_OK


gamelist = [
    "Counter-Strike: Global Offensive;CSGO",
    "World of Warcraft: Warlords of Draenor;WOW"
    ]


def gameshort(game):
    global gamelist
    for games in gamelist:
        gamelong=games.split(';')[0]
        if gamelong.lower() == game.lower():
            return('<'+games.split(';')[-1]+'>')
        else:
            return '<'+game+'>'

cleantitle = lambda title: ''.join(filter(string.printable.__contains__, title))


def process_complete(data, command, rc, stdout, stderr):
    try:
        jsonDict = json.loads(stdout.strip())
    except Exception as e: 
        weechat.prnt(data, 'TWITCH: Error with twitch API')
        return weechat.WEECHAT_RC_OK
    currentbuf = weechat.current_buffer()
    title_fg=weechat.color(weechat.config_color(weechat.config_get("weechat.bar.title.color_fg")))
    title_bg=weechat.color(weechat.config_color(weechat.config_get("weechat.bar.title.color_bg")))
    pcolor=weechat.color('chat_prefix_network')
    ccolor=weechat.color('chat')
    red=weechat.color('red')
    blue=weechat.color('blue')
    green=weechat.color('green')
    ptime=time.strftime("%H:%M:%S")
    if not jsonDict['stream']:
        weechat.buffer_set(data, "title", "STREAM: %sOFFLINE%s %sCHECKED AT: %s" % (red, title_fg, blue, ptime))
    else:
        currenttime = time.time()
        output='STREAM: %sLIVE%s' % (green, title_fg)
        if 'game' in jsonDict['stream']:
            game = gameshort(jsonDict['stream']['game'])
            output += ' %s with' % game
        if 'viewers' in jsonDict['stream']:
            viewers = jsonDict['stream']['viewers']
            output += ' %s viewers started' % viewers
        if 'created_at' in jsonDict['stream']:
            createtime = jsonDict['stream']['created_at'].replace('Z', 'GMT')
            starttime = timegm(time.strptime(createtime,'%Y-%m-%dT%H:%M:%S%Z'))
            dur=timedelta(seconds=currenttime-starttime)
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
                    weechat.buffer_set(data, 'localvar_set_tstatus', title)
                    weechat.prnt(data, '%s--%s Title is "%s"' % (pcolor, ccolor, title))
            if 'updated_at' in jsonDict['stream']['channel']:
                updateat = jsonDict['stream']['channel']['updated_at'].replace('Z', 'GMT')
                updatetime = timegm(time.strptime(updateat,'%Y-%m-%dT%H:%M:%S%Z'))
                udur = timedelta(seconds=currenttime-updatetime)
                titleage = days_hours_minutes(udur)

        output += ' %s' % ptime
        weechat.buffer_set(data, "title", output)
    return weechat.WEECHAT_RC_OK

def twitch_clearchat(data, modifier, modifier_data, string):
    string = string.split(" ")
    channel = string[2]
    server = modifier_data
    user = ""
    if len(string) == 4:
        user = string[3].replace(":","")
    if not channel.startswith("#"):
        return ""
    buffer = weechat.buffer_search("irc", "%s.%s" % (server,channel))
    if buffer:
        pcolor=weechat.color('chat_prefix_network')
        ccolor=weechat.color('chat')
        if user:
            weechat.prnt(buffer,"%s--%s %s's Chat Cleared By Moderator" % (pcolor,ccolor,user))
        else:
            weechat.prnt(buffer,"%s--%s Entire Chat Cleared By Moderator" % (pcolor,ccolor))
    return ""

def twitch_suppress(data, modifier, modifier_data, string):
    return ""

def twitch_reconnect(data, modifier, modifier_data, string):
    server = modifier_data
    buffer = weechat.buffer_search("irc", "server.%s" % server)
    if buffer:
        pcolor=weechat.color('chat_prefix_network')
        ccolor=weechat.color('chat')
        weechat.prnt(buffer,"%s--%s Server sent reconnect request. Issuing /reconnect" % (pcolor,ccolor))
        weechat.command(buffer, "/reconnect")
    return ""

def twitch_buffer_switch(data, signal, signal_data):
    server = weechat.buffer_get_string(signal_data, 'localvar_server')
    type = weechat.buffer_get_string(signal_data, 'localvar_type')
    if not (server == 'twitch' and type == 'channel'):
        return weechat.WEECHAT_RC_OK
    twitch_main('', signal_data, 'bs')
    return weechat.WEECHAT_RC_OK


if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE,
                    SCRIPT_DESC, "", ""):
    weechat.hook_command("twitch", SCRIPT_DESC, "", "", "", "twitch_main", "")
    weechat.hook_signal('buffer_switch', 'twitch_buffer_switch', '')
    weechat.hook_modifier("irc_in_CLEARCHAT", "twitch_clearchat", "")
    weechat.hook_modifier("irc_in_RECONNECT", "twitch_reconnect", "")
    weechat.hook_modifier("irc_in_USERSTATE", "twitch_suppress", "")
    weechat.hook_modifier("irc_in_HOSTTARGET", "twitch_suppress", "")
    weechat.hook_modifier("irc_in_ROOMSTATE", "twitch_suppress", "")
