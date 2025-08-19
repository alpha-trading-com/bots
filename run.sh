pm2 start  coldkey_swap_v3.py --interpreter python3  --name "coldkey_swap_v3" --interpreter-args "-u"
pm2 start  coldkey_swap_v2.py --interpreter python3  --name "coldkey_swap_v2" --interpreter-args "-u"
pm2 start  coldkey_swap.py --interpreter python3  --name "coldkey_swap" --interpreter-args "-u"