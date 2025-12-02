pm2 start  coldkey_swap_v2.py --interpreter python3  --name "coldkey_swap_v2" --interpreter-args "-u"
pm2 start  owner_coldkey_events.py --interpreter python3  --name "owner_coldkey_events" --interpreter-args "-u"
pm2 start  channel_monitor_bot.py --interpreter python3  --name "channel_monitor_bot" --interpreter-args "-u"
pm2 start  watch_channel_name_change.py --interpreter python3  --name "watch_channel_name_change" --interpreter-args "-u"