import os
import fastapi
import bittensor as bt
import uvicorn
import subprocess
from typing import Dict
from fastapi import Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dotenv import load_dotenv

from auth import get_current_username
from constants import ROUND_TABLE_HOTKEY, NETWORK

app = fastapi.FastAPI()

# Set up templates
templates = Jinja2Templates(directory="templates")

load_dotenv()
wallet_names = os.getenv('WALLET_NAMES', '').split(',')
wallets: Dict[str, bt.wallet] = {}

def unlock_wallets():
    for wallet_name in wallet_names:
        wallet = bt.wallet(name=wallet_name)
        print(f"Unlocking wallet {wallet_name}")
        retries = 3
        for _ in range(retries):
            try:
                wallet.unlock_coldkey()
                break
            except Exception as e:
                print(f"Error unlocking wallet {wallet_name}: {e}")
                continue
        wallets[wallet_name] = wallet

@app.get("/")
def read_root(request: fastapi.Request, username: str = Depends(get_current_username)):
    subtensor = bt.subtensor(network=NETWORK)
    def get_balance_html():
        balance_html = ""
        for wallet_name in wallet_names:
            wallet = wallets[wallet_name]
            balance = subtensor.get_balance(wallet.coldkey.ss58_address)
            balance_html += f"""
                <div class="balance-container">
                    <div class="balance-title"><a target="_blank" href="/stake_list?wallet_name={wallet_name}" style="text-decoration: none; color: inherit; cursor: pointer; text-decoration: underline;">{wallet_name}</a></div>
                    <div class="balance-amount">{balance} TAO</div>
                </div>
            """
        return balance_html

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "balance_html": get_balance_html(), "wallet_names": wallet_names}
    )


@app.get("/min_tolerance")
def min_tolerance(
    tao_amount: float, 
    netuid: int, 
):
    subtensor = bt.subtensor(network=NETWORK)
    subnet = subtensor.subnet(netuid=netuid)
    min_tolerance = tao_amount / subnet.tao_in.tao  
    return {"min_tolerance": min_tolerance}


@app.get("/stake")
def stake(
    tao_amount: float, 
    netuid: int, 
    wallet_name: str, 
    dest_hotkey: str = ROUND_TABLE_HOTKEY, 
    rate_tolerance: float = 0.005,
    min_tolerance_staking: bool = True,
    retries: int = 1,
    username: str = Depends(get_current_username)
):
    if retries < 1:
        retries = 1
    result = None
    min_tolerance = None
    wallet = wallets[wallet_name]
    subtensor = bt.subtensor(network=NETWORK)
    subnet = subtensor.subnet(netuid=netuid)
    min_tolerance = tao_amount / subnet.tao_in.tao  
    if min_tolerance_staking:
        rate_tolerance = min_tolerance + 0.001

    while retries > 0:
        try:

            result = subtensor.add_stake(
                netuid=netuid,
                amount= bt.Balance.from_tao(tao_amount, netuid),
                wallet=wallet,
                hotkey_ss58=dest_hotkey,
                safe_staking=True,
                rate_tolerance=rate_tolerance
            )
            if not result:
                raise Exception("Stake failed")
            
            return {
                "success": True,
                "result": result,
                "min_tolerance": min_tolerance,
            }
        except Exception as e:
            retries -= 1
            if retries == 0:
                return {
                    "success": False,
                    "result": result,
                    "min_tolerance": min_tolerance,
                }


@app.get("/unstake")
def unstake(
    netuid: int,
    wallet_name: str,
    amount: float = None,
    dest_hotkey: str = ROUND_TABLE_HOTKEY,
    rate_tolerance: float = 0.005,
    min_tolerance_unstaking: bool = True,
    retries: int = 1,
    username: str = Depends(get_current_username)
):
    if retries < 1:
        retries = 1
    result = None
    wallet = wallets[wallet_name]
    subtensor = bt.subtensor(network=NETWORK)
    subnet = subtensor.subnet(netuid=netuid)

    if amount is None:
        amount = subtensor.get_stake(
            coldkey_ss58=wallet.coldkeypub.ss58_address,
            hotkey_ss58=dest_hotkey,
            netuid=netuid
        )
    else:
        amount = bt.Balance.from_tao(amount / subnet.price.tao, netuid)
                    
    min_tolerance = amount.tao / (amount.tao + subnet.alpha_in.tao)

    if min_tolerance_unstaking:
        rate_tolerance = min_tolerance + 0.001

    while retries > 0:
        try:
            result = subtensor.unstake(
                netuid=netuid, 
                wallet=wallet, 
                amount=amount,
                hotkey_ss58=dest_hotkey,
                safe_staking=True,
                rate_tolerance=rate_tolerance,
            )
            if not result:
                raise Exception("Unstake failed")
            
            return {
                "success": True,
                "result": result,
                "min_tolerance": min_tolerance,
            }
        
        except Exception as e:
            retries -= 1
            if retries == 0:
                return {
                    "success": False,
                    "result": result,
                    "min_tolerance": min_tolerance,
                }


@app.get("/stake_list")
def stake_list(wallet_name: str):
    result = subprocess.run(["btcli", "stake", "list", "--name", wallet_name, "--no-prompt"], capture_output=True, text=True)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{wallet_name} | Stake List</title>
    </head>
    <body>
        <pre>{result.stdout}</pre>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    unlock_wallets()
    if not wallet_names:
        print("No wallet names found in .env file")
        exit(1)
    uvicorn.run(app, host="0.0.0.0", port=9000)