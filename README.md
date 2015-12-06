weechat-twitch
==============

Checks status of streams using twitch api


This script assumes your Twitch server is named 'twitch' and Group Chat server is named 'twitchgrp' (for whisper support)
The Group server you will only be able to join Group chat channels and send and recieve whispers. I just idle the Group server with no channels joined incase i recieve a whisper
```
/server add twitch irc.twitch.tv
/set irc.server.twitch.capabilities "twitch.tv/membership,twitch.tv/commands,twitch.tv/tags"
/set irc.server.twitch.nicks "My Twitch Username"
/set irc.server.twitch.password "oauth:My Oauth Key"
```
```
/server add twitchgrp 192.16.64.180:443,192.16.64.212:443,199.9.253.119:443,199.9.253.120:443
/set irc.server.twitchgrp.capabilities "twitch.tv/membership,twitch.tv/commands,twitch.tv/tags"
/set irc.server.twitchgrp.nicks "My Twitch Username"
/set irc.server.twitchgrp.password "oauth:My Oauth Key"
```
