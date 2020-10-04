# MAD Plugin - Shiny Watcher

Get support on this [Discord Server](https://discord.gg/cMZs5tk)

Shiny Watcher checks your DB for shiny encounters and then sends a notification to Discord if it finds any. It allows to filter out Pokemon and Workers as well as report the login account used by the worker.

Notifications appear as: `Name (Gender icon, IV%, lv#; remaining min/sec left)\nFound: Time\nDespawns: Time\nWorker device/account` (the screenshot below is somewhat outdated, but is accurate enough). For Android devices, the coordinates are embeded so you can copy them by pressing for ~2 seconds. Fast and easy. There's also an option to optimize notifications for iOS devices.

![Screenshot](https://i.imgur.com/kvUSoI4.png)

## Notes
- MAD and Discord only
- only works with MAD plugin system
- Credits to [CCEV](https://github.com/ccev/shinywatcher) who created the original version of shinywatcher

## Getting Started
- Enable `game_stats` and `game_stats_raw` in your MAD config.ini, if not already done
- import Plugin `ShinyWatcher.mp` via MADmin website at System > MAD Plugins
- `cp plugin.ini.example plugin.ini`
- Edit and fill out plugin.ini (see example below for what to fill in)
- `discord_webhookurl` is required for messages. Google how to get the url.
- restart MAD to activate the plugin configuration

## What to fill in
### Config
copy plugin.ini.example to plugin.ini and adjust it with your data
- `ONLY_SHOW_WORKERS` Leave blank if you want notifications from all workers. If you only want them from certain Accounts, follow the format in the example
- `EXCLUDE_MONS` Filter out Mons you already have enough Shinies of. Follow the example format!
- `OS` Set your notifications to `android` or `ios` mode. On Android, messages have an embed contaning the coords. For iOS an extra message containing coords will be sent
###  plugin.ini

```
[plugin]
active = true
discord_webhookurl: https://discord.com/api/webhooks/xxxxxxxx/xxxxxxxxxxxxxxxxxxxxxx
language = en
os = android
only_show_workers = ATV01,ATV19,ATV34
exlude_mons = 1,4,7
mask_mail = no
pinguser = yes

[pingusermapping]
device_origin = <@xxxxxxxxxxxxxxxxxxxxxxxx>
```
