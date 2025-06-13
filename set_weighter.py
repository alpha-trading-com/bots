import time
import argparse
import datetime

import bittensor as bt
from bittensor_wallet import Wallet
from constants import NETWORK


MAINNET_NETUID = 5
BLOCK_TIME = 12


class TempWeighter:
    def __init__(self):
        self.config = self.get_config()

        # Initialize wallet.
        self.wallet = Wallet(config=self.config)
        print(f"Wallet: {self.wallet}")

        # Initialize subtensor.
        self.subtensor = bt.subtensor(network=NETWORK)
        print(f"Subtensor: {self.subtensor}")

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

        # Adds override arguments for network and netuid.
        run_command_parser.add_argument(
            "--netuid", type=int, default=MAINNET_NETUID, help="The chain subnet uid." # TODO: change to 40
        )

        run_command_parser.add_argument(
            "--set_weights_interval",
            type=int,
            default= 2,  # 2 epochs
            help="The interval to set weights in blocks.",
        )

        # Adds subtensor specific arguments.
        bt.subtensor.add_args(run_command_parser)
        # Adds wallet specific arguments.
        Wallet.add_args(run_command_parser)

        # Parse the config.
        try:
            config = bt.config(parser)
        except ValueError as e:
            print(f"Error parsing config: {e}")
            exit(1)

        return config

    def run(self):
        print("Running weighter...")

        while True:
            print("Running weighter loop...")
            # Get the burn UID.
            burn_uid = 13

            # Set weights to burn UID.
            uids = [burn_uid]
            weights = [1.0]

            # Set weights.
            success, message = self.subtensor.set_weights(
                self.wallet,
                self.config.netuid,
                uids,
                weights,
                wait_for_inclusion=True,
                wait_for_finalization=True,
            )
            if not success:
                print(f"Error setting weights: {message}")
                time.sleep(1)
                continue

            print("Weights set.")
            # Save the current state to a file
            try:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"weight_set.txt"
                
                with open(filename, "a") as f:
                    f.write(f"Timestamp: {timestamp}\n")
                    f.write(f"Burn UID: {burn_uid}\n")
                    f.write(f"Success: {success}\n")
                    f.write(f"Message: {message}\n")
                    f.write(f"Name: {self.wallet.name}\n")
                print(f"Saved weight set information to {filename}")
            except Exception as e:
                print(f"Error saving weight set information: {e}")

            # Wait for next time to set weights.
            print(
                f"Waiting {self.config.set_weights_interval} blocks before next weight set..."
            )
            time.sleep(10)


if __name__ == "__main__":
    weighter = TempWeighter()
    weighter.run()