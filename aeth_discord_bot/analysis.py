import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bittensor as bt
import requests
import re

from modules.constants import GOOGLE_DOC_ID_BOTS, GOOGLE_DOC_ID_JEETERS

bots = []
jeeters = []
jeeter_address_to_owner = {}
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

def load_jeeters_from_gdoc():
    url = f"https://docs.google.com/document/d/{GOOGLE_DOC_ID_JEETERS}/export?format=txt"
    try:
        global jeeters
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        text = response.text
        # Each pair is like: <wallet_address> <owner_name>
        # build a dict mapping wallet address to owner name
        pattern = r'(5[1-9A-HJ-NP-Za-km-z]{47})\s+([^\s]+)'
        for match in re.findall(pattern, text):
            address, owner = match
            jeeters.append({
                "address": address, 
                "owner": owner,
            })
            jeeter_address_to_owner[address] = owner
    except Exception as e:  
        print(f"Failed to load jeeters from Google Doc: {e}")

load_bots_from_gdoc()
load_jeeters_from_gdoc()

def get_bot_staked_in_subnet(subnet_id: int) -> tuple[float, list[dict]]:
    total_staked_amount = 0.0
    subnet = subtensor.subnet(netuid=subnet_id)
    batch_size = 60
    bot_staked_infos = []
    for i in range(0, len(bots), batch_size):
        batch = bots[i:i+batch_size]
        stake_infos = subtensor.get_stake_info_for_coldkeys(coldkey_ss58s=batch)
        for bot, stake_info in stake_infos.items():
            bot_staked_amount = 0.0
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


def get_jeeter_staked_in_subnet(subnet_id: int) -> tuple[float, list[dict]]:
    total_staked_amount = 0.0
    subnet = subtensor.subnet(netuid=subnet_id)
    batch_size = 60
    jeeter_staked_infos = []
    for i in range(0, len(jeeters), batch_size):
        batch = [jeeter["address"] for jeeter in jeeters[i:i+batch_size]]
        stake_infos = subtensor.get_stake_info_for_coldkeys(coldkey_ss58s=batch)
        for jeeter, stake_info in stake_infos.items():
            jeeter_staked_amount = 0.0
            for stake in stake_info:
                if stake.netuid != subnet_id:
                    continue
                jeeter_staked_amount += stake.stake.tao * subnet.price.tao
            total_staked_amount += jeeter_staked_amount
            if jeeter_staked_amount < 0.5:
                continue
            jeeter_staked_infos.append({
                "address": jeeter,
                "owner": jeeter_address_to_owner[jeeter],
                "staked_amount": jeeter_staked_amount,
            })
    return total_staked_amount, jeeter_staked_infos

def get_subnet_info(subnet_id: int) -> dict:
    subnet: bt.DynamicInfo = subtensor.subnet(netuid=subnet_id)
    return {
        "name": subnet.subnet_name,
        "price": subnet.price.tao,
        "owner": subnet.owner_coldkey,
        "tao_in": subnet.tao_in.tao,
        "alpha_in": subnet.alpha_in.tao,
        "emission": subnet.emission.tao,
    }

def get_reg_price() -> float:
    query = subtensor.substrate.runtime_call(
        api="SubnetRegistrationRuntimeApi",
        method="get_network_registration_cost",
    )
    decoded = query.decode() / 1e9  # convert to TAO
    return decoded

if __name__ == "__main__":
    print(get_jeeter_staked_in_subnet(2))