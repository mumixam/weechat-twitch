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
# when you switch to its buffer or by issuing /twitch in the buffer

import weechat
import json
import datetime
import time

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
    username = weechat.buffer_get_string(buffer, 'short_name').replace('#', '')
    server = weechat.buffer_get_string(buffer, 'localvar_server')
    type = weechat.buffer_get_string(buffer, 'localvar_type')
    if not (server == 'twitch' and type == 'channel'):
        return weechat.WEECHAT_RC_OK
    url = 'https://api.twitch.tv/kraken/streams/' + username
    url_hook_process = weechat.hook_process(
        "url:%s" % url, 5 * 1000, "process_complete", buffer)
    return weechat.WEECHAT_RC_OK


def process_complete(data, command, rc, stdout, stderr):
    try:
        jsonDict = json.loads(stdout.strip())
    except:
        weechat.prnt(data, 'TWITCH: Error with twitch API')
        return weechat.WEECHAT_RC_OK
    currentbuf = weechat.current_buffer()
    if not jsonDict['stream']:
        weechat.buffer_set(data, "title", "STREAM: OFFLINE")
    else:
        createtime = jsonDict['stream']['created_at']
        viewers = jsonDict['stream']['viewers']
        followers = jsonDict['stream']['channel']['followers']
        starttime = datetime.datetime.fromtimestamp(
            time.mktime(time.strptime(createtime + " GMT", "%Y-%m-%dT%H:%M:%SZ %Z")))
        currenttime = datetime.datetime.utcnow()
        dur = currenttime - starttime
        uptime = days_hours_minutes(dur)

        weechat.buffer_set(data, "title", "STREAM: LIVE with %s viewers started %s ago [%s followers]" % (
            viewers, uptime, followers))
    return weechat.WEECHAT_RC_OK


def twitch_buffer_switch(data, signal, signal_data):
    server = weechat.buffer_get_string(signal_data, 'localvar_server')
    type = weechat.buffer_get_string(signal_data, 'localvar_type')
    if not (server == 'twitch' and type == 'channel'):
        return weechat.WEECHAT_RC_OK
    twitch_main('', signal_data, '')
    return weechat.WEECHAT_RC_OK


if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE,
                    SCRIPT_DESC, "", ""):
    weechat.hook_command("twitch", SCRIPT_DESC, "", "", "", "twitch_main", "")
    weechat.hook_signal('buffer_switch', 'twitch_buffer_switch', '')
