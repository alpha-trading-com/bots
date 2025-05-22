import fastapi
import bittensor as bt
import uvicorn
import subprocess
from typing import Dict
from fastapi import Depends
from fastapi.responses import HTMLResponse

from auth import get_current_username
from constants import ROUND_TABLE_HOTKEY

app = fastapi.FastAPI()

wallet_names = ["stake_2",]
wallets: Dict[str, bt.wallet] = {}

def unlock_wallets():
    for wallet_name in wallet_names:
        wallet = bt.wallet(name=wallet_name)
        print(f"Unlocking wallet {wallet_name}")
        wallet.unlock_coldkey()
        wallets[wallet_name] = wallet

@app.get("/")
def read_root(username: str = Depends(get_current_username)):
    from index import INDEX_HTML
    subtensor = bt.subtensor('finney')
    def get_balance_html():
        balance_html = ""
        for wallet_name in wallet_names:
            wallet = wallets[wallet_name]
            balance = subtensor.get_balance(wallet.coldkey.ss58_address)
            balance_html += f"""
                <div class="balance-container">
                    <div class="balance-title"><a target="_blank" href="/stake_list?wallet={wallet_name}" style="text-decoration: none; color: inherit; cursor: pointer; text-decoration: underline;">{wallet_name}</a></div>
                    <div class="balance-amount">{balance} TAO</div>
                </div>
            """
        return balance_html

    return fastapi.responses.HTMLResponse(
        content=INDEX_HTML.format(balance_html=get_balance_html())
    )

@app.get("/stake")
def stake(
    tao_amount: float, 
    netuid: int, 
    wallet_name: str="stake_2", 
    dest_hotkey: str = ROUND_TABLE_HOTKEY, 
    rate_tolerance: float = 0.005,
    username: str = Depends(get_current_username)
):
    retries = 4
    while retries > 0:
        try:
            wallet = wallets[wallet_name]
            subtensor = bt.subtensor('finney')
            subnet = subtensor.subnet(netuid=netuid)
            min_tolerance = tao_amount / subnet.tao_in.tao  
            if rate_tolerance < min_tolerance:
                rate_tolerance = min_tolerance

            result = subtensor.add_stake(
                netuid=netuid,
                amount= bt.Balance.from_tao(tao_amount),
                wallet=wallet,
                hotkey_ss58=dest_hotkey,
                safe_staking=True,
                rate_tolerance=rate_tolerance
            )
            if not result:
                raise Exception("Stake failed")
            return {"message": f"Staked {tao_amount} TAO from {wallet_name}, min_tolerance: {min_tolerance}", "result": result}
        except Exception as e:
            retries -= 1
            if retries == 0:
                return {
                    "message": f"Error staking {tao_amount} TAO from {wallet_name}: {e}, min_tolerance: {min_tolerance}", "result": None,
                }


@app.get("/unstake")
def unstake(
    netuid: int,
    wallet_name: str="stake_2",
    dest_hotkey: str = ROUND_TABLE_HOTKEY,
    username: str = Depends(get_current_username)
):
    retries = 4
    while retries > 0:
        try:
            wallet = wallets[wallet_name]
            subtensor = bt.subtensor('finney')
            result = subtensor.unstake(netuid=netuid, wallet=wallet, hotkey_ss58=dest_hotkey)
            if not result:
                raise Exception("Unstake failed")
            
            return {"message": f"Unstaked from {netuid} network", "result": result}
        except Exception as e:
            retries -= 1
            if retries == 0:
                return {"message": f"Error unstaking from {netuid} network: {e}", "result": False}

@app.get("/stake_list")
def stake_list(wallet_name: str = "stake_2"):
    result = subprocess.run(["btcli", "stake", "list", "--name", wallet_name, "--no-prompt"], capture_output=True, text=True)
    return HTMLResponse(content=f"<pre>{result.stdout}</pre>")


if __name__ == "__main__":
    unlock_wallets()
    uvicorn.run(app, host="0.0.0.0", port=8000)