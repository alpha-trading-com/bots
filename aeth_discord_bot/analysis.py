import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bittensor as bt
import requests
import re

from modules.constants import GOOGLE_DOC_ID_BOTS

bots = []
subtensor = bt.Subtensor("finney")


def load_bots_from_gdoc():
    url = f"https://docs.google.com/document/d/{GOOGLE_DOC_ID_BOTS}/export?format=txt"
    try:
        global bots
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        text = response.text
        bots = re.findall(r'5[1-9A-HJ-NP-Za-km-z]{47}', text)
    except Exception as e:
        print(f"Failed to load bots from Google Doc: {e}")

load_bots_from_gdoc()

def get_bot_staked_in_subnet(subnet_id: int) -> tuple[float, list[dict]]:
    total_staked_amount = 0.0
    subnet = subtensor.subnet(netuid=subnet_id)
    stake_infos = subtensor.get_stake_info_for_coldkeys(coldkey_ss58s=bots)
    bot_staked_infos = []
    for bot, stake_info in stake_infos.items():
        bot_staked_amount = 0.0
        print(stake_info)
        for stake in stake_info:
            if stake.netuid != subnet_id:
                continue
            bot_staked_amount += stake.stake.tao * subnet.price.tao
        total_staked_amount += bot_staked_amount
        if bot_staked_amount < 0.5:
            continue
        bot_staked_infos.append({
            "bot": bot,
            "staked_amount": bot_staked_amount,
        })
    
    return total_staked_amount, bot_staked_infos


if __name__ == "__main__":
    print(get_bot_staked_in_subnet(2))