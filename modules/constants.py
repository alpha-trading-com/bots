import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL_AETH_VIP_MESSAGES = "https://discord.com/api/webhooks/1444355854387253502/TzAaJT1a-Eya4PC49UamnXybEB6SthXgih8CclHarcXscTqSrI7D6OtTzhAyYf-wchCr"
WEBHOOK_URL_AETH_NEWS = "https://discord.com/api/webhooks/1440684964784902299/oqS9xREAL46lsroqnsKfjuJ35xFSmXGj135qKqHk_UKwQ0oB--GY20n9m38pjqBRx-Ip"

WEBHOOK_URL_AETH_CHAIN_EVENT = "https://discord.com/api/webhooks/1458409060595662890/BONgFo99qZkeH2k995SqzRDFCnaOPplbF1zULSWz5tAwp_AcE1r7VMebuKWR19EdTb5s"
WEBHOOK_URL_AETH_WALLET_TRANSACTIONS = "https://discord.com/api/webhooks/1458407677716598835/YrzG-vAo19z_nS3NdqK0R2taKd1RU5xloCLdnBFUW40qOZZbZ-kPpNe0Pk-bo_SU4a-7"

WEBHOOK_URL_SS_EVENTS = "https://discord.com/api/webhooks/1442889980962803855/L-rzuMa5KjmOdW_tQHWFFAG7gMiYBJ6FE8NkuV-qFmWhwogDF_9sGSVzmbZwt0NsvUfa"
WEBHOOK_URL_SS_WALLET_TRANSACTIONS = "https://discord.com/api/webhooks/1443556449165901864/Y80Cyvwlzr_Zb5iL1t1H7KPOnQUwYKt8TPho5XhjAbZXaoMIhqXW-LXV9OlxcL_a6ZOa"
WEBHOOK_URL_SS_MINI_WALLET_TRANSACTIONS = "https://discord.com/api/webhooks/1443556723133775902/zC_O25YvNxsMXrnRGEMQWe_vPypeA2LUg72X_vKcUchLy5FjtQbxDCwWikqBJWrD49fe"
WEBHOOK_URL_SS_TRANSFER_TRANSACTIONS = "https://discord.com/api/webhooks/1445165442925723660/rpQjJaewW0ZPTHs2KyHD1ClsXr0BDcmMcm1V9jviuwHcjP4TXVD9FU3Pg3ncNPMHwFXl"
WEBHOOK_URL_SS_SENSTIVE_MESSAGES = "https://discord.com/api/webhooks/1444902359380656130/nIOCmE9Fn9_j13WXWY_ebm7Ai_YodKQGsSjSgZzCiW953g-uSQXVmlNy7O0aoo8-EBL1"
WEBHOOK_URL_SS_INFOS = "https://discord.com/api/webhooks/1448700610281996391/I1J-wjDbM2-gyFjC0sCnVsu9djC6EXG2emjywEWhKqFumaMBahoffBubtjTB4AxBIRLY"

WEBHOOK_URL_SS_TRANSFER_TRANSACTIONS_IMP = "https://discord.com/api/webhooks/1459521067759439893/VEHiD_TZrUQTTJ2TRywuaHwIDLhS0j8ltojmS-NfVpGdWMW_1Cqw5izrCh3pJ8CKjRZv"
WEBHOOK_URL_SS_GITHUB_REPOS = "https://discord.com/api/webhooks/1466575672888655915/QM7R9Wnd8MQMbFdLcuuLP0OY_obqVEK2p1fpAAykvFcl1Dwqvxogfbw4GUi9i0DsH2Fd"
# NETWORK = "finney"
NETWORK = "ws://161.97.128.68:9944"


CEXS = {
    "5FqBL928choLPmeFz5UVAvonBD5k7K2mZSXVC9RkFzLxoy2s": "MEXC",
    "5GBnPzvPghS8AuCoo6bfnK7JUFHuyUhWSFD4woBNsKnPiEUi": "Binance",
    "5HiveMEoWPmQmBAb8v63bKPcFhgTGCmST1TVZNvPHSTKFLCv": "Taobridge",
    "5FqqXKb9zonSNKbZhEuHYjCXnmPbX9tdzMCU2gx8gir8Z8a5": "Cex",
}


KEY_WORDS = [
    "new team", 
    "ownership", 
    "man in charge", 
    "partner", 
    "launch", 
    "product",
    "phase",
    "live",
]

BOT_TOKEN = os.environ.get("BOT_TOKEN", "") # Discord token, can be found in the .env file and you can get it from inspect element of google browser

GOOGLE_DOC_ID_OWNER_WALLETS = "1VUDA8mzHd_iUQEqiDWMORys6--2ab8nDSThGb--_PaQ"
GOOGLE_DOC_ID_BOTS = "1Vdm20cXVAK-kjgjBw9XcbVYaAvvCWyY8IuPLAE2aRBI"
GOOGLE_DOC_ID_CHANNELS = "1c-KDhGKINbJRKlXBtsLahyuNIZg3ptRic1ZwM1PpWo4"
GOOGLE_DOC_ID_OWNER_WALLETS_SS = "167NEkUZkpzZx1L-jDgjdDQNhu5rlddpV__rArvTfqoo"
GOOGLE_DOC_ID_OWNER_WALLETS_PS = "1o0f3bPL5kvsRrnSI3vTc1knOlmY928SpaQP9Mi0USeI"
GOOGLE_DOC_ID_PRIVATE_WALLETS = "1HsQMieCTJVdznv8lkqIw2i5NJaYfAmYoLfEV92WzIOI"
GOOGLE_DOC_ID_JEETERS = "1h86JmOczyOD3hIJ3oi-KEx6gQPRI2j4KEb2ilxmUQQI"
TARGET_USER_IDS = [
    "389189199514959893",  # const
    "346765365642133514",  # siam kidd
    #"1020187154502144072", # Tegridy
    #"1438183192610734211",  # soon
]