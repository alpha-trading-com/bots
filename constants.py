ROUND_TABLE_HOTKEY = "5FFApaS75bv5pJHfAp2FVLBj9ZaXuFDjEypsaBNc1wCfe52v"
NETWORK = "ws://144.126.145.166:9944"


WEBHOOK_URL = "https://discord.com/api/webhooks/1379627091502305280/1GW3BaWycWYqbPgiDVkUq7QEWghyHk32IhUMP3iN8VE-vlXeQPD4WxcRqfJON8IchABF"


USERS = []
try:
    with open("handles.txt", "r") as f:
        USERS = f.read().splitlines()
except FileNotFoundError:
    print("handles.txt not found")
    USERS = []
