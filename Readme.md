## 1. Setup

 - Update WEBHOOK_URLS in `modules/constants.py`
 - Add your discord bot token `.env` file. You can get token by inspecting element and watching Network section in discord browser.
 - You can see bot running commands in the `run.sh` file.


## 2. Scripts

 - to see real time txs : `watch_pool_v2.py`
 - to see real time transfers between wallets: `watch_transfers.py`
 - to see real time failed txs: `watch_failed_txs_v4.py`