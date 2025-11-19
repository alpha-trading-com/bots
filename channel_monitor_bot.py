import requests
import time
import json
import re
from datetime import datetime
from typing import List, Dict, Set


class DiscordCrawler:
    def __init__(self, channel_list: List[str], bot_token: str, webhook_url: str):
        self.channel_list = channel_list
        self.bot_token = bot_token
        self.webhook_url = webhook_url
        self.seen_message_ids: List = []
        self.api_urls = []
        self.initial_messages = []
        for channel_id in self.channel_list:
            self.api_urls.append(f"https://discord.com/api/v10/channels/{channel_id}/messages")
            empty_set = set()
            self.seen_message_ids.append(empty_set)

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"{self.bot_token}",
            "Content-Type": "application/json"
        }
    
    def fetch_messages(self, limit: int = 50, api_url: str = "") -> List[Dict]:
        """Fetch recent messages from the channel"""
        headers = self.get_headers()
        params = {"limit": limit}

        retries = 5
        # print(f"api_url: {api_url}")

        while retries > 0:
            # print(f"Retrying {retries} times...")
            try:
                response = requests.get(api_url, headers=headers, params=params)

                print(f"Response: {response.status_code}")
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Error response: {response.text}")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"Error fetching messages: {e}")
                retries -= 1
        print("Failed to fetch messages")
        return []
    
    def is_target_user_message(self, message: Dict) -> bool:
        """Check if message is from a target user"""
        author_id = message.get("author", {}).get("id")
        # return True
        return author_id in self.target_user_ids

    def is_twitter_hold(self, message: Dict) -> Dict:
        "Check if message holds twitter url"
        content = message.get("content", "")
        pattern = r'https://x.com/'
        return re.search(pattern, content) is not None

    def is_owner_claimed_message(self, message: Dict) -> bool:
        "Check if message is a owner claimed message"
        content = message.get("content", "")
        pattern = r'claimed ownership of this channel'
        return re.search(pattern, content) is not None

    def is_announcement_message(self, message: Dict) -> bool:
        "Check if message is an announcement message"
        content = message.get("content", "")
        pattern = r'announcement'
        is_announcement = re.search(pattern, content) is not None
        mention_roles = message.get("mention_roles", [])
        if len(mention_roles) > 0:
            is_announcement = True
        return is_announcement

    def create_embed(self, message: Dict, subnet_id: int) -> Dict:
        """Create Discord embed from message data"""
        author = message.get("author", {})
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")
        message_id = message.get("id", "")
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            formatted_time = timestamp

        color = 0xffff00
        if self.is_twitter_hold(message):
            title = f"New Twitter Posted from **Subnet {subnet_id}**" if subnet_id != 129 else f"New Twitter Posted from **Price-talk**"
            color = 0xffff00
        elif self.is_owner_claimed_message(message):
            title = f"New Owner Claimed Message from **Subnet {subnet_id}**" if subnet_id != 129 else f"New Owner Claimed Message from **Price-talk**"
            color = 0xa832a8
        elif self.is_announcement_message(message):
            title = f"New Announcement Message from **Subnet {subnet_id}**" if subnet_id != 129 else f"New Announcement Message from **Price-talk**"
            color = 0x66aaff
        else:
            title = f"New Unknown Type Message from **Subnet {subnet_id}**" if subnet_id != 129 else f"New Unknown Type Message from **Price-talk**"


        # Create embed
        embed = {
            "title": title,
            "description": content[:4096] if content else "*No text content*",  # Discord embed limit
            "color": color,
            "timestamp": timestamp,
            "author": {
                "name": f"{author.get('global_name', author.get('username', 'Unknown'))}",
                "icon_url": f"https://cdn.discordapp.com/avatars/{author.get('id')}/{author.get('avatar')}.png" if author.get('avatar') else None
            },
            "fields": [
                {
                    "name": "Channel",
                    "value": f"<#{self.channel_list[subnet_id]}>",
                    "inline": True
                }
            ]
        }

        return embed
    
    def send_webhook_message(self, embeds: List[Dict]):
        """Send message to webhook"""
        if not embeds:
            return
        
        payload = {
            "content": "@everyone Twitter posted",
            "embeds": embeds,
            "username": "Message Monitor",
            "avatar_url": "https://cdn.discordapp.com/embed/avatars/0.png"
        }
        
        retries = 5
        while retries > 0:
            try:
                response = requests.post(self.webhook_url, json=payload)
                if response.status_code in [200, 204]:
                    print(f"Successfully sent {len(embeds)} message(s) to webhook")
                    return
                else:
                    print(f"Failed to send webhook: {response.status_code} {response.text}")
                    retries -= 1
                    time.sleep(2)
            except Exception as e:
                print(f"Error sending webhook: {e}")
                retries -= 1
                time.sleep(2)
        print("Failed to send webhook")

    def process_new_messages(self, api_url: str, channel_name: int):
        """Process new messages and send to webhook"""
        messages = self.fetch_messages(api_url=api_url)
        if not messages:
            return

        new_messages = []
        new_message_ids = set()

        for message in messages:
            message_id = message.get("id")
            if not message_id:
                continue

            new_message_ids.add(message_id)

            # Check if this is a new message from a target user
            if (
                message_id not in self.seen_message_ids[channel_name]
                and (self.is_twitter_hold(message) or # twitter hold
                self.is_owner_claimed_message(message) or # owner claimed
                self.is_announcement_message(message)) # announcement
            ):
                new_messages.append(message)
                print(f"Found new message from {message.get('author', {}).get('username', 'Unknown')}: {message.get('content', '')[:50]}...")
        # for messages in new_message_ids:
        #     print(f"message = {messages}")

        # Update seen message IDs
        self.seen_message_ids[channel_name].update(new_message_ids)
        
        # Send new messages to webhook
        if new_messages:
            embeds = [self.create_embed(message=msg, subnet_id=channel_name) for msg in new_messages]
            self.send_webhook_message(embeds)
        else:
            print(f"No new messages from {channel_name}")
    
    def run(self, check_interval: int = 60):
        """Run the crawler with specified interval in seconds"""
        print(f"Starting Discord crawler...")
        for i, channel_id in enumerate(self.channel_list):
            init_messages = self.fetch_messages(api_url=self.api_urls[i])
            self.initial_messages.append(init_messages)

            for message in init_messages:
                message_id = message.get("id")
                if message_id:
                    self.seen_message_ids[i].add(message_id)

        print(f"Initial fetch complete. Found {len(init_messages)} existing messages.")

        # Start monitoring loop
        while True:
            try:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new messages...")
                for i, channel_id in enumerate(self.channel_list):
                    self.process_new_messages(api_url=self.api_urls[i], channel_name=i)
                print(f"Waiting {check_interval} seconds until next check...")
            except KeyboardInterrupt:
                print("\nCrawler stopped by user")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                print("Continuing in 60 seconds...")
            time.sleep(check_interval)


def main():
    # Configuration - Replace these with your actual values
    CHANNEL_LIST = [
        "1161764746819805215",  # channel 0
        "1161764867166961704",  # channel 1
        "1220504695404236800",  # channel 2
        "1222226314824777853",  # channel 3
        "1161765008347254915",  # channel 4
        "1368959417936252998",  # channel 5
        "1209554949449457705",  # channel 6
        "1437494877578330174",  # channel 7
        "1162384774170677318",  # channel 8
        "1162768567821930597",  # channel 9
        "1217952256306057298",  # channel 10
        "1232378968187867147",  # channel 11
        "1201941624243109888",  # channel 12
        "1185617142914236518",  # channel 13
        "1364251338707570698",  # channel 14
        "1366877131132375170",  # channel 15
        "1407020346208682175",  # channel 16
        "1179081290289528864",  # channel 17
        "1335971614516576296",  # channel 18
        "1414687189752746167",  # channel 19
        "1416079117614448841",  # channel 20
        "1240801129177157692",  # channel 21
        "1189589759065067580",  # channel 22
        "1191833510021955695",  # channel 23
        "1214246819886931988",  # channel 24
        "1234881153832321024",  # channel 25
        "1321148494253264998",  # channel 26
        "1174835090539433994",  # channel 27
        "1343950080465698836",  # channel 28
        "1263866060780605501",  # channel 29
        "1255568373056671804",  # channel 30
        "1361421560988041267",  # channel 31
        "1215319932062011464",  # channel 32
        "1233428828479819876",  # channel 33
        "1247680967225905273",  # channel 34
        "1415790978077556906",  # channel 35
        "1339356060787408996",  # channel 36
        "1420486463841374261",  # channel 37
        "1281623984286334987",  # channel 38
        "1387865673690251445",  # channel 39
        "1371491429775446147",  # channel 40
        "1263142301786574889",  # channel 41
        "1275149537547391058",  # channel 42
        "1263507367405031434",  # channel 43
        "1271486854830755981",  # channel 44
        "1267511824601976935",  # channel 45
        "1397618038894759956",  # channel 46
        "1370452296940650656",  # channel 47
        "1407438037956427960",  # channel 48
        "1434923225229295697",  # channel 49
        "1311109830282313781",  # channel 50
        "1291754566957928469",  # channel 51
        "1213131262483628102",  # channel 52
        "1302975822554202142",  # channel 53
        "1351934165964296232",  # channel 54
        "1320766712508977192",  # channel 55
        "1311360495428702240",  # channel 56
        "1310698546852528180",  # channel 57
        "1304499133675081761",  # channel 58
        "1407849009976053832",  # channel 59
        "1300553352274382848",  # channel 60
        "1319313447435108413",  # channel 61
        "1320812830735339580",  # channel 62
        "1387107117697073302",  # channel 63
        "1320739778534047785",  # channel 64
        "1342275465267642408",  # channel 65
        "1392960766990221312",  # channel 66
        "1412074718877581495",  # channel 67
        "1345470582161936405",  # channel 68
        "1349118519198875778",  # channel 69
        "1349119225868058644",  # channel 70
        "1349121405903573114",  # channel 71
        "1349122541754515538",  # channel 72
        "1351969903132938302",  # channel 73
        "1349123574820245534",  # channel 74
        "1349124437752152075",  # channel 75
        "1264939518641963070",  # channel 76
        "1351180132295118848",  # channel 77
        "1351180661918142474",  # channel 78
        "1353733356470276096",  # channel 79
        "1353733529774723073",  # channel 80
        "1354089114189955102",  # channel 81
        "1354838433142542407",  # channel 82
        "1355560253076410428",  # channel 83
        "1408463235082092564",  # channel 84
        "1342559689690583202",  # channel 85
        "1358810927943782673",  # channel 86
        "1347299108238397572",  # channel 87
        "1358854051634221328",  # channel 88
        "1359592408119120033",  # channel 89
        "1361438967198908577",  # channel 90
        "1361439346154016900",  # channel 91
        "1361761424153645217",  # channel 92
        "1362489640841380045",  # channel 93
        "1343988268630409226",  # channel 94
        "1364253568961609859",  # channel 95
        "1364655778149171250",  # channel 96
        "1366426210275692544",  # channel 97
        "1366426973781364816",  # channel 98
        "1366845111945658409",  # channel 99
        "1429935142847381617",  # channel 100
        "1368946065738436749",  # channel 101
        "1375534889486778409",  # channel 102
        "1370083644818849955",  # channel 103
        "1370430761408139404",  # channel 104
        "1437473346026475702",  # channel 105
        "1371902705605546075",  # channel 106
        "1372284562276745338",  # channel 107
        "1374389639225409598",  # channel 108
        "1374389869148770425",  # channel 109
        "1374390003865747546",  # channel 110
        "1375215258678857728",  # channel 111
        "1376603375113863178",  # channel 112
        "1363882173991747584",  # channel 113
        "1418239987291525291",  # channel 114
        "1379143301478744064",  # channel 115
        "1379496997752410172",  # channel 116
        "1380199829669416970",  # channel 117
        "1381659575522033724",  # channel 118
        "1381660350818029578",  # channel 119
        "1381987595881414656",  # channel 120
        "1382818027241738352",  # channel 121
        "1375509743753236722",  # channel 122
        "1384252267770806293",  # channel 123
        "1385341501130801172",  # channel 124
        "1386721054906646549",  # channel 125
        "1386721120652361800",  # channel 126
        "1387151679266230323",  # channel 127
        "1387438124132733110",  # channel 128
        "1341812134807343114",  # Price talk
    ]
    BOT_TOKEN = "MTIwNjY0MzY5NDEyODg1NzEwMw.GkBLIU.9yxK6xuxJbqYOJ7IcBFekUufJqNRCu-YqNE_I8"  # Your bot token
    WEBHOOK_URL = "https://discord.com/api/webhooks/1420813134410682378/KXZ6CZeoPDr-h_balb62sZA_xnVtUsAyaNU1udShLzJfW7chTUwzd83IxfPS_1XaUBS0"  # Replace with your webhook URL
    
    # List of user IDs to monitor (from your output example)
    TARGET_USER_IDS = [
        "1213176263758319698",  # dt
        "595372674121990144",  # adamw
        "1209166548955041835",  # atel
    ]
    
    # Create and run crawler
    crawler = DiscordCrawler(
        channel_list=CHANNEL_LIST,
        bot_token=BOT_TOKEN,
        webhook_url=WEBHOOK_URL
    )
    
    crawler.run(check_interval=10)  # Check every 60 seconds
if __name__ == "__main__":
    main()

