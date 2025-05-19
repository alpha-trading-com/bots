import fastapi
import bittensor as bt
import uvicorn
from typing import Dict


from constants import ROUND_TABLE_HOTKEY


app = fastapi.FastAPI()

wallet_names = ["stake_2", "sangar_ck2",]
wallets: Dict[str, bt.wallet] = {}


def unlock_wallets():
    for wallet_name in wallet_names:
        wallet = bt.wallet(name=wallet_name)
        print(f"Unlocking wallet {wallet_name}")
        wallet.unlock_coldkey()
        wallets[wallet_name] = wallet


@app.get("/")
def read_root():
    return {"message": "Hello, World wallet server"}


@app.get("/stake")
def stake(tao_amount: float, netuid: int, wallet_name: str="stake_2", dest_hotkey: str = ROUND_TABLE_HOTKEY):
    retries = 4
    while retries > 0:
        try:
            wallet = wallets[wallet_name]
            subtensor = bt.subtensor('finney')
            
            stake = subtensor.add_stake(
                netuid=netuid,
                amount=tao_amount,
                wallet=wallet,
                hotkey_ss58=dest_hotkey
            )
            return {"message": f"Staked {tao_amount} TAO from {wallet_name}", "result": stake}
        except Exception as e:
            retries -= 1
            if retries == 0:
                return {"message": f"Error staking {tao_amount} TAO from {wallet_name}: {e}", "result": None}


if __name__ == "__main__":
    unlock_wallets()
    uvicorn.run(app, host="0.0.0.0", port=8000)