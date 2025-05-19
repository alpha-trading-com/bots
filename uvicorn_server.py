import fastapi
import bittensor as bt
import uvicorn
from typing import Dict


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
def read_root():
    from index import INDEX_HTML
    subtensor = bt.subtensor('finney')
    def get_balance_html():
        balance_html = ""
        for wallet_name in wallet_names:
            wallet = wallets[wallet_name]
            balance = subtensor.get_balance(wallet.coldkey.ss58_address)
            balance_html += f"""
                <div class="balance-container">
                    <div class="balance-title">{wallet_name}</div>
                    <div class="balance-amount">{balance} TAO</div>
                </div>
            """
        return balance_html

    return fastapi.responses.HTMLResponse(
        content=INDEX_HTML.format(balance_html=get_balance_html())
    )


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