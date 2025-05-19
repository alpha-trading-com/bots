import fastapi
import bittensor as bt
import uvicorn
from typing import Dict


from constants import ROUND_TABLE_HOTKEY


app = fastapi.FastAPI()

wallet_names = ["stake_2", "sangar_ck2", "sec_ck4", "sec_ck12"]
wallets: Dict[str, bt.wallet] = {}


def unlock_wallets():
    for wallet_name in wallet_names:
        wallet = bt.wallet(name=wallet_name)
        wallet.unlock_coldkey()
        wallets[wallet_name] = wallet


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/stake")
def stake(tao_amount: float, netuid: int, wallet_name: str="stake_2", dest_hotkey: str = ROUND_TABLE_HOTKEY):
    retries = 4
    while retries > 0:
        try:
            wallet = wallets[wallet_name]
            subtensor = bt.subtensor('finney')
                
            amount = bt.Balance.from_tao(tao_amount)
            
            stake = subtensor.add_stake(
                netuid=netuid,
                amount=amount,
                wallet=wallet,
                hotkey_ss58=dest_hotkey
            )
            return {"message": f"Staked {amount} TAO from {wallet_name}", "result": stake}
        except Exception as e:
            retries -= 1
            if retries == 0:
                return {"message": f"Error staking {amount} TAO from {wallet_name}: {e}", "result": None}


if __name__ == "__main__":
    unlock_wallets()
    uvicorn.run(app, host="0.0.0.0", port=8000)