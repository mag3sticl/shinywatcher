# MAD Plugin - Shiny Watcher

Get support on this [Discord Server](https://discord.gg/cMZs5tk)

Shiny Watcher checks your DB for active Shinies and then sends a notification to Discord if it finds any. It allows to filter out Pokemon and Workers as well as connect a Login E-Mail to every worker.

Notifications will always be: `Name (IV%) until Time (time left)\nWorker name (account/email)`. The coordinates are in an embed so you can copy them by pressing for ~2 seconds on an Android device. Fast and easy. There's also an option to optimize notifications for iOS.

![Screenshot](https://i.imgur.com/kvUSoI4.png)

## Notes
- MAD and Discord only
- only works with MAD plugin system
- Credits to [CCEV](https://github.com/ccev/shinywatcher) who created the original version of shinywatcher

## Getting Started
- import Plugin via MADmin website at System > MAD Plugins
- `cp plugin.ini.example plugin.ini`
- Fill out plugin.ini (It's explained below what to fill in)
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
webhookurl: https://discord.com/api/webhooks/xxxxxxxx   
language = de
os = android
only_show_workers = ATV01,ATV19,ATV34
exlude_mons = 1,4,7
```