import time
import argparse
import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

import bittensor as bt
from bittensor_wallet import Wallet
from constants import NETWORK


class TempWeighter:
    def __init__(self):
        pass
        

    def get_config(self):
        # Set up the configuration parser.
        parser = argparse.ArgumentParser(
            description="Temp Weighter",
            usage="python3 set_weighter.py <command> [options]",
            add_help=True,
        )
        command_parser = parser.add_subparsers(dest="command")
        run_command_parser = command_parser.add_parser(
            "run", help="""Run the weighter"""
        )

        # Adds subtensor specific arguments.
        bt.async_subtensor.add_args(run_command_parser)
        # Adds wallet specific arguments.
        Wallet.add_args(run_command_parser)

        # Parse the config.
        try:
            config = bt.config(parser)
        except ValueError as e:
            print(f"Error parsing config: {e}")
            exit(1)

        return config

    async def set_weights(self, netuid, burn_uid):
        uids = [burn_uid]
        weights = [1.0]

        # Set weights.
        success, message = await self.async_subtensor.set_weights(
            self.wallet,
            netuid,
            uids,
            weights,
            wait_for_inclusion=True,
            wait_for_finalization=True,
        )    

        if not success:
            print(f"Error setting weights: {message}")
            return netuid, burn_uid, success, message

        print("Weights set.")
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"weight_set_all_new.txt"
            
            with open(filename, "a") as f:
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Burn UID: {burn_uid}\n")
                f.write(f"Success: {success}\n")
                f.write(f"Message: {message}\n")
                f.write(f"Name: {self.wallet.hotkey.ss58_address}\n")
            print(f"Saved weight set information to {filename}")
        except Exception as e:
            print(f"Error saving weight set information: {e}")

        return netuid, burn_uid, success, message
    

    async def run_async(self, netuid, burn_uid):
        print("Running weighter...")

        while True:
            print("Running weighter loop...")
            # Create tasks for all pairs
            
            netuid, burn_uid, success, message = await self.set_weights(netuid, burn_uid)
            if not success:
                print(f"Error setting weights for netuid {netuid}: {message}")
                await asyncio.sleep(1)
            else:
                print(f"Successfully set weights for netuid {netuid} and burn_uid {burn_uid}")
                await asyncio.sleep(10)


    async def run(self):
        self.config = self.get_config()

        self.wallet = Wallet(config=self.config)
        self.async_subtensor = bt.async_subtensor(network=NETWORK)
        await self.async_subtensor.initialize()

        self.netuid_burn_pairs = [
            (69, 100),
            (40, 67),
            (63, 149),
            (82, 51),
            (15, 25),
            (47, 97),
            (28, 234),
            (104, 52),
            (108, 12),
            (98, 222),
            (114, 29),
        ]
        # Create tasks for each pair
        tasks = []
        for netuid, burn_uid in self.netuid_burn_pairs:
            task = asyncio.create_task(self.run_async(netuid, burn_uid))
            tasks.append(task)
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)


async def main():
    weighter = TempWeighter()
    await weighter.run()

if __name__ == "__main__":
    asyncio.run(main())


if __name__ == "__main__":
    weighter = TempWeighter()
    weighter.run()