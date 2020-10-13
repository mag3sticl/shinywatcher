# MAD Plugin - Shiny Watcher

Get support on this [Discord Server](https://discord.gg/cMZs5tk)

Shiny Watcher checks your DB for active Shinies and then sends a notification to Discord if it finds any. It allows to filter out Pokemon and Workers as well as connect a Login E-Mail to every worker.

Notifications will always be: `Pokemon-name IV% L# CP# Gender:symbol \n Despawns: Time (time left) \n Worker name (account/email/)`. On Android devices, the coordinates are embeded so you can copy them by long-pressing (for ~2 seconds). Fast and easy. There's also an option to optimize what is displayed for iOS.

![Screenshot](https://i.imgur.com/kvUSoI4.png)

## Notes
- MAD and Discord only
- only works with MAD plugin system
- discord_webhook has to be installed in the MAD enviroment
- You need to enable game_stats_raw at your MAD config
- Credits to [CCEV](https://github.com/ccev/shinywatcher) who created the original version of shinywatcher

## Getting Started
- import Plugin `ShinyWatcher.mp` via MADmin website at System > MAD Plugins
- `cp plugin.ini.example plugin.ini`
- Fill out plugin.ini (It's explained below what to fill in)
- restart MAD to activate the plugin configuration

## What to fill in
### Config
copy plugin.ini.example to plugin.ini and adjust it with your data
- `ONLY_SHOW_WORKERS` Leave blank if you want notifications from all workers. If you only want them from certain Accounts, follow the format in the example
- `EXCLUDE_MONS` Filter out Mons you already have enough Shinies of. Follow the example format!
- `OS` Set your notifications to `android` or `ios` mode. On Android, messages have an embed contaning the coords. For iOS an extra message containing coords will be sent

###Pingusermapping
Ping one or more users in Discord when the mapped Scanner encounters a shiny. To get your User ID or anyone else’s User ID right click on their name and click “Copy ID” Alternative type there name as a mention and place a backslash \ in front of the mention.

###  plugin.ini

```
[plugin]
active = true
discord_webhookurl: https://discord.com/api/webhooks/xxxxxxxx/xxxxxxxxxxxxxxxxxxxxxx
language = en
os = android
only_show_workers = ATV01,ATV19,ATV34
exlude_mons = Bulbasaur,Pikachu,Gible
mask_mail = no
pinguser = no
timezone_offset = 0
accounts_usernames = privatePTC1,privateGmail1@gmail.com
accounts_display_custom = Instead_of_privatePTC1,Instead_of_privateGmail1@gmail.com

[pingusermapping]
device_origin = @xxxxxxxxxxxxxxxxxxxxxxxx
```
