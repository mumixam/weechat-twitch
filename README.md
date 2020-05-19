weechat-twitch
==============

Checks status of streams using twitch api


Option `plugins.var.python.twitch.servers` controls what server this script will work on.
The default is `twitch` but you can have multiples separated by a space.
`/set plugins.var.python.twitch.servers twitch twitchcopy`

This script also will prefix users nicks @ for mod, % for sub, and ~ for broadcaster. This will break the traditional function of `/ignore add nightbot` and will require you to prefix nicks if you want to ignore someone `/ignore add re:[~@%]{0,3}nightbot` should ignore a nick with all or none of the prefixes used by this script.   
This may cause high cpu usage in very active chat and/or on slower cpus.   
This can also be disabled by setting `/set plugins.var.python.twitch.prefix_nicks off`   

```
/server add twitch irc.twitch.tv
/set irc.server.twitch.capabilities "twitch.tv/membership,twitch.tv/commands,twitch.tv/tags"
/set irc.server.twitch.nicks "My Twitch Username"
/set irc.server.twitch.password "oauth:My Oauth Key"
```

After your up and running this script will check if a stream is live via the Twitch API everytime you switch to a streams chat buffer.   
You can also issue `/twitch` in a stream's chat buffer to request a update and display stream topic.   
`/whois twitchuser` will perform a api lookup on said user and reply in the buffer you issued the command from.   
```
/whois justin

-- [justin] Account Created: 2007-05-22
-- [justin] Status: Monstercat Label Showcase Powered by TheDrop.club
-- [justin] Partnered: False Followers: 288596
-- [justin] Following: 33
-- [justin] Steam64ID: 76561197960265728 steamID3: 1 steamID: STEAM_0:0:1
```

If you are experiencing errors you can enable debug mode by setting
```
/set plugins.var.python.twitch.debug on
```
And/or disable SSL/TLS verification by setting
```
/set plugins.var.python.twitch.ssl_verify off
```

A Oauth token with matching ClientID is now required for all Twitch Helix API Calls.
You can use the generator below if you wish.
https://mumixam.github.io/weechat_twitch/

